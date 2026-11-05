from pathlib import Path
import sys
import time
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from fastapi.testclient import TestClient
from web.api import app, Simulation

def test_dataset_health():
    with TestClient(app) as client:
        response=client.get('/api/health')
        assert response.status_code==200
        assert response.json()['records']==34560
        assert response.json()['live_simulation']=='ready'

def test_initial_live_state():
    with TestClient(app) as client:
        data=client.get('/api/live/overview').json()
        assert len(data['assets'])==4
        assert data['sequence']>=1
        for a in data['assets']:
            assert a['mode']=='LIVE_SYNTHETIC'
            assert 'source_timestamp' in a and 'wall_timestamp' in a
            assert 0<=a['failure_probability']<=1
            assert 0<=a['health_score']<=100

def test_pause_and_resume():
    with TestClient(app) as client:
        assert client.post('/api/live/control',json={'action':'pause'}).status_code==200
        start=client.get('/api/live/overview').json()['sequence']
        time.sleep(1.2)
        assert client.get('/api/live/overview').json()['sequence']==start
        assert client.post('/api/live/control',json={'action':'resume'}).json()['running']
        time.sleep(1.2)
        assert client.get('/api/live/overview').json()['sequence']>start

def test_injected_anomaly_and_clear():
    with TestClient(app) as client:
        assert client.post('/api/live/control',json={
          'action':'inject','asset_id':'HVAC_Chiller_01','scenario':'overheating'}).status_code==200
        time.sleep(1.2)
        s=next(x for x in client.get('/api/live/overview').json()['assets'] if x['asset_id']=='HVAC_Chiller_01')
        assert s['scenario']=='overheating'
        assert client.post('/api/live/control',json={'action':'clear','asset_id':'HVAC_Chiller_01'}).status_code==200
        assert client.post('/api/live/control',json={'action':'reset'}).json()['sequence']==1

def test_invalid_scenario_or_asset():
    with TestClient(app) as client:
        assert client.post('/api/live/control',json={'action':'inject','asset_id':'FAKE','scenario':'overheating'}).status_code==422
        assert client.post('/api/live/control',json={'action':'speed','speed':99}).status_code==422
        assert client.get('/api/live/assets/FAKE/history').status_code==404
        assert client.get('/api/live/assets/HVAC_Chiller_01/history?limit=999').status_code==422

def test_history_and_historical_replay():
    with TestClient(app) as client:
        response=client.get('/api/overview?at=2026-02-15T12:00')
        assert response.status_code==200
        assert len(response.json()['assets'])==4
        bad=client.get('/api/overview?at=not-a-time')
        assert bad.status_code==422
        history=client.get('/api/live/assets/HVAC_Chiller_01/history').json()
        assert len(history['readings'])>=1
        assert client.get('/').status_code==200

def test_simulator_seed_reproducible():
    sim1=Simulation();sim2=Simulation()
    for asset_id in sim1.assets:
        assert sim1.assets[asset_id]['history'][0]['vibration_rms_mms']==sim2.assets[asset_id]['history'][0]['vibration_rms_mms']
