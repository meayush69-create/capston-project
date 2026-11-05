# CampusPulse — React + Vite, Vercel-ready

This is a component-based React conversion of the **CampusPulse Smart Campus Digital Twin for Predictive Maintenance** interface and live synthetic simulator. The original dashboard layout, dark theme, four campus assets, live telemetry chart, fault-injection laboratory, pause/resume, speed controls, and maintenance advisory have been retained and adapted to React.

**Source provenance:** This conversion uses the CampusPulse live project archive supplied earlier in the conversation (`web/static/index.html`, `web/static/style.css`, `web/static/app.js`, and `web/api.py`). The GitHub `capston-project` URL could not be fetched in the creation environment; differences introduced on GitHub after the supplied archive may not be included.

## Recommended: Vercel zero-config browser demo

The default deployment is a **fully functional static React application**. It runs continuously in the browser without a Python process, database, or external API. Four assets produce synthetic readings, and the simulated faults alter displayed trends, status, and recommendations. Every visitor receives an independent session, and resetting the page restarts the simulation.

> **Important:** This default mode uses transparent, deterministic **educational heuristics** for risk and remaining-life estimates, NOT the original serialized scikit-learn models. It is an interactive, deployable simulator, not a live ML inference backend. The UI always identifies which mode is active.

### Run locally (Node.js 18+)

```powershell
npm install
npm run dev
```

Open http://localhost:5173. For a production build:

```powershell
npm run build
npm run preview
```

This React build does not require `pip.exe`. It avoids the earlier Windows Application Control error because the default demo needs only Node.js/npm.

### Deploy from GitHub to Vercel

1. Create a new repository or copy the contents of this package to the **root of your existing GitHub repository**. Don't upload the ZIP itself as the only repository file.
2. Import the GitHub repository in [Vercel](https://vercel.com/new).
3. If files are at the repository root, set **Root Directory** to `./`; if placed under a subfolder such as `campuspulse-react`, select that subfolder.
4. Framework preset: **Vite**. Build command: `npm run build`. Output directory: `dist`. Install command: `npm install`.
5. Leave `VITE_API_BASE_URL` **unset** to use the standalone browser simulation; click Deploy.

`vercel.json` supplies the SPA fallback and Vite output. No server or scheduled task is needed for browser mode.

## Optional: use the real scikit-learn predictions

The `backend/` folder includes the original FastAPI live-simulator logic and **trusted original training artifacts**. This is an **independent Python service** that must run on an always-on platform supporting a long-running ASGI process and Server-Sent Events (such as Render, Railway, Fly.io, or your own host). Do not deploy it as a Vercel serverless function: the in-memory background loop and long-held SSE connections are not designed for that environment.

To run the companion backend locally:

```powershell
cd backend
python -m pip install -r requirements.txt
python -m uvicorn api:app --host 127.0.0.1 --port 8000
```

Back in the React project root, create `.env.local`:

```env
VITE_API_BASE_URL=http://127.0.0.1:8000
```

Then restart Vite (`npm run dev`). The React application will use the backend's `/api/live/overview`, `/api/live/assets/{id}/history`, `/api/live/control`, and `/api/live/events` endpoints. The backend then performs **actual scikit-learn inference**. Backend mode is clearly shown in the UI.

For production, deploy `backend/` separately and add these environment variables:

- On Python host: `CORS_ORIGINS=https://your-project.vercel.app` (also list custom domains or local test domains as needed).
- On Vercel: `VITE_API_BASE_URL=https://your-python-backend.example.com` (the backend must support HTTPS).

Rebuild/redeploy the React app after setting `VITE_API_BASE_URL`, since Vite embeds it at build time. Note that this is a browser-visible URL, **not a secret**.

The original FastAPI simulator is process-local: run **one process/worker**. Multiple workers will have independent, nonshared simulation histories. Its models may require matching scikit-learn versions; use a trusted Python environment, investigate deserialization-version warnings, and pin dependencies for production use. Real hardware control, real IoT ingestion, centralized storage, authentication and production resilience have **not** been implemented.

## Layout

```
index.html
src/
  App.jsx                       # React UI and simulation controls
  components/SensorChart.jsx    # Dependency-free canvas trend chart
  hooks/useCampusSimulation.js  # Browser simulation or optional REST/SSE backend adapter
  lib/simulator.js              # Synthetic data and explicitly heuristic scoring
  main.jsx
  style.css                     # Adapted from original CampusPulse web/static/style.css
backend/                        # OPTIONAL separately hosted FastAPI ML simulator
vite.config.js
vercel.json
.env.example
```

## Acceptance checklist

- `npm run build` generates `dist/` (run in an environment where npm registry packages can be installed).
- Overview renders four asset cards; chart updates roughly once a second.
- Temperature, vibration and power tabs update the visualization.
- Changing the selected asset changes the chart and recommendation.
- Fault injection increases selected synthetic sensor values over 12 ticks; clear removes the scenario.
- Pause freezes the stream; resume continues; reset returns to baseline; speed allows 1×/2×/5×.
- Reload in browser mode starts a fresh visitor-local simulation.
- In backend mode, verify the Python host `/api/health` first and check cross-origin SSE and POST controls.

## Security and scientific claims

All data is synthetic. Browser-mode results are heuristic estimates, not validated predictions. Backend-mode results are predictions of supplied models trained on synthetic data; they are not field-validated failure probabilities or RUL guarantees. Neither mode should be used to control or safeguard real equipment.
