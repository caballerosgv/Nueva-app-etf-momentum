from __future__ import annotations

import numpy as np
import pandas as pd


def inverse_vol_weights(vols: pd.Series) -> pd.Series:
    inv = 1 / vols.replace(0, np.nan)
    w = inv / inv.sum()
    return w.fillna(0)


def apply_max_weight(weights: pd.Series, max_weight: float) -> pd.Series:
    clipped = weights.clip(upper=max_weight)
    remainder = 1 - clipped.sum()
    if remainder > 0:
        below_cap = clipped[clipped < max_weight]
        if not below_cap.empty:
            clipped.loc[below_cap.index] += remainder * (below_cap / below_cap.sum())
    return clipped / clipped.sum() if clipped.sum() > 0 else clipped


def market_filter(spx_price: float, spx_ma200: float) -> bool:
    return spx_price >= spx_ma200


def apply_dynamic_stop(entry_price: float, current_price: float, atr_value: float, atr_mult: float) -> bool:
    stop = entry_price - atr_mult * atr_value
    return current_price <= stop
