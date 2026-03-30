from __future__ import annotations

import logging
from typing import Iterable

import pandas as pd
import yfinance as yf

LOGGER = logging.getLogger(__name__)


def _download(symbols: Iterable[str], start: str, end: str | None = None) -> pd.DataFrame:
    tickers = list(dict.fromkeys(symbols))
    df = yf.download(tickers=tickers, start=start, end=end, auto_adjust=True, progress=False)
    if df.empty:
        raise ValueError("No price data downloaded. Check tickers or date range.")
    return df


def download_prices(symbols: Iterable[str], start: str, end: str | None = None) -> pd.DataFrame:
    tickers = list(dict.fromkeys(symbols))
    LOGGER.info("Downloading close prices for %s", tickers)
    df = _download(tickers, start, end)

    if isinstance(df.columns, pd.MultiIndex):
        close = df["Close"].copy()
    else:
        close = df[["Close"]].rename(columns={"Close": tickers[0]})

    close = close.dropna(how="all").ffill().dropna(how="all")
    missing = [c for c in tickers if c not in close.columns]
    if missing:
        LOGGER.warning("Missing symbols in downloaded data: %s", missing)

    return close


def download_ohlc(symbols: Iterable[str], start: str, end: str | None = None) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    tickers = list(dict.fromkeys(symbols))
    LOGGER.info("Downloading OHLC data for %s", tickers)
    df = _download(tickers, start, end)
    if not isinstance(df.columns, pd.MultiIndex):
        raise ValueError("Expected multi-ticker OHLC data.")

    high = df["High"].dropna(how="all").ffill()
    low = df["Low"].dropna(how="all").ffill()
    close = df["Close"].dropna(how="all").ffill()
    return high, low, close


def monthly_rebalance_dates(index: pd.DatetimeIndex, freq: str = "M") -> pd.DatetimeIndex:
    return pd.Series(index=index, dtype=float).resample(freq).last().dropna().index
