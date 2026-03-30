from __future__ import annotations

import pandas as pd


def adjusted_momentum_score(
    mom3: pd.Series,
    mom6: pd.Series,
    mom12: pd.Series,
    volatility: pd.Series,
    w3: float,
    w6: float,
    w12: float,
) -> pd.Series:
    raw = (w3 * mom3) + (w6 * mom6) + (w12 * mom12)
    return raw / volatility.replace(0, pd.NA)


def rank_assets(scores: pd.Series, top_n: int = 2) -> list[str]:
    scores = scores.dropna().sort_values(ascending=False)
    return list(scores.head(top_n).index)
