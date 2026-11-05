# CampusPulse Live — Digital Twin Predictive Maintenance Simulator

**Continuous synthetic sensor readings + real pretrained ML inference.** The upgraded frontend and FastAPI backend run on your Windows machine. It does not require a physical IoT device, external database, or active Internet connection. All charts are built with the browser's native Canvas API; the optional external Google Font falls back to system fonts when offline.

## Windows PowerShell installation

From the extracted `uni projects` directory:

```powershell
py --version
py -m pip install -r requirements-web.txt
py -m uvicorn web.api:app --host 127.0.0.1 --port 8000
```

If the `py` launcher is not available, replace `py` with `python`. If Windows Application Control blocks pip or Python, use an approved interpreter and ask the device administrator; do not disable the security policy.

Open **http://127.0.0.1:8000** for the dashboard and **http://127.0.0.1:8000/docs** for interactive API documentation.

## Live simulator behavior

- Replays time-ordered baseline telemetry from the original four-asset synthetic dataset; adds small bounded, deterministic pseudo-random sensor noise.
- Generates one synthetic reading **per asset per second** at 1× speed. At 2× and 5× speed the simulator advances two or five *source samples* per second while the UI still receives up to one event per real second.
- Each new sample reruns the original saved classifier and RUL regressor with **four contiguous real sequence sensor values** for rolling mean and standard deviation. Health/status/recommendations are recomputed, not pre-scripted.
- Two timestamps are tracked: `wall_timestamp` (real UTC emission time) and `source_timestamp` (original 2026 synthetic CSV timeline). Source data represents 15-minute virtual intervals; **one simulated source interval is accelerated to one real second** at 1×. Do not interpret 1× as real-time physical duration.
- Scenario selection injects one of three progressively increasing virtual anomalies: bearing wear, overheating or power surge. The model may or may not mark every scenario CRITICAL: it uses the actual pretrained model response and the supplied thresholds.
- 'Clear fault' removes the additional anomaly immediately; previous simulated readings remain in rolling history until replaced by new readings.
- Pause/resume and reset are local controls. Reset uses the same pseudo-random seed, clears anomaly state and resets the sample position.
- Data exists **in memory for one server process**, with a 240-sample rolling history for each asset. It is not persisted across restarts and is not synchronized between multiple server workers. Use **one Uvicorn worker**, without `--workers N` or `--reload` when demonstrating a consistent continuous stream.
- The server-sent event feed reconnects automatically after short network interruptions. All API controls are intended for a localhost demonstration, not an internet-facing service.

## API

| Endpoint | Method | Function |
|---|---|---|
| `/api/live/overview` | GET | Latest states, statuses, counters and simulation configuration |
| `/api/live/events` | GET | Server-Sent Events containing changing overview snapshots |
| `/api/live/assets/{asset_id}/history?limit=100` | GET | Last 8–240 recent live synthetic samples |
| `/api/live/control` | POST | Pause, resume, reset, speed, inject or clear |
| `/api/overview?at=2026-03-15T12:00` | GET | Original historical dataset replay with proper rolling features |
| `/api/assets/{asset_id}/history?limit=192` | GET | Original archived historical samples |
| `/api/health` | GET | Data/model checks and simulator readiness |

### Control examples (PowerShell)

```powershell
Invoke-RestMethod 'http://127.0.0.1:8000/api/live/control' -Method Post -ContentType 'application/json' -Body '{"action":"inject","asset_id":"Water_Pump_Central","scenario":"bearing_wear"}'
Invoke-RestMethod 'http://127.0.0.1:8000/api/live/control' -Method Post -ContentType 'application/json' -Body '{"action":"clear","asset_id":"Water_Pump_Central"}'
```

## Automated tests

```powershell
py -m pytest -q tests/
```

**Limitations:** Synthetic data and engineered faults are illustrative. RUL is extrapolative outside the model's training domain. The original models were saved with a different scikit-learn version on the creator's machine; a version-matched Python environment is recommended if compatibility warnings occur. This project is not a real-equipment management system and must not be used to trigger safety-critical action.
