"""CampusPulse synthetic live digital twin and historical simulation API.

No real equipment connections or automated control commands. This is a local academic demo.
"""
from __future__ import annotations

import asyncio
import contextlib
import json
import random
import warnings
from collections import deque
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path
from typing import Literal

import joblib
import pandas as pd
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

ROOT = Path(__file__).resolve().parents[1]
STATIC = Path(__file__).resolve().parent / 'static'
SENSORS = ('ambient_temp_c','internal_temp_c','vibration_rms_mms','acoustic_db',
           'pressure_psi','power_kw','campus_occupancy_flag')
MOVING = ('vibration_rms_mms','internal_temp_c','power_kw')
BASE_INTERVAL = 1.0  # one simulated 15-minute sample per real second at 1x

@lru_cache(maxsize=1)
def resources():
    frame = pd.read_csv(ROOT/'smart_campus_iot_telemetry.csv', parse_dates=['timestamp'])
    needed = {'timestamp','asset_id','asset_type',*SENSORS}
    if missing := needed - set(frame.columns):
        raise RuntimeError(f'Missing dataset columns: {sorted(missing)}')
    if frame[list(SENSORS)].isna().any().any():
        raise RuntimeError('Dataset has missing sensor measurements')
    frame = frame.sort_values(['asset_id','timestamp']).reset_index(drop=True)
    # Serialized artifacts are supplied with the original local project: do not load untrusted pickle files.
    with warnings.catch_warnings():
        warnings.filterwarnings('ignore', category=UserWarning, message='Trying to unpickle estimator')
        clf = joblib.load(ROOT/'failure_classifier.pkl')
        reg = joblib.load(ROOT/'rul_regressor.pkl')
    cols = joblib.load(ROOT/'feature_columns.pkl')
    groups = {name: group.reset_index(drop=True) for name,group in frame.groupby('asset_id',sort=True)}
    return frame,groups,clf,reg,list(cols)

def predict(asset_id,asset_type,records,timestamp,mode):
    _,_,classifier,regressor,cols = resources()
    current = {k:float(records[-1][k]) for k in SENSORS}
    current['temp_gradient'] = current['internal_temp_c']-current['ambient_temp_c']
    window = pd.DataFrame(list(records)[-4:])
    for k in MOVING:
        current[k+'_roll_mean'] = float(window[k].mean())
        current[k+'_roll_std'] = float(window[k].std()) if len(window)>1 else 0.0
    x = pd.DataFrame([{name:current[name] for name in cols}],columns=cols)
    with warnings.catch_warnings():
        warnings.filterwarnings('ignore', category=UserWarning)
        p = float(classifier.predict_proba(x)[0][1])
        rul = max(0.0,float(regressor.predict(x)[0]))
    health = max(0.0,100.0-80.0*p-0.15*max(0.0,150.0-rul))
    if p>0.65 or health<40:
        status,action,energy = ('CRITICAL','Dispatch an urgent inspection; consider transferring load to a standby asset.','DERATED_ECO')
    elif p>0.35 or health<70:
        status,action,energy = ('WARNING','Schedule a preventive inspection during an off-peak window.','LOAD_BALANCED')
    else:
        status,action,energy = ('HEALTHY','Continue monitoring and scheduled routine maintenance.','CAMPUS_EFFICIENCY_OPTIMIZED')
    return dict(asset_id=asset_id,asset_type=asset_type,timestamp=timestamp,
                health_score=round(health,1),status=status,
                failure_probability=round(p,4),estimated_rul_hours=round(rul,1),
                energy_mode=energy,action=action,
                telemetry={k:round(v,3) for k,v in current.items() if k in SENSORS},
                mode=mode)

def parse_replay_date(value):
    if value is None:return None
    try:
        stamp = pd.Timestamp(value)
        if stamp.tzinfo is not None:raise ValueError()
        return stamp
    except (ValueError,TypeError):
        raise HTTPException(422,detail='Use a timezone-free ISO time, e.g. 2026-02-15T12:00')

def historical(asset_id,at=None):
    _,groups,*_=resources()
    if asset_id not in groups:raise HTTPException(404,'Unknown asset ID')
    group = groups[asset_id]
    stamp = parse_replay_date(at)
    if stamp is not None:group = group.loc[group.timestamp<=stamp]
    if group.empty:raise HTTPException(404,'No telemetry available for the selected date')
    rows = [{k:float(v) for k,v in rec.items() if k in SENSORS} for rec in group.tail(4).to_dict('records')]
    last=group.iloc[-1]
    return predict(asset_id,str(last.asset_type),rows,last.timestamp.isoformat(),'HISTORICAL')

class Controls(BaseModel):
    action:Literal['pause','resume','reset','speed','inject','clear']
    asset_id:str|None=None
    scenario:Literal['normal','bearing_wear','overheating','power_surge']|None=None
    speed:Literal[1,2,5]|None=None

class Simulation:
    """Process-local seeded simulator; state is intentionally never claimed to be durable."""
    def __init__(self):
        self.lock=asyncio.Lock()
        self.notify=asyncio.Condition()
        self.version=0
        self.seed=2026
        self.running=True
        self.speed=1
        self.tick_count=0
        self.assets={}
        self.start()

    def start(self):
        _,groups,*_=resources()
        self.random=random.Random(self.seed)
        self.groups=groups
        self.assets={name:{'type':str(g.iloc[0].asset_type),
            'history':deque(maxlen=240),'recent':deque(maxlen=4),
            'scenario':'normal','scenario_age':0,'state':None} for name,g in groups.items()}
        self.tick_count=0
        self._step() # warm initial frame

    def _step(self):
        # At 1x one real second = one successive source sample (15 simulation minutes).
        position=self.tick_count%min(len(g) for g in self.groups.values())
        wall=datetime.now(timezone.utc).isoformat(timespec='seconds')
        for name,group in self.groups.items():
            asset=self.assets[name]
            row=group.iloc[position]
            sensor={k:float(row[k]) for k in SENSORS}
            # Small bounded noise makes source-derived sensor streams feel alive while preserving their ranges.
            for k,fraction in [('ambient_temp_c',.006),('internal_temp_c',.008),
                                ('vibration_rms_mms',.016),('acoustic_db',.004),
                                ('pressure_psi',.006),('power_kw',.008)]:
                sensor[k]=max(0.,sensor[k]*(1+self.random.uniform(-fraction,fraction)))
            mode=asset['scenario']
            if mode!='normal':
                age=asset['scenario_age']+1
                asset['scenario_age']=age
                strength=min(1.,age/12.)
                if mode=='bearing_wear':
                    sensor['vibration_rms_mms']+=7.5*strength
                    sensor['acoustic_db']+=18*strength
                    sensor['internal_temp_c']+=20*strength
                elif mode=='overheating':
                    sensor['internal_temp_c']+=48*strength
                    sensor['power_kw']+=14*strength
                    sensor['vibration_rms_mms']+=4.0*strength
                elif mode=='power_surge':
                    sensor['power_kw']+=43*strength
                    sensor['internal_temp_c']+=28*strength
                    sensor['vibration_rms_mms']+=3.5*strength
            asset['recent'].append(sensor)
            generated=predict(name,asset['type'],asset['recent'],wall,'LIVE_SYNTHETIC')
            generated.update(scenario=mode,sequence=self.tick_count+1,
                wall_timestamp=wall,source_timestamp=row.timestamp.isoformat())
            asset['state']=generated
            asset['history'].append({'timestamp':wall,'sequence':self.tick_count+1,
                                     'source_timestamp':row.timestamp.isoformat(),**sensor})
        self.tick_count+=1
        self.version+=1

    def overview(self):
        states=[asset['state'] for asset in self.assets.values()]
        return {'mode':'LIVE_SYNTHETIC','running':self.running,'speed':self.speed,
            'sequence':self.tick_count,'version':self.version,
            'updated_at':states[0]['wall_timestamp'],
            'source':'Synthetic streaming simulation (not connected to physical sensors)',
            'assets':states,
            'counts':{status:sum(s['status']==status for s in states)
                      for status in ['HEALTHY','WARNING','CRITICAL']},
            'average_health':round(sum(s['health_score'] for s in states)/len(states),1)}

simulator:Simulation|None=None

async def tick_loop():
    while True:
        await asyncio.sleep(BASE_INTERVAL)
        sim=simulator
        if sim is None:continue
        async with sim.lock:
            if sim.running:
                for _ in range(sim.speed):sim._step()
                async with sim.notify:sim.notify.notify_all()

@contextlib.asynccontextmanager
async def lifespan(app):
    global simulator
    simulator=Simulation()
    task=asyncio.create_task(tick_loop())
    try:yield
    finally:
        task.cancel()
        with contextlib.suppress(asyncio.CancelledError):await task
        simulator=None

app=FastAPI(title='CampusPulse Synthetic Digital Twin',version='2.0.0',lifespan=lifespan)
app.mount('/static',StaticFiles(directory=STATIC),name='static')

def live():
    if simulator is None:raise HTTPException(503,'Live simulation not initialized')
    return simulator

@app.get('/',include_in_schema=False)
def homepage():return FileResponse(STATIC/'index.html')

@app.get('/api/health')
def health():
    try:
        frame,groups,*_=resources()
        return {'status':'ok','records':len(frame),'assets':len(groups),
                'live_simulation':'ready' if simulator else 'not started', 'source':'synthetic'}
    except Exception:raise HTTPException(503,'Model files or dataset unavailable')

@app.get('/api/overview')
def overview(at:str|None=None):
    _,groups,*_=resources()
    states=[historical(name,at) for name in groups]
    return {'mode':'HISTORICAL','assets':states,
            'counts':{status:sum(s['status']==status for s in states) for status in ['HEALTHY','WARNING','CRITICAL']},
            'average_health':round(sum(s['health_score'] for s in states)/len(states),1),
            'source':'Archived synthetic dataset'}

@app.get('/api/assets/{asset_id}')
def asset_detail(asset_id:str,at:str|None=None):return historical(asset_id,at)

@app.get('/api/assets/{asset_id}/history')
def asset_history(asset_id:str,at:str|None=None,limit:int=Query(192,ge=8,le=1000)):
    _,groups,*_=resources()
    if asset_id not in groups:raise HTTPException(404,'Unknown asset ID')
    frame=groups[asset_id]
    stamp=parse_replay_date(at)
    if stamp is not None:frame=frame.loc[frame.timestamp<=stamp]
    frame=frame.tail(limit)[['timestamp',*SENSORS]].copy()
    frame['timestamp']=frame['timestamp'].dt.strftime('%Y-%m-%dT%H:%M:%S')
    return {'asset_id':asset_id,'count':len(frame),'readings':frame.to_dict('records')}

@app.get('/api/live/overview')
async def live_overview():
    sim=live()
    async with sim.lock:return sim.overview()

@app.get('/api/live/assets/{asset_id}/history')
async def live_history(asset_id:str,limit:int=Query(100,ge=8,le=240)):
    sim=live()
    async with sim.lock:
        if asset_id not in sim.assets:raise HTTPException(404,'Unknown asset ID')
        records=list(sim.assets[asset_id]['history'])[-limit:]
        return {'asset_id':asset_id,'count':len(records),'readings':records,'mode':'LIVE_SYNTHETIC'}

@app.post('/api/live/control')
async def control(payload:Controls):
    sim=live()
    async with sim.lock:
        action=payload.action
        if action=='reset':
            sim.running=True;sim.speed=1;sim.start()
        elif action=='pause':sim.running=False
        elif action=='resume':sim.running=True
        elif action=='speed':
            if payload.speed is None:raise HTTPException(422,'speed required')
            sim.speed=payload.speed
        elif action in ('inject','clear'):
            if not payload.asset_id or payload.asset_id not in sim.assets:
                raise HTTPException(422,'Choose a valid asset_id')
            if action=='inject' and (payload.scenario is None or payload.scenario=='normal'):
                raise HTTPException(422,'Choose bearing_wear, overheating or power_surge')
            a=sim.assets[payload.asset_id]
            a['scenario']=payload.scenario if action=='inject' else 'normal'
            a['scenario_age']=0
        sim.version+=1
        response=sim.overview()
        async with sim.notify:sim.notify.notify_all()
        return response

@app.get('/api/live/events')
async def live_events():
    """Server-sent events. Initial snapshot + up to one update per physical second."""
    sim=live()
    async def stream():
        last=-1
        while True:
            async with sim.lock:
                version=sim.version
                data=sim.overview()
            if version!=last:
                yield 'event: overview\ndata: '+json.dumps(data,allow_nan=False)+'\n\n'
                last=version
            try:
                async with sim.notify:
                    await asyncio.wait_for(sim.notify.wait_for(lambda: sim.version != last),timeout=15)
            except asyncio.TimeoutError:
                yield ': keepalive\n\n'
    return StreamingResponse(stream(),media_type='text/event-stream',headers={
        'Cache-Control':'no-cache, no-transform','X-Accel-Buffering':'no'})
