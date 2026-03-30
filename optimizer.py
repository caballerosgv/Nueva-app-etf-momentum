from __future__ import annotations

import itertools
import logging
from copy import deepcopy

import pandas as pd

from backtest import run_backtest
from config import AppConfig, DEFAULT_GRID

LOGGER = logging.getLogger(__name__)


def optimize_parameters(
    prices: pd.DataFrame,
    benchmark: pd.Series,
    atr_values: pd.DataFrame,
    regime_df: pd.DataFrame,
    cfg: AppConfig,
    grid: dict | None = None,
) -> tuple[AppConfig, pd.DataFrame]:
    grid = grid or DEFAULT_GRID
    keys = list(grid.keys())
    rows = []
    best_cfg = deepcopy(cfg)
    best_score = float("-inf")

    for values in itertools.product(*[grid[k] for k in keys]):
        params = dict(zip(keys, values))
        if params["w_m3"] + params["w_m6"] >= 1.0:
            continue

        trial = deepcopy(cfg)
        trial.momentum_weights["m3"] = params["w_m3"]
        trial.momentum_weights["m6"] = params["w_m6"]
        trial.momentum_weights["m12"] = 1 - params["w_m3"] - params["w_m6"]
        trial.vol_window = params["vol_window"]
        trial.atr_multiplier = params["atr_multiplier"]
        trial.ml_threshold = params["ml_threshold"]

        result = run_backtest(prices, benchmark, atr_values, regime_df, trial)
        sharpe = result.metrics.get("Sharpe", -99)
        cagr = result.metrics.get("CAGR", -99)
        score = 0.6 * sharpe + 0.4 * cagr

        row = {**params, "sharpe": sharpe, "cagr": cagr, "score": score}
        rows.append(row)

        if score > best_score:
            best_score = score
            best_cfg = trial

    leaderboard = pd.DataFrame(rows).sort_values("score", ascending=False)
    LOGGER.info("Optimization evaluated %d combinations", len(leaderboard))
    return best_cfg, leaderboard
