# Planned Analysis Workflow — Brent Oil Price Change Point Study

**Birhan Energies · 10 Academy AIM Week 10 · Task 1**

## 1. Purpose

Birhan Energies advises stakeholders who each depend on understanding how
major geopolitical and economic events move the Brent oil market: **investors**
need it to manage risk and time portfolio decisions in a violently volatile
asset; **policymakers** need it to design strategies for economic stability
and energy security; and **energy companies** need it to forecast prices for
operational planning, cost control, and supply-chain security.

The project pursues three objectives:

1. **Identify** key events that have significantly impacted Brent oil prices,
   by detecting structural breaks in the daily price series
   (May 1987 – Nov 2022) with a Bayesian change point model built in PyMC.
2. **Quantify** how much these events affected prices, using the model's
   posterior distributions to state before/after shifts in mean price and
   volatility with explicit uncertainty.
3. **Deliver** clear, data-driven insights to guide investment strategy,
   policy development, and operational planning — via a final report and an
   interactive Flask + React dashboard.

A foundational assumption throughout: a detected break that coincides with an
event is a statistical association in time, **not proof of causal impact**
(see §5).

## 2. Data

- **Prices:** `data/BrentOilPrices.csv` — 9,011 daily observations of Brent
  crude in USD/bbl, 20 May 1987 to 14 Nov 2022. Dates arrive in two formats
  (`20-May-87` and `"Apr 22, 2020"`); the loader parses both, sorts, and
  indexes by date. Weekends and market holidays are absent by construction.
- **Events:** `data/events.csv` — 16 researched key events (conflicts, OPEC
  decisions, sanctions, economic shocks) with start dates, categories, and
  descriptions. Compiled from public reporting on the oil market; dates are
  the approximate start of each event. This file is unit-tested in CI for
  schema, parseability, and minimum coverage.

## 3. Analysis steps, from data loading to insight generation

1. **Load & prepare** — parse mixed date formats, sort chronologically, set a
   `DatetimeIndex`, compute daily log returns
   `r_t = log(P_t) − log(P_{t−1})` (`src/data_loader.py`).
2. **Exploratory analysis** (`notebooks/01_eda.ipynb`) — raw price series with
   event overlay; log-scale trend view with rolling annual mean; log returns
   and 30-day rolling volatility; return distribution (tail behaviour); ADF
   stationarity tests on the price level and on returns.
3. **Event research** — compile and validate the structured events dataset
   (see §2).
4. **Bayesian change point modeling** (`src/change_point_model.py`,
   `notebooks/02_change_point_model.ipynb`) — discrete-uniform prior on the
   switch point τ; separate "before" and "after" parameters joined by
   `pm.math.switch`; Normal likelihood; NUTS/Metropolis sampling via
   `pm.sample()`. The base model shifts the **mean of log returns**; the
   implemented extension also shifts the **volatility**, which for oil is
   often the stronger and better-identified signal. Because a single change
   point over 35 years is too coarse, the model is applied to focused windows
   around candidate break periods (e.g., 2008 crash, 2014–15 OPEC price war,
   2020 COVID collapse, 2022 invasion).
5. **Diagnostics** — convergence via `r_hat ≈ 1`, effective sample size, and
   trace plots; posterior of τ inspected for sharpness (a narrow peak = a
   confidently located break).
6. **Association & quantification** — compare the posterior distribution of
   each break date against the events list; report shifts quantitatively
   ("mean daily price moved from $X to $Y, a Z% change") with probabilistic
   statements from the posteriors.
7. **Communication** — final blog-style report plus an interactive dashboard
   (Flask API serving prices, change points, and event correlations to a
   React frontend with date filters and event highlighting).

## 4. What a change point model gives us — and what it doesn't

A Bayesian change point model treats the date of a structural break, τ, as an
unknown parameter with a prior over all days in the window, and lets the data
before and after τ be governed by different parameters. Its outputs are:

- a **posterior distribution over the break date** (not a single point — the
  width expresses dating uncertainty);
- **posterior distributions of the before/after parameters** (mean return,
  volatility), from which impact statements follow, e.g. "the probability
  that volatility rose after τ exceeds 99%";
- convergence diagnostics that tell us whether these posteriors are reliable.

Limitations: the simple model finds **one** break per window (multiple breaks
require windowing or a multiple-change point extension); it locates breaks in
time but says nothing about *why* they happened; and gradual transitions are
approximated by an abrupt switch.

## 5. Assumptions and limitations

- **Correlation is not causation.** The core inferential caveat: a change
  point that coincides with an event is a *temporal association*, not proof
  that the event caused the shift. Markets anticipate events (prices may move
  before the headline date), multiple events overlap (e.g., sanctions during a
  demand shock), and unobserved confounders (inventories, the dollar, macro
  cycles) move prices continuously. Impact statements are therefore framed
  as *hypotheses supported by timing evidence*, not causal claims. Establishing
  causality would need explicit causal designs (natural experiments,
  counterfactual/synthetic-control methods) and richer covariates.
- **Event dates are approximate.** Many "events" unfold over weeks (OPEC
  negotiation cycles, escalating conflicts); we use the most defensible start
  date and compare against the *posterior distribution* of τ rather than exact
  day matches.
- **Model simplifications.** Abrupt single switch per window; Normal
  likelihood despite heavy tails (EDA measured excess kurtosis ≈ 66 — a
  Student-t likelihood is the natural robustness extension); business-day
  gaps treated as consecutive observations.
- **Data limitations.** A single price series with no volume, inventory, or
  macro covariates; the events list (16 items) is curated, not exhaustive, and
  its selection is itself a judgment call.
- **Scope.** Findings describe *this* historical sample; regime behaviour
  (e.g., the shale era) changes the market's response to similar events over
  time, so extrapolation to future events is qualified.
