import { useCallback, useEffect, useRef, useState } from 'react';
import { controlSimulator, createSimulator, snapshot, stepSimulator } from '../lib/simulator';

const BASE_URL = (import.meta.env.VITE_API_BASE_URL || '').trim().replace(/\/+$/, '');
const BACKEND = Boolean(BASE_URL);

async function api(path, options) {
  const response = await fetch(BASE_URL + path, options);
  if (!response.ok) {
    let detail = `HTTP ${response.status}`;
    try { const json = await response.json(); detail = json.detail || detail; } catch { /* invalid JSON */ }
    throw Error(typeof detail === 'string' ? detail : JSON.stringify(detail));
  }
  return response.json();
}

export function useCampusSimulation() {
  const simRef = useRef(null);
  const [overview, setOverview] = useState(null);
  const [connected, setConnected] = useState(false);
  const [error, setError] = useState('');
  const [historyVersion, setHistoryVersion] = useState(0);
  const backendMode = BACKEND;

  useEffect(() => {
    if (!BACKEND) {
      const sim = createSimulator();
      simRef.current = sim;
      setOverview(snapshot(sim));
      setConnected(true);
      const timer = window.setInterval(() => {
        if (simRef.current?.running) {
          for (let i = 0; i < simRef.current.speed; i++) stepSimulator(simRef.current);
          setOverview(snapshot(simRef.current));
          setHistoryVersion(v => v + 1);
        }
      }, 1000);
      return () => window.clearInterval(timer);
    }
    let stream;
    let cancelled = false;
    api('/api/live/overview').then(value => {
      if (!cancelled) { setOverview(value); setConnected(true); }
    }).catch(e => { if (!cancelled) { setError(`Backend unavailable: ${e.message}`); setConnected(false); }});
    stream = new EventSource(BASE_URL + '/api/live/events');
    stream.addEventListener('overview', event => {
      try {
        const data = JSON.parse(event.data);
        setOverview(data);
        setHistoryVersion(v => v + 1);
        setConnected(true);
        setError('');
      } catch (e) { setError(`Malformed backend stream: ${e.message}`); }
    });
    stream.onerror = () => { setConnected(false); setError('Live backend disconnected; attempting to reconnect.'); };
    return () => { cancelled = true; stream?.close(); };
  }, []);

  const control = useCallback(async (action, opts = {}) => {
    try {
      setError('');
      if (!BACKEND) {
        simRef.current = controlSimulator(simRef.current, action, opts);
        setOverview(snapshot(simRef.current));
        setHistoryVersion(v => v + 1);
        return true;
      }
      const data = await api('/api/live/control', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action, ...opts }),
      });
      setOverview(data);
      return true;
    } catch (e) { setError(e.message); return false; }
  }, []);

  const getHistory = useCallback(async assetId => {
    if (!assetId) return [];
    if (!BACKEND) return simRef.current?.assets[assetId]?.history.slice(-100) || [];
    const result = await api('/api/live/assets/' + encodeURIComponent(assetId) + '/history?limit=100');
    return result.readings;
  }, []);

  return { overview, connected, error, setError, control, getHistory, historyVersion, backendMode };
}
