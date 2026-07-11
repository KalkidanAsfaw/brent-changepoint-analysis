"""Loading and preparation helpers for the Brent oil price analysis."""

from pathlib import Path

import numpy as np
import pandas as pd

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
PRICES_CSV = DATA_DIR / "BrentOilPrices.csv"
EVENTS_CSV = DATA_DIR / "events.csv"


def load_prices(path: Path = PRICES_CSV) -> pd.DataFrame:
    """Load daily Brent prices with a parsed DatetimeIndex, sorted ascending.

    The source file mixes date styles (e.g. '20-May-87' and 'Apr 22, 2020'),
    so parsing falls back to pandas' flexible parser per-element.
    """
    df = pd.read_csv(path)
    df["Date"] = pd.to_datetime(df["Date"], format="mixed", dayfirst=True)
    df = df.sort_values("Date").set_index("Date")
    df["Price"] = pd.to_numeric(df["Price"])
    return df


def add_log_returns(df: pd.DataFrame) -> pd.DataFrame:
    """Append a LogReturn column: log(price_t) - log(price_{t-1})."""
    out = df.copy()
    out["LogReturn"] = np.log(out["Price"]).diff()
    return out


def load_events(path: Path = EVENTS_CSV) -> pd.DataFrame:
    """Load the researched key-events dataset with parsed dates."""
    df = pd.read_csv(path, parse_dates=["event_date"])
    return df.sort_values("event_date").reset_index(drop=True)
