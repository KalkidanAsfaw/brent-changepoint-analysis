"""Bayesian change point model for Brent oil log returns (PyMC).

A single switch point ``tau`` (discrete uniform over the window) separates two
regimes with their own mean and volatility of daily log returns. Applied over
focused windows around candidate break periods rather than the full 35-year
series, since the model detects exactly one break.
"""

import arviz as az
import numpy as np
import pandas as pd
import pymc as pm

# Priors are scaled to daily log returns: |mean| well under 5%/day,
# volatility of a few percent per day.
MU_PRIOR_SIGMA = 0.05
SIGMA_PRIOR_SIGMA = 0.05


def window(df: pd.DataFrame, start: str, end: str) -> pd.DataFrame:
    """Slice a date-indexed frame to [start, end] and drop the NaN first return."""
    out = df.loc[start:end].dropna(subset=["LogReturn"])
    if len(out) < 30:
        raise ValueError(f"window {start}..{end} has only {len(out)} observations")
    return out


def build_model(returns: np.ndarray) -> pm.Model:
    """Change point model: separate mean and volatility before/after tau."""
    n = len(returns)
    idx = np.arange(n)
    with pm.Model() as model:
        tau = pm.DiscreteUniform("tau", lower=0, upper=n - 1)
        mu_1 = pm.Normal("mu_1", mu=0.0, sigma=MU_PRIOR_SIGMA)
        mu_2 = pm.Normal("mu_2", mu=0.0, sigma=MU_PRIOR_SIGMA)
        sigma_1 = pm.HalfNormal("sigma_1", sigma=SIGMA_PRIOR_SIGMA)
        sigma_2 = pm.HalfNormal("sigma_2", sigma=SIGMA_PRIOR_SIGMA)
        mu = pm.math.switch(idx < tau, mu_1, mu_2)
        sigma = pm.math.switch(idx < tau, sigma_1, sigma_2)
        pm.Normal("obs", mu=mu, sigma=sigma, observed=returns)
    return model


def fit(
    returns: np.ndarray,
    draws: int = 2000,
    tune: int = 2000,
    chains: int = 4,
    random_seed: int = 42,
) -> az.InferenceData:
    """Sample the change point model (NUTS for continuous, Metropolis for tau)."""
    with build_model(returns):
        return pm.sample(
            draws=draws,
            tune=tune,
            chains=chains,
            random_seed=random_seed,
            progressbar=False,
        )


def tau_posterior_dates(idata: az.InferenceData, index: pd.DatetimeIndex) -> pd.Series:
    """Map posterior samples of tau (integer positions) to dates in the window."""
    samples = idata.posterior["tau"].values.ravel()
    return pd.Series(index[samples])


def summarize_change(idata: az.InferenceData, win: pd.DataFrame) -> dict:
    """Quantify the detected break: date estimate and before/after behaviour.

    Price impact uses the actual price level averaged on each side of the
    estimated break date; volatility is the posterior of sigma annualized.
    """
    post = idata.posterior
    tau_samples = post["tau"].values.ravel()
    tau_hat = int(np.median(tau_samples))
    lo, hi = np.percentile(tau_samples, [2.5, 97.5]).astype(int)

    change_date = win.index[tau_hat]
    price_before = float(win["Price"].iloc[:tau_hat].mean())
    price_after = float(win["Price"].iloc[tau_hat:].mean())

    sigma_1 = post["sigma_1"].values.ravel()
    sigma_2 = post["sigma_2"].values.ravel()
    ann = np.sqrt(252)

    return {
        "change_date": change_date.strftime("%Y-%m-%d"),
        "change_date_hdi_95": [
            win.index[lo].strftime("%Y-%m-%d"),
            win.index[hi].strftime("%Y-%m-%d"),
        ],
        "mean_price_before": round(price_before, 2),
        "mean_price_after": round(price_after, 2),
        "price_change_pct": round(100 * (price_after - price_before) / price_before, 1),
        "ann_vol_before": round(float(sigma_1.mean()) * ann, 3),
        "ann_vol_after": round(float(sigma_2.mean()) * ann, 3),
        "p_vol_increased": round(float((sigma_2 > sigma_1).mean()), 3),
        "max_rhat": round(float(az.summary(idata)["r_hat"].max()), 3),
    }


def nearest_events(
    events: pd.DataFrame, change_date: str, within_days: int = 45
) -> pd.DataFrame:
    """Events whose start date falls within ±within_days of the detected break."""
    delta = (events["event_date"] - pd.Timestamp(change_date)).dt.days.abs()
    return events.loc[delta <= within_days].assign(days_from_break=delta)
