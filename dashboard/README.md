# Dashboard — Brent Change Point Explorer

Flask backend + React (Vite + Recharts) frontend for exploring how major
events relate to Brent oil price changes and to the Bayesian change points
detected in Task 2.

## Features

- **Change point cards** — one per detected break, showing the break date,
  mean price before → after, % change, and the volatility regime shift;
  clicking a card zooms the price chart to that break's window.
- **Price chart** — daily Brent prices with researched events (gray dashed)
  and detected change points (violet dashed) overlaid; crosshair tooltip.
- **Event highlight** — click a bar in the "avg price change around events"
  chart to highlight that event on the price chart and open its description.
- **Filters** — date-range presets (full history, 2008 crisis, OPEC price
  war, COVID-19, 2022 invasion), custom date inputs, and an event-category
  filter; every panel re-renders against the same slice.
- **Indicators** — 30-day rolling annualized volatility and per-event
  ±30-day average price impact.
- Responsive layout (desktop / tablet / mobile) and light/dark theme
  following the system preference.

## API endpoints (Flask, port 5001)

| Endpoint | Query params | Returns |
|---|---|---|
| `GET /api/prices` | `start`, `end` (YYYY-MM-DD) | Daily `{date, price, log_return}` |
| `GET /api/events` | — | 16 researched events with category + description |
| `GET /api/changepoints` | — | Detected breaks with quantified impacts (from Task 2) |
| `GET /api/indicators` | `window` (days, default 30) | Rolling volatility series + per-event avg price change |

Errors return JSON `{error}` with 400 (bad params) or 404 (empty range).

## Running locally

Backend (from the repo root, venv active, data downloaded per `data/README.md`):

```bash
pip install -r requirements.txt
python dashboard/backend/app.py        # serves on http://127.0.0.1:5001
```

Frontend (Node 20+):

```bash
cd dashboard/frontend
npm install
npm run dev                            # http://localhost:5173, proxies /api to :5001
```

Production build: `npm run build` (outputs `dashboard/frontend/dist/`).

## Screenshots

See `dashboard/screenshots/` — full history, COVID window zoom, event
highlight, change point drill-down, dark mode, and mobile layout.
