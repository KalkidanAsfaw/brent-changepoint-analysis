"""Tests for the dashboard Flask API."""

import pytest

from dashboard.backend.app import create_app


@pytest.fixture(scope="module")
def client():
    app = create_app()
    app.testing = True
    return app.test_client()


def test_prices_full_range(client):
    rows = client.get("/api/prices").get_json()
    assert len(rows) == 9011
    assert rows[0] == {"date": "1987-05-20", "price": 18.63, "log_return": None}


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
    assert len(data["rolling_volatility"]) > 1000
    assert len(data["event_impacts"]) >= 10
    invasion = next(e for e in data["event_impacts"]
                    if e["name"].startswith("Russia invades"))
    assert invasion["pct_change"] > 0


def test_indicators_bad_window(client):
    assert client.get("/api/indicators?window=abc").status_code == 400
    assert client.get("/api/indicators?window=1").status_code == 400
