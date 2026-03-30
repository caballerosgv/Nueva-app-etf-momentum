from __future__ import annotations

import numpy as np
import pandas as pd


def compute_returns(prices: pd.DataFrame) -> pd.DataFrame:
    return prices.pct_change().replace([np.inf, -np.inf], np.nan)


def compute_momentum_features(prices: pd.DataFrame, windows: dict[str, int]) -> dict[str, pd.DataFrame]:
    return {name: prices.pct_change(window) for name, window in windows.items()}


def rolling_volatility(returns: pd.DataFrame, window: int) -> pd.DataFrame:
    return returns.rolling(window).std()


def compute_rsi(prices: pd.DataFrame, window: int = 14) -> pd.DataFrame:
    delta = prices.diff()
    up = delta.clip(lower=0)
    down = -delta.clip(upper=0)
    avg_gain = up.rolling(window).mean()
    avg_loss = down.rolling(window).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    return 100 - (100 / (1 + rs))


def drawdown_series(prices: pd.DataFrame, window: int = 126) -> pd.DataFrame:
    rolling_max = prices.rolling(window).max()
    return prices / rolling_max - 1


def moving_average(prices: pd.Series, window: int) -> pd.Series:
    return prices.rolling(window).mean()


def moving_average_slope(ma: pd.Series, window: int = 20) -> pd.Series:
    return ma.diff(window) / window


def atr(high: pd.DataFrame, low: pd.DataFrame, close: pd.DataFrame, window: int = 14) -> pd.DataFrame:
    prev_close = close.shift(1)
    tr_1 = high - low
    tr_2 = (high - prev_close).abs()
    tr_3 = (low - prev_close).abs()
    tr = pd.concat([tr_1, tr_2, tr_3], axis=0).groupby(level=0).max()
    return tr.rolling(window).mean()
