import { useEffect, useRef } from 'react';
import { METRICS } from '../lib/simulator';

export default function SensorChart({ readings, metric }) {
  const ref = useRef(null);
  useEffect(() => {
    const canvas = ref.current;
    if (!canvas) return;
    const render = () => {
      const rect = canvas.getBoundingClientRect();
      if (rect.width < 40 || rect.height < 40) return;
      const ratio = window.devicePixelRatio || 1;
      canvas.width = Math.round(rect.width * ratio);
      canvas.height = Math.round(rect.height * ratio);
      const context = canvas.getContext('2d');
      const w = rect.width, h = rect.height;
      context.scale(ratio, ratio);
      context.clearRect(0, 0, w, h);
      const vals = readings.map(r => Number(r[metric])).filter(Number.isFinite);
      if (!vals.length) return;
      const pad = { left: 48, right: 15, top: 16, bottom: 32 };
      const dw = w - pad.left - pad.right, dh = h - pad.top - pad.bottom;
      let min = Math.min(...vals), max = Math.max(...vals);
      const spread = max - min || Math.max(1, max * .08);
      min -= spread * .2; max += spread * .2;
      const x = i => pad.left + (vals.length === 1 ? .5 : i / (vals.length - 1)) * dw;
      const y = v => pad.top + (max - v) / (max - min) * dh;
      context.font = '11px Arial'; context.textBaseline = 'middle'; context.textAlign = 'right';
      for (let i = 0; i <= 4; i++) {
        const val = min + (max - min) * (4 - i) / 4, yy = y(val);
        context.strokeStyle = '#293c53'; context.lineWidth = 1;
        context.beginPath(); context.moveTo(pad.left, yy); context.lineTo(w - pad.right, yy); context.stroke();
        context.fillStyle = '#8298b1'; context.fillText(val.toFixed(val >= 10 ? 1 : 2), pad.left - 8, yy);
      }
      context.textBaseline = 'top'; context.textAlign = 'center'; context.fillStyle = '#8298b1';
      for (const index of [...new Set([0, Math.floor((vals.length - 1) / 2), vals.length - 1])]) {
        const stamp = new Date(readings[index]?.timestamp || Date.now());
        context.fillText(Number.isNaN(stamp.getTime()) ? '' : stamp.toLocaleTimeString(), x(index), h - 23);
      }
      const gradient = context.createLinearGradient(0, pad.top, 0, h - pad.bottom);
      gradient.addColorStop(0, 'rgba(77,220,196,.23)'); gradient.addColorStop(1, 'rgba(77,220,196,.007)');
      context.beginPath(); vals.forEach((v, i) => i ? context.lineTo(x(i), y(v)) : context.moveTo(x(i), y(v)));
      context.lineTo(x(vals.length - 1), h - pad.bottom); context.lineTo(x(0), h - pad.bottom);
      context.closePath(); context.fillStyle = gradient; context.fill();
      context.beginPath(); vals.forEach((v, i) => i ? context.lineTo(x(i), y(v)) : context.moveTo(x(i), y(v)));
      context.lineJoin = 'round'; context.strokeStyle = '#58e1ca'; context.lineWidth = 2.5; context.stroke();
      context.beginPath(); context.arc(x(vals.length - 1), y(vals.at(-1)), 4, 0, Math.PI * 2);
      context.fillStyle = '#b4ffee'; context.fill();
    };
    render();
    const resize = new ResizeObserver(render);
    resize.observe(canvas);
    return () => resize.disconnect();
  }, [readings, metric]);
  return <div className="chart-container">
    <canvas ref={ref} aria-label={`${METRICS[metric]} trend from ${readings.length} synthetic samples`} role="img" />
    {!readings.length && <div className="chart-placeholder">Streaming sensor readings…</div>}
  </div>;
}
