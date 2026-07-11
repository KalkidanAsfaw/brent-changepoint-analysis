"""Validate the researched events dataset required by Task 1."""

from pathlib import Path

import pandas as pd

EVENTS_CSV = Path(__file__).resolve().parent.parent / "data" / "events.csv"


def load_events():
    return pd.read_csv(EVENTS_CSV, parse_dates=["event_date"])


def test_has_required_columns():
    df = load_events()
    assert {"event_date", "event_name", "category", "description"} <= set(df.columns)


def test_has_at_least_10_events():
    assert len(load_events()) >= 10


def test_dates_parse_and_fall_within_price_data_range():
    df = load_events()
    assert df["event_date"].notna().all()
    assert df["event_date"].min() >= pd.Timestamp("1987-05-20")
    assert df["event_date"].max() <= pd.Timestamp("2022-09-30")


def test_no_duplicate_events():
    df = load_events()
    assert not df.duplicated(subset=["event_date", "event_name"]).any()


def test_categories_are_from_known_set():
    df = load_events()
    allowed = {"Conflict", "Economic", "OPEC", "Sanctions", "Geopolitical"}
    assert set(df["category"].unique()) <= allowed
