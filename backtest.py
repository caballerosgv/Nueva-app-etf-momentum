from __future__ import annotations

import logging
from dataclasses import dataclass

import numpy as np
import pandas as pd

from config import AppConfig
from data import monthly_rebalance_dates
from features import compute_momentum_features, compute_returns, moving_average
from portfolio import risk_adjusted_weights
from risk import apply_dynamic_stop, market_filter
from signals import adjusted_momentum_score, rank_assets

LOGGER = logging.getLogger(__name__)


@dataclass
class BacktestResult:
    equity_curve: pd.Series
    weights: pd.DataFrame
    trades: pd.DataFrame
    metrics: dict[str, float]
    benchmark_curve: pd.Series
    regime: pd.DataFrame


def performance_metrics(equity: pd.Series, benchmark: pd.Series, risk_free_rate: float = 0.01) -> dict[str, float]:
    returns = equity.pct_change().dropna()
    if returns.empty:
        return {}
    years = (equity.index[-1] - equity.index[0]).days / 365.25
    cagr = (equity.iloc[-1] / equity.iloc[0]) ** (1 / years) - 1 if years > 0 else np.nan
    running_max = equity.cummax()
    dd = equity / running_max - 1
    max_dd = dd.min()
    vol = returns.std() * np.sqrt(252)
    excess = returns.mean() * 252 - risk_free_rate
    sharpe = excess / vol if vol > 0 else np.nan
    downside = returns[returns < 0].std() * np.sqrt(252)
    sortino = excess / downside if downside and downside > 0 else np.nan

    return {
        "CAGR": cagr,
        "Max Drawdown": max_dd,
        "Sharpe": sharpe,
        "Volatility": vol,
        "Sortino": sortino,
        "Total Return": equity.iloc[-1] / equity.iloc[0] - 1,
        "Benchmark Return": benchmark.iloc[-1] / benchmark.iloc[0] - 1,
    }


def run_backtest(
    prices: pd.DataFrame,
    benchmark_prices: pd.Series,
    atr_values: pd.DataFrame,
    regime_df: pd.DataFrame,
    cfg: AppConfig,
) -> BacktestResult:
    returns = compute_returns(prices)
    mom = compute_momentum_features(prices, cfg.momentum_windows)
    vol = returns.rolling(cfg.vol_window).std()
    spx_ma = moving_average(benchmark_prices, cfg.ma_filter_window)

    rebalance_dates = monthly_rebalance_dates(prices.index, cfg.rebalance_freq)

    portfolio_value = cfg.initial_capital
    equity = []
    trade_log = []
    weights_hist = []

    current_weights = pd.Series(0.0, index=prices.columns)
    entry_prices = pd.Series(np.nan, index=prices.columns)

    for i in range(1, len(prices.index)):
        dt = prices.index[i]
        prev = prices.index[i - 1]

        # Mark-to-market
        day_ret = returns.loc[dt].fillna(0)
        portfolio_value *= 1 + float((current_weights * day_ret).sum())
        equity.append((dt, portfolio_value))

        # Check dynamic stops
        for asset in current_weights[current_weights > 0].index:
            atr_v = atr_values.at[dt, asset] if asset in atr_values.columns and dt in atr_values.index else np.nan
            if np.isnan(atr_v) or np.isnan(entry_prices[asset]):
                continue
            if apply_dynamic_stop(float(entry_prices[asset]), float(prices.at[dt, asset]), float(atr_v), cfg.atr_multiplier):
                current_weights[asset] = 0
        if current_weights.sum() > 0:
            current_weights /= current_weights.sum()

        if dt not in rebalance_dates:
            continue

        regime = 0
        if dt in regime_df.index:
            regime = int(regime_df.at[dt, "regime"])

        risk_on = market_filter(float(benchmark_prices.asof(dt)), float(spx_ma.asof(dt))) and regime == 1

        if risk_on:
            scores = adjusted_momentum_score(
                mom["m3"].loc[prev],
                mom["m6"].loc[prev],
                mom["m12"].loc[prev],
                vol.loc[prev],
                cfg.momentum_weights["m3"],
                cfg.momentum_weights["m6"],
                cfg.momentum_weights["m12"],
            )
            selected = rank_assets(scores, cfg.top_n)
            next_weights = risk_adjusted_weights(
                selected,
                vol.loc[prev],
                cfg.base_allocations,
                cfg.max_weight_per_asset,
            )
        else:
            next_weights = pd.Series(0.5, index=list(cfg.defensive_assets))

        full_weights = pd.Series(0.0, index=prices.columns)
        full_weights.update(next_weights)
        full_weights = full_weights / full_weights.sum()

        changed = (full_weights - current_weights).abs().sum()
        if changed > 0.05:
            trade_log.append(
                {
                    "date": dt,
                    "risk_on": risk_on,
                    "weights": full_weights[full_weights > 0].to_dict(),
                    "portfolio_value": portfolio_value,
                }
            )
            for asset in full_weights[full_weights > 0].index:
                entry_prices[asset] = prices.at[dt, asset]

        current_weights = full_weights
        weights_hist.append((dt, *[current_weights[c] for c in prices.columns]))

    equity_curve = pd.Series(dict(equity)).sort_index()
    benchmark_curve = (benchmark_prices / benchmark_prices.dropna().iloc[0]) * cfg.initial_capital
    benchmark_curve = benchmark_curve.reindex(equity_curve.index).ffill()

    weights_df = pd.DataFrame(weights_hist, columns=["date", *prices.columns]).set_index("date") if weights_hist else pd.DataFrame()
    trades_df = pd.DataFrame(trade_log)
    metrics = performance_metrics(equity_curve, benchmark_curve, cfg.risk_free_rate)

    return BacktestResult(
        equity_curve=equity_curve,
        weights=weights_df,
        trades=trades_df,
        metrics=metrics,
        benchmark_curve=benchmark_curve,
        regime=regime_df,
    )
