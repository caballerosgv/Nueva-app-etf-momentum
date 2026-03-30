from __future__ import annotations

import pandas as pd

from risk import apply_max_weight, inverse_vol_weights


def base_weights(selected_assets: list[str], base_allocations: tuple[float, float]) -> pd.Series:
    if not selected_assets:
        return pd.Series(dtype=float)
    alloc = list(base_allocations[: len(selected_assets)])
    if len(alloc) < len(selected_assets):
        remaining = 1 - sum(alloc)
        alloc.extend([remaining / (len(selected_assets) - len(alloc))] * (len(selected_assets) - len(alloc)))
    return pd.Series(alloc, index=selected_assets, dtype=float)


def risk_adjusted_weights(
    selected_assets: list[str],
    vols: pd.Series,
    base_allocations: tuple[float, float],
    max_weight_per_asset: float,
) -> pd.Series:
    base = base_weights(selected_assets, base_allocations)
    if base.empty:
        return base

    inv_vol = inverse_vol_weights(vols.reindex(selected_assets))
    combined = (0.5 * base + 0.5 * inv_vol).fillna(0)
    combined = combined / combined.sum() if combined.sum() > 0 else combined
    return apply_max_weight(combined, max_weight_per_asset)
