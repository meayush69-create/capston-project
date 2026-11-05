/**
 * Browser-only simulation: performs independent synthetic sensor generation and
 * an EXPLICITLY HEURISTIC risk/RUL calculation. Does NOT execute trained Python ML.
 * In backend mode, the actual model scores are returned from FastAPI.
 */
export const ASSET_DEFS = [
  { id: 'HVAC_Chiller_01', type: 'HVAC', base: { ambient_temp_c: 30.2, internal_temp_c: 55, vibration_rms_mms: 3.4, acoustic_db: 65, pressure_psi: 74, power_kw: 36.8 }, phase: 0.4 },
  { id: 'HVAC_Chiller_02', type: 'HVAC', base: { ambient_temp_c: 29.4, internal_temp_c: 45.2, vibration_rms_mms: 2.1, acoustic_db: 58, pressure_psi: 71, power_kw: 31.9 }, phase: 1.7 },
  { id: 'Water_Pump_Central', type: 'Pump', base: { ambient_temp_c: 29.6, internal_temp_c: 61.2, vibration_rms_mms: 4.3, acoustic_db: 73, pressure_psi: 82, power_kw: 19.8 }, phase: 2.8 },
  { id: 'Elevator_Tower_A', type: 'Elevator', base: { ambient_temp_c: 28.8, internal_temp_c: 43.9, vibration_rms_mms: 2.4, acoustic_db: 58, pressure_psi: 45, power_kw: 12.4 }, phase: 4.2 },
];
export const SCENARIOS = {
  normal: 'Normal operation',
  bearing_wear: 'Bearing wear',
  overheating: 'Thermal overload',
  power_surge: 'Power surge',
};
export const METRICS = {
  internal_temp_c: 'Internal temperature (°C)',
  vibration_rms_mms: 'Vibration (mm/s)',
  power_kw: 'Power draw (kW)',
};
const clamp = (value, low, high) => Math.max(low, Math.min(high, value));
const round = (value, places = 2) => Number(value.toFixed(places));

export function createSimulator() {
  const assets = Object.fromEntries(ASSET_DEFS.map(def => [def.id, {
    type: def.type, scenario: 'normal', scenario_age: 0, state: null, history: [],
  }]));
  const simulation = { running: true, speed: 1, sequence: 0, assets, version: 0 };
  stepSimulator(simulation);
  return simulation;
}

function scoreSensor(sensor) {
  // Educational heuristic only. Thresholds are NOT calibrated for real machinery.
  const temp = clamp((sensor.internal_temp_c - 47) / 55, 0, 1);
  const vib = clamp((sensor.vibration_rms_mms - 2.5) / 11, 0, 1);
  const power = clamp((sensor.power_kw - 32) / 72, 0, 1);
  const acoustic = clamp((sensor.acoustic_db - 63) / 30, 0, 1);
  const p = clamp(0.02 + temp * 0.34 + vib * 0.46 + power * 0.11 + acoustic * 0.12, 0, .99);
  const rul = clamp(590 - 520 * p, 10, 590);
  const health = clamp(100 - 80 * p - .15 * Math.max(0, 150 - rul), 0, 100);
  let status = 'HEALTHY', action = 'Continue monitoring and scheduled routine maintenance.', energy_mode = 'CAMPUS_EFFICIENCY_OPTIMIZED';
  if (p > .65 || health < 40) {
    status = 'CRITICAL'; action = 'Dispatch an urgent inspection; consider transferring load to a standby asset.'; energy_mode = 'DERATED_ECO';
  } else if (p > .35 || health < 70) {
    status = 'WARNING'; action = 'Schedule a preventive inspection during an off-peak window.'; energy_mode = 'LOAD_BALANCED';
  }
  return { health_score: round(health, 1), failure_probability: round(p, 4), estimated_rul_hours: round(rul, 1), status, action, energy_mode };
}

export function stepSimulator(sim) {
  const t = sim.sequence;
  const wall = new Date().toISOString();
  for (const def of ASSET_DEFS) {
    const asset = sim.assets[def.id];
    const s = {};
    for (const [key, baseline] of Object.entries(def.base)) {
      const cycle = Math.sin(t * .11 + def.phase + key.length * .47) * .021;
      const secondary = Math.sin(t * .39 + def.phase * 3 + key.length) * .009;
      s[key] = round(Math.max(0, baseline * (1 + cycle + secondary)), 3);
    }
    s.campus_occupancy_flag = Math.floor(t / 12) % 3 === 2 ? 0 : 1;
    const scenario = asset.scenario;
    if (scenario !== 'normal') {
      asset.scenario_age += 1;
      const strength = Math.min(1, asset.scenario_age / 12);
      if (scenario === 'bearing_wear') {
        s.vibration_rms_mms += 8.7 * strength;
        s.acoustic_db += 21 * strength;
        s.internal_temp_c += 22 * strength;
      } else if (scenario === 'overheating') {
        s.internal_temp_c += 53 * strength;
        s.power_kw += 21 * strength;
        s.vibration_rms_mms += 4.5 * strength;
      } else if (scenario === 'power_surge') {
        s.power_kw += 54 * strength;
        s.internal_temp_c += 32 * strength;
        s.vibration_rms_mms += 4 * strength;
      }
    }
    const sensor = Object.fromEntries(Object.entries(s).map(([key, value]) => [key, round(value, 3)]));
    const state = scoreSensor(sensor);
    asset.state = {
      asset_id: def.id, asset_type: def.type, timestamp: wall, wall_timestamp: wall,
      telemetry: sensor, scenario, mode: 'BROWSER_SYNTHETIC', sequence: t + 1, ...state,
    };
    asset.history.push({ timestamp: wall, sequence: t + 1, ...sensor });
    if (asset.history.length > 240) asset.history.shift();
  }
  sim.sequence += 1;
  sim.version += 1;
}

export function snapshot(sim) {
  const assets = ASSET_DEFS.map(d => sim.assets[d.id].state);
  return {
    mode: 'BROWSER_SYNTHETIC', running: sim.running, speed: sim.speed,
    sequence: sim.sequence, version: sim.version, updated_at: assets[0].wall_timestamp,
    source: 'Synthetic browser-generated data (heuristic estimates, not trained ML)',
    assets, average_health: round(assets.reduce((n, a) => n + a.health_score, 0) / assets.length, 1),
    counts: Object.fromEntries(['HEALTHY', 'WARNING', 'CRITICAL'].map(s => [s, assets.filter(a => a.status === s).length])),
  };
}

export function controlSimulator(sim, action, { asset_id, scenario, speed } = {}) {
  if (action === 'reset') return createSimulator();
  if (action === 'pause') sim.running = false;
  else if (action === 'resume') sim.running = true;
  else if (action === 'speed') {
    if (![1, 2, 5].includes(speed)) throw Error('Speed must be 1×, 2× or 5×');
    sim.speed = speed;
  } else if (action === 'inject' || action === 'clear') {
    if (!sim.assets[asset_id]) throw Error('Select a valid virtual asset.');
    if (action === 'inject' && !['bearing_wear', 'overheating', 'power_surge'].includes(scenario)) throw Error('Select a valid synthetic fault.');
    sim.assets[asset_id].scenario = action === 'clear' ? 'normal' : scenario;
    sim.assets[asset_id].scenario_age = 0;
  } else throw Error('Unknown simulator control');
  sim.version++;
  return sim;
}
