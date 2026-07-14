"""Tests for the dashboard Flask API.

Uses a synthetic price series (the real CSV is downloaded separately and not
in git, so CI never has it). Events and change point results are committed
files and used as-is.
"""

import numpy as np
import pandas as pd
import pytest

from dashboard.backend.app import create_app

START, END = "2019-06-03", "2022-11-14"


@pytest.fixture(scope="module")
def prices_csv(tmp_path_factory):
    # Monotonically increasing prices → every event impact is positive,
    # and log returns are constant and well-defined.
    dates = pd.bdate_range(START, END)
    prices = 50 * 1.0005 ** np.arange(len(dates))
    path = tmp_path_factory.mktemp("data") / "prices.csv"
    pd.DataFrame({
        "Date": dates.strftime("%d-%b-%y"),
        "Price": prices.round(2),
    }).to_csv(path, index=False)
    return path, len(dates)


@pytest.fixture(scope="module")
def client(prices_csv):
    app = create_app(prices_csv=prices_csv[0])
    app.testing = True
    return app.test_client()


def test_prices_full_range(client, prices_csv):
    rows = client.get("/api/prices").get_json()
    assert len(rows) == prices_csv[1]
    assert rows[0] == {"date": START, "price": 50.0, "log_return": None}
    assert rows[1]["log_return"] == pytest.approx(np.log(1.0005), abs=1e-4)


def test_prices_date_filter(client):
    rows = client.get("/api/prices?start=2020-03-01&end=2020-03-31").get_json()
    assert all(r["date"].startswith("2020-03") for r in rows)
    assert 0 < len(rows) < 25


def test_prices_empty_range_404(client):
    resp = client.get("/api/prices?start=2030-01-01&end=2030-02-01")
    assert resp.status_code == 404


def test_events(client):
    events = client.get("/api/events").get_json()
    assert len(events) >= 10
    assert {"date", "name", "category", "description"} <= set(events[0])


def test_changepoints(client):
    cps = client.get("/api/changepoints").get_json()
    assert "2022 Russia invasion" in cps
    cp = cps["2022 Russia invasion"]
    assert cp["change_date"] == "2022-02-24"
    assert {"mean_price_before", "mean_price_after", "price_change_pct",
            "ann_vol_before", "ann_vol_after"} <= set(cp)


def test_indicators(client):
    data = client.get("/api/indicators?window=30").get_json()
    assert data["window_days"] == 30
    assert len(data["rolling_volatility"]) > 100
    # Events inside the synthetic span (Abqaiq 2019 → invasion 2022).
    assert len(data["event_impacts"]) >= 5
    invasion = next(e for e in data["event_impacts"]
                    if e["name"].startswith("Russia invades"))
    assert invasion["pct_change"] > 0  # prices are monotonically increasing


def test_indicators_bad_window(client):
    assert client.get("/api/indicators?window=abc").status_code == 400
    assert client.get("/api/indicators?window=1").status_code == 400
