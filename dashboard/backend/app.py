"""Flask API serving the Brent change point analysis results.

Endpoints
---------
GET /api/prices?start=YYYY-MM-DD&end=YYYY-MM-DD   Daily prices + log returns
GET /api/events                                    Researched key events
GET /api/changepoints                              Detected breaks + impacts
GET /api/indicators?window=30                      Rolling volatility series
                                                   and per-event price impact

All data is read once at startup from the repository's data/ directory.
"""

import json
import sys
from pathlib import Path

import numpy as np
from flask import Flask, jsonify, request
from flask_cors import CORS

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from src.data_loader import add_log_returns, load_events, load_prices  # noqa: E402

RESULTS_JSON = ROOT / "data" / "changepoint_results.json"


def create_app() -> Flask:
    app = Flask(__name__)
    CORS(app)

    prices = add_log_returns(load_prices())
    events = load_events()
    changepoints = json.loads(RESULTS_JSON.read_text())

    def parse_range():
        start = request.args.get("start", str(prices.index.min().date()))
        end = request.args.get("end", str(prices.index.max().date()))
        try:
            window = prices.loc[start:end]
        except (KeyError, ValueError) as exc:
            return None, (jsonify(error=f"invalid date range: {exc}"), 400)
        if window.empty:
            return None, (jsonify(error="no data in requested range"), 404)
        return window, None

    @app.get("/api/prices")
    def get_prices():
        window, err = parse_range()
        if err:
            return err
        return jsonify([
            {
                "date": str(d.date()),
                "price": round(float(p), 2),
                "log_return": None if np.isnan(r) else round(float(r), 5),
            }
            for d, p, r in zip(window.index, window["Price"], window["LogReturn"])
        ])

    @app.get("/api/events")
    def get_events():
        return jsonify([
            {
                "date": str(ev["event_date"].date()),
                "name": ev["event_name"],
                "category": ev["category"],
                "description": ev["description"],
            }
            for _, ev in events.iterrows()
        ])

    @app.get("/api/changepoints")
    def get_changepoints():
        return jsonify(changepoints)

    @app.get("/api/indicators")
    def get_indicators():
        try:
            window_days = int(request.args.get("window", 30))
        except ValueError:
            return jsonify(error="window must be an integer"), 400
        if not 2 <= window_days <= 365:
            return jsonify(error="window must be between 2 and 365"), 400

        vol = prices["LogReturn"].rolling(window_days).std() * np.sqrt(252)
        # Thin the ~9k-point series for charting: keep every 5th point.
        vol = vol.dropna().iloc[::5]

        event_impacts = []
        for _, ev in events.iterrows():
            date = ev["event_date"]
            before = prices["Price"].loc[:date].tail(window_days)
            after = prices["Price"].loc[date:].head(window_days)
            if before.empty or after.empty:
                continue
            b, a = float(before.mean()), float(after.mean())
            event_impacts.append({
                "date": str(date.date()),
                "name": ev["event_name"],
                "category": ev["category"],
                "avg_price_before": round(b, 2),
                "avg_price_after": round(a, 2),
                "pct_change": round(100 * (a - b) / b, 1),
            })

        return jsonify({
            "window_days": window_days,
            "rolling_volatility": [
                {"date": str(d.date()), "volatility": round(float(v), 4)}
                for d, v in vol.items()
            ],
            "event_impacts": event_impacts,
        })

    return app


if __name__ == "__main__":
    create_app().run(host="127.0.0.1", port=5001, debug=True)
