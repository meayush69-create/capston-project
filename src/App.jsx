import { useEffect, useMemo, useRef, useState } from 'react';
import SensorChart from './components/SensorChart';
import { METRICS, SCENARIOS } from './lib/simulator';
import { useCampusSimulation } from './hooks/useCampusSimulation';

const formatName = (id = '') => id.replaceAll('_', ' ');
const iconFor = type => type === 'HVAC' ? '❄' : type === 'Pump' ? '◉' : '↟';
const safeClock = value => value ? new Date(value).toLocaleTimeString() : '—';

function Sidebar({ connected, backendMode }) {
  return <aside className="sidebar">
    <div className="logo"><div className="logo-mark">◈</div><div><strong>campus<span>pulse</span></strong><small>INTELLIGENT OPERATIONS</small></div></div>
    <div className="nav-heading">OPERATIONS</div>
    <a href="#overview" className="nav active">▦ <span>Command center</span></a>
    <a href="#assets" className="nav">▤ <span>Asset intelligence</span></a>
    <a href="#telemetry" className="nav">〽 <span>Sensor telemetry</span></a>
    <a href="#simulation" className="nav">◉ <span>Simulation lab</span></a>
    <div className="sidebar-foot"><div className="system-tile"><span className="dot" /> {connected ? 'Live simulator connected' : 'Connecting to stream…'}</div><small>{backendMode ? 'Python model backend connected when available' : 'Self-contained browser simulation'}<br />Academic research demonstration</small></div>
  </aside>;
}

function Hero() {
  return <section className="hero"><div className="hero-content">
    <div className="eyebrow">NEXT GENERATION CAMPUS MONITORING <span className="sparkle">✧</span></div>
    <h2>Know what&apos;s next.<br /><em>Before it happens.</em></h2>
    <p>Watch predictive digital twins evolve as virtual sensors stream live. Explore anomalies, investigate asset health, and test maintenance scenarios in real time.</p>
    <div className="hero-chips"><span>◈ &nbsp; 4 infrastructure assets</span><span>◷ &nbsp; Continuous synthetic feed</span></div>
  </div><div className="hero-graphic"><div className="orbit orbit-outer" /><div className="orbit orbit-inner" /><div className="hero-core">◈</div><span className="node node-one">HVAC</span><span className="node node-two">PUMP</span><span className="node node-three">LIFT</span><span className="node node-four">AI</span></div></section>;
}

function MetricCard({ label, value, note, icon, type = '' }) {
  return <div className="metric"><div className="metric-caption">{label}<span className={`metric-icon ${type}`}>{icon}</span></div><div className="metric-value">{value}</div><div className="metric-note">{note}</div></div>;
}

function AssetCard({ state, selected, onSelect }) {
  return <button type="button" className={`asset-card ${selected ? 'selected' : ''}`} onClick={onSelect} aria-label={`Inspect ${formatName(state.asset_id)}`} aria-pressed={selected}>
    <div className="asset-top"><span className="asset-icon">{iconFor(state.asset_type)}</span><span className={`status ${state.status}`}>{state.status}</span></div>
    <h4>{formatName(state.asset_id)}</h4><div className="asset-kind">{state.asset_type} · {state.scenario === 'normal' ? 'Nominal' : (SCENARIOS[state.scenario] || state.scenario)}</div>
    <div className="bar"><div className={state.status} style={{ width: `${Math.max(0, Math.min(100, state.health_score))}%` }} /></div>
    <div className="asset-footer"><span>Current health</span><b>{state.health_score}%</b></div>
  </button>;
}

export default function App() {
  const { overview, connected, error, setError, control, getHistory, historyVersion, backendMode } = useCampusSimulation();
  const [selected, setSelected] = useState('HVAC_Chiller_01');
  const [metric, setMetric] = useState('internal_temp_c');
  const [readings, setReadings] = useState([]);
  const [faultAsset, setFaultAsset] = useState('HVAC_Chiller_01');
  const [faultType, setFaultType] = useState('bearing_wear');
  const [speed, setSpeed] = useState(1);
  const [activity, setActivity] = useState([{ id: 1, time: Date.now(), text: 'Synthetic digital twin simulator initialized' }]);
  const [clock, setClock] = useState(new Date());
  const lastStatuses = useRef({});
  const lastSequence = useRef(null);
  const lastHistoryRequest = useRef(0);
  const states = overview?.assets || [];
  const selectedState = useMemo(() => states.find(s => s.asset_id === selected) || states[0], [states, selected]);
  const pushActivity = text => setActivity(list => [{ id: Date.now() + Math.random(), time: Date.now(), text }, ...list].slice(0, 8));

  useEffect(() => {
    const timer = window.setInterval(() => setClock(new Date()), 1000);
    return () => window.clearInterval(timer);
  }, []);
  useEffect(() => {
    if (!overview) return;
    setSpeed(overview.speed);
    if (!overview.assets.some(a => a.asset_id === selected)) setSelected(overview.assets[0].asset_id);
    if (lastSequence.current !== null && overview.sequence < lastSequence.current) {
      lastStatuses.current = {};
    }
    lastSequence.current = overview.sequence;
    for (const state of overview.assets) {
      const old = lastStatuses.current[state.asset_id];
      if (old && old !== state.status) pushActivity(`${formatName(state.asset_id)} changed from ${old} to ${state.status}`);
      lastStatuses.current[state.asset_id] = state.status;
    }
  }, [overview]);
  useEffect(() => {
    if (!selectedState) return;
    const current = ++lastHistoryRequest.current;
    getHistory(selectedState.asset_id).then(items => {
      if (current === lastHistoryRequest.current) setReadings(items);
    }).catch(e => setError(`Could not load sensor history: ${e.message}`));
  }, [selectedState?.asset_id, historyVersion, getHistory]);

  const act = async (action, extra = {}, message = '') => {
    const ok = await control(action, extra);
    if (ok && message) pushActivity(message);
    return ok;
  };
  const inject = async () => {
    if (await act('inject', { asset_id: faultAsset, scenario: faultType }, `Injected ${SCENARIOS[faultType]} into ${formatName(faultAsset)}`)) setSelected(faultAsset);
  };
  return <div className="app"><Sidebar connected={connected} backendMode={backendMode} /><main>
    <header><div><div className="breadcrumb">SMART CAMPUS <span>/</span> MONITORING CONSOLE</div><h1>Digital twin command center <span className="title-spark">✦</span></h1><p>Predictive maintenance insights for connected campus infrastructure.</p></div><div className="header-actions"><span className={`mode-pill ${connected ? '' : 'offline'}`}><span className="dot" /> {backendMode ? 'LIVE · ML BACKEND' : 'LIVE · BROWSER DEMO'}</span><span className="clock">{clock.toLocaleTimeString()}</span></div></header>
    <Hero />
    <section className="metrics" id="overview">
      <MetricCard label="ACTIVE DIGITAL TWINS" value={states.length || '—'} note="Across campus operations" icon="▤" />
      <MetricCard label="AVERAGE HEALTH" value={overview ? `${overview.average_health}%` : '—'} note="Simulated health index" icon="♡" type="green" />
      <MetricCard label="NEED ATTENTION" value={overview ? overview.counts.WARNING + overview.counts.CRITICAL : '—'} note="Warning or critical alerts" icon="⚠" type="amber" />
      <MetricCard label="SIMULATED READINGS" value={overview ? overview.sequence.toLocaleString() : '—'} note={`At simulation speed ${overview?.speed || 1}×`} icon="◷" type="blue" />
    </section>
    <section id="assets"><div className="section-title"><div><h3>Infrastructure intelligence</h3><p>Live-updated asset states · choose a unit for deeper analytics</p></div><div className="stream-indicator"><span className="pulse" />{overview ? `Updated ${safeClock(overview.updated_at)}` : 'Awaiting readings'}</div></div><div className="asset-grid">{states.length ? states.map(s => <AssetCard key={s.asset_id} state={s} selected={s.asset_id === selectedState?.asset_id} onSelect={() => setSelected(s.asset_id)} />) : <p className="empty">Connecting to simulator…</p>}</div></section>
    <section className="insights" id="telemetry"><div className="chart-panel"><div className="section-title compact"><div><h3>Sensor analytics <span className="mini-tag">LIVE CHART</span></h3><p>{formatName(selectedState?.asset_id)} · {METRICS[metric]}</p></div><div className="chart-tabs">{[['internal_temp_c', 'Temperature'], ['vibration_rms_mms', 'Vibration'], ['power_kw', 'Power']].map(([key, label]) => <button type="button" className={`tab ${metric === key ? 'selected' : ''}`} key={key} onClick={() => setMetric(key)}>{label}</button>)}</div></div>
      <SensorChart readings={readings} metric={metric} /><div className="chart-footer"><span className="legend-dot" />{METRICS[metric]}<span className="chart-footer-right">Latest 100 samples · auto-refresh</span></div></div>
      <div className="advisor"><div className="advisor-eyebrow">✦ MAINTENANCE ADVISOR</div><div className="advisor-title">{formatName(selectedState?.asset_id) || 'Choose an asset'}</div><div className="health-number" style={{ color: selectedState?.status === 'CRITICAL' ? '#ff889b' : selectedState?.status === 'WARNING' ? '#ffc477' : '#65e5bf' }}>{selectedState ? `${selectedState.health_score}%` : '—'}</div><div className="health-label">HEALTH INDEX</div><div className="info-line"><span>Risk estimate</span><b>{selectedState ? `${(100 * selectedState.failure_probability).toFixed(1)}%` : '—'}</b></div><div className="info-line"><span>Estimated useful life*</span><b>{selectedState ? `${selectedState.estimated_rul_hours.toFixed(1)} h` : '—'}</b></div><div className="info-line"><span>Simulation scenario</span><b>{SCENARIOS[selectedState?.scenario] || '—'}</b></div><div className="recommendation"><div>RECOMMENDED ACTION</div><p>{selectedState?.action || 'Awaiting simulator data…'}</p></div><small className="caution">*{backendMode ? 'Risk/RUL comes from the original Python ML models; predictions have not been field-validated.' : 'Estimates are generated by browser-based heuristics, NOT by trained ML models.'}</small></div></section>
    <section id="simulation" className="sim-panel"><div className="section-title compact"><div><h3>Simulation laboratory <span className="mini-tag">INTERACTIVE</span></h3><p>Inject a controlled virtual fault and watch the simulated asset status evolve.</p></div><div className={`run-label ${overview?.running ? '' : 'paused'}`}>{overview?.running ? '● RUNNING' : 'Ⅱ PAUSED'}</div></div><div className="sim-controls">
      <div className="control-group"><label htmlFor="faultAsset">TARGET ASSET</label><select id="faultAsset" value={faultAsset} onChange={e => setFaultAsset(e.target.value)}>{states.map(s => <option key={s.asset_id} value={s.asset_id}>{formatName(s.asset_id)}</option>)}</select></div>
      <div className="control-group"><label htmlFor="faultType">FAULT SCENARIO</label><select id="faultType" value={faultType} onChange={e => setFaultType(e.target.value)}><option value="bearing_wear">Bearing wear / abnormal vibration</option><option value="overheating">Thermal overload</option><option value="power_surge">Power surge</option></select></div>
      <div className="control-group"><label htmlFor="simSpeed">SIMULATION SPEED</label><select id="simSpeed" value={speed} onChange={async e => { const value = Number(e.target.value); setSpeed(value); await act('speed', { speed: value }, `Simulation speed set to ${value}×`); }}><option value={1}>1× · One sample per second</option><option value={2}>2× · Two samples per second</option><option value={5}>5× · Five samples per second</option></select></div>
      <button type="button" className="primary-btn" onClick={inject}>⚡ Inject fault</button><button type="button" className="secondary-btn" onClick={() => act('clear', { asset_id: faultAsset }, `Cleared injected fault for ${formatName(faultAsset)}`)}>Clear fault</button>
    </div><div className="sim-actions"><button className="small-btn" type="button" onClick={() => act(overview?.running ? 'pause' : 'resume', {}, overview?.running ? 'Simulation paused' : 'Simulation resumed')}>{overview?.running ? 'Ⅱ Pause stream' : '▶ Resume stream'}</button><button className="small-btn" type="button" onClick={() => { if (window.confirm('Reset all virtual sensor histories and fault scenarios?')) act('reset', {}, 'Simulation reset'); }}>↺ Reset simulation</button><span className="sim-explain">Faults are synthetic. No physical equipment is contacted or controlled.</span></div>
      <div className="timeline"><b>SIMULATOR ACTIVITY</b><div className="event-log" aria-live="polite">{activity.map(item => <div key={item.id}>{new Date(item.time).toLocaleTimeString()} · {item.text}</div>)}</div></div></section>
    <div className="footnote">CampusPulse © Academic demonstration · {backendMode ? 'Trained-model inference through separately deployed FastAPI' : 'Standalone browser simulation with heuristic estimates'} · Not for critical infrastructure decisions</div>
    {error && <div className="error" role="alert">{error} <button type="button" onClick={() => setError('')} aria-label="Dismiss alert">✕</button></div>}
  </main></div>;
}
