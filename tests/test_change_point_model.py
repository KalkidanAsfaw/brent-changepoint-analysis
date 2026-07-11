"""Tests for the change point model helpers (no MCMC sampling in CI)."""

import arviz as az
import numpy as np
import pandas as pd
import pytest

from src.change_point_model import (
    build_model,
    nearest_events,
    summarize_change,
    tau_posterior_dates,
    window,
)


@pytest.fixture
def win():
    idx = pd.bdate_range("2020-01-01", periods=100)
    rng = np.random.default_rng(0)
    r = np.concatenate([rng.normal(0, 0.01, 60), rng.normal(0, 0.04, 40)])
    return pd.DataFrame({"Price": 50 * np.exp(np.cumsum(r)), "LogReturn": r}, index=idx)


@pytest.fixture
def fake_idata():
    # Posterior concentrated at tau=60 with sigma_2 > sigma_1 always.
    n = 100
    shape = (2, 50)
    rng = np.random.default_rng(1)
    return az.from_dict(posterior={
        "tau": np.full(shape, 60),
        "mu_1": rng.normal(0.001, 1e-4, shape),
        "mu_2": rng.normal(-0.002, 1e-4, shape),
        "sigma_1": np.abs(rng.normal(0.01, 1e-4, shape)),
        "sigma_2": np.abs(rng.normal(0.04, 1e-4, shape)),
    })


def test_window_slices_dates(win):
    out = window(win, "2020-02-01", "2020-03-31")
    assert out.index.min() >= pd.Timestamp("2020-02-01")
    assert out.index.max() <= pd.Timestamp("2020-03-31")


def test_window_rejects_too_small(win):
    with pytest.raises(ValueError):
        window(win, "2020-01-01", "2020-01-07")


def test_build_model_has_expected_rvs(win):
    model = build_model(win["LogReturn"].to_numpy())
    names = {rv.name for rv in model.free_RVs}
    assert names == {"tau", "mu_1", "mu_2", "sigma_1", "sigma_2"}


def test_summarize_change(fake_idata, win):
    res = summarize_change(fake_idata, win)
    assert res["change_date"] == win.index[60].strftime("%Y-%m-%d")
    assert res["p_vol_increased"] == 1.0
    assert res["ann_vol_after"] > res["ann_vol_before"]
    expected_pct = 100 * (win["Price"].iloc[60:].mean()
                          / win["Price"].iloc[:60].mean() - 1)
    assert res["price_change_pct"] == pytest.approx(expected_pct, abs=0.1)


def test_tau_posterior_dates(fake_idata, win):
    dates = tau_posterior_dates(fake_idata, win.index)
    assert (dates == win.index[60]).all()


def test_nearest_events():
    events = pd.DataFrame({
        "event_date": pd.to_datetime(["2020-03-06", "2020-03-11", "2019-09-14"]),
        "event_name": ["OPEC+ collapse", "COVID pandemic", "Abqaiq attack"],
    })
    near = nearest_events(events, "2020-03-09", within_days=45)
    assert set(near["event_name"]) == {"OPEC+ collapse", "COVID pandemic"}
    assert (near["days_from_break"] <= 45).all()
