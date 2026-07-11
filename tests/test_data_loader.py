"""Tests for data loading error handling and parsing."""

import pandas as pd
import pytest

from src.data_loader import add_log_returns, load_events, load_prices


def test_load_prices_missing_file(tmp_path):
    with pytest.raises(FileNotFoundError, match="data/README.md"):
        load_prices(tmp_path / "nope.csv")


def test_load_prices_missing_columns(tmp_path):
    p = tmp_path / "bad.csv"
    p.write_text("Date,Close\n20-May-87,18.63\n")
    with pytest.raises(ValueError, match="Price"):
        load_prices(p)


def test_load_prices_rejects_nonpositive(tmp_path):
    p = tmp_path / "neg.csv"
    p.write_text("Date,Price\n20-May-87,18.63\n21-May-87,-1.0\n")
    with pytest.raises(ValueError, match="non-positive"):
        load_prices(p)


def test_load_prices_parses_mixed_date_formats(tmp_path):
    p = tmp_path / "ok.csv"
    p.write_text('Date,Price\n20-May-87,18.63\n"Apr 22, 2020",20.37\n')
    df = load_prices(p)
    assert list(df.index) == [pd.Timestamp("1987-05-20"), pd.Timestamp("2020-04-22")]
    assert df["Price"].tolist() == [18.63, 20.37]


def test_add_log_returns_first_row_nan(tmp_path):
    p = tmp_path / "ok.csv"
    p.write_text("Date,Price\n20-May-87,10.0\n21-May-87,20.0\n")
    df = add_log_returns(load_prices(p))
    assert pd.isna(df["LogReturn"].iloc[0])
    assert df["LogReturn"].iloc[1] == pytest.approx(0.6931, abs=1e-4)


def test_load_events_missing_file(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_events(tmp_path / "nope.csv")


def test_load_events_missing_columns(tmp_path):
    p = tmp_path / "bad.csv"
    p.write_text("event_date,event_name\n2020-03-06,OPEC+ collapse\n")
    with pytest.raises(ValueError, match="category"):
        load_events(p)
