# Change Point Analysis of Brent Oil Prices

Bayesian change point detection and statistical modeling of Brent oil prices
(May 1987 – Sep 2022), associating detected structural breaks with major
geopolitical events, OPEC decisions, sanctions, and economic shocks.

Built for **Birhan Energies** (10 Academy AIM Week 10 challenge) to support
investors, policymakers, and energy companies with data-driven insight into
how major events move the oil market.

## Objectives

1. Identify key events that significantly impacted Brent oil prices.
2. Quantify the effect of these events on price changes using Bayesian
   change point models (PyMC).
3. Communicate clear, data-driven insights via a report and an interactive
   dashboard (Flask + React).

## Project Structure

```
├── .github/workflows/unittests.yml   # CI: pytest on push/PR
├── .vscode/                          # Editor settings
├── data/
│   ├── events.csv                    # 16 researched key events (Task 1)
│   └── BrentOilPrices.csv            # Daily prices (download separately, gitignored)
├── notebooks/
│   └── 01_eda.ipynb                  # Data prep, EDA, stationarity analysis
├── src/
│   └── data_loader.py                # Loading / log-return helpers
├── scripts/                          # CLI utilities
├── tests/                            # Unit tests (events dataset validation)
├── reports/                          # Interim and final reports
└── requirements.txt
```

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Download `BrentOilPrices.csv` from the challenge's shared Drive folder into
`data/` (see `data/README.md`), then run the notebooks in order.

## Tests

```bash
pytest tests/ -v
```

## Analysis Workflow

1. **Data preparation** — parse dates, sort, compute log returns.
2. **EDA** — trend, volatility clustering, stationarity (ADF tests).
3. **Event research** — compile key oil-market events (`data/events.csv`).
4. **Bayesian change point modeling** — PyMC model with a discrete-uniform
   switch point `tau` and before/after parameters selected via
   `pm.math.switch`; MCMC sampling with convergence checks (r_hat, traces).
5. **Interpretation** — posterior of `tau` mapped to calendar dates,
   quantified before/after shifts, association with researched events.
6. **Dashboard** — Flask API serving prices, events, and change point
   results; React frontend with interactive event-highlight charts.

## Assumptions & Limitations

- A change point that coincides in time with a known event indicates a
  **statistical association, not proven causation** — markets may price in
  anticipated events early, and multiple events can overlap.
- Daily close prices limit resolution of intraday reactions.
- The core model detects shifts in the mean (and/or volatility) of returns;
  gradual regime transitions may be attributed to a single date.
