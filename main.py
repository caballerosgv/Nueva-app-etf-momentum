from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd
from backtest import run_backtest
from config import AppConfig
from data import download_ohlc, download_prices, monthly_rebalance_dates
from execution import build_signal_message, send_telegram
from features import (
    atr,
    compute_momentum_features,
    compute_returns,
    compute_rsi,
    drawdown_series,
    moving_average,
    moving_average_slope,
)
from ml_model import build_regime_dataset, rolling_regime_probabilities
from optimizer import optimize_parameters


def setup_logging(level: str) -> None:
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )


def prepare_ml_features(prices: pd.DataFrame, benchmark_prices: pd.Series, cfg: AppConfig) -> pd.DataFrame:
    rets = compute_returns(prices)
    mom = compute_momentum_features(prices, cfg.momentum_windows)
    mean_mom = pd.concat(mom.values(), axis=1).groupby(level=0, axis=1).mean()

    feature_frame = pd.DataFrame(index=prices.index)
    feature_frame["mom3"] = mean_mom.iloc[:, 0]
    feature_frame["mom6"] = mean_mom.iloc[:, 1]
    feature_frame["mom12"] = mean_mom.iloc[:, 2]
    feature_frame["vol20"] = rets.mean(axis=1).rolling(20).std()
    feature_frame["vol60"] = rets.mean(axis=1).rolling(60).std()
    feature_frame["rsi14"] = compute_rsi(prices).mean(axis=1)
    feature_frame["drawdown126"] = drawdown_series(prices, 126).mean(axis=1)

    spx_ma = moving_average(benchmark_prices, cfg.ma_filter_window)
    feature_frame["spx_above_ma200"] = (benchmark_prices > spx_ma).astype(int)
    feature_frame["ma_slope20"] = moving_average_slope(spx_ma, 20)

    benchmark_returns = benchmark_prices.pct_change()
    return build_regime_dataset(feature_frame, benchmark_returns)


def export_outputs(result, leaderboard: pd.DataFrame, cfg: AppConfig) -> None:
    cfg.output_dir.mkdir(exist_ok=True, parents=True)

    equity_df = pd.DataFrame({"strategy": result.equity_curve, "benchmark": result.benchmark_curve})
    equity_df.index.name = "date"
    equity_df.to_csv(cfg.output_dir / "equity_curve.csv")

    pd.DataFrame([result.metrics]).to_csv(cfg.output_dir / "metrics.csv", index=False)
    result.weights.to_csv(cfg.output_dir / "weights.csv", index_label="date")
    result.trades.to_csv(cfg.output_dir / "trades.csv", index=False)
    result.regime.to_csv(cfg.output_dir / "regime.csv", index_label="date")
    leaderboard.to_csv(cfg.output_dir / "optimizer_leaderboard.csv", index=False)


def main(send_notifications: bool = False) -> None:
    cfg = AppConfig()
    setup_logging(cfg.log_level)

    symbols = cfg.etfs + [cfg.benchmark]
    close_prices = download_prices(symbols, cfg.start_date, cfg.end_date)

    etf_prices = close_prices[cfg.etfs].dropna(how="all")
    benchmark_prices = close_prices[cfg.benchmark].dropna()

    high, low, close = download_ohlc(cfg.etfs, cfg.start_date, cfg.end_date)
    atr_values = atr(high[etf_prices.columns], low[etf_prices.columns], close[etf_prices.columns], cfg.atr_window)

    ml_dataset = prepare_ml_features(etf_prices, benchmark_prices, cfg)
    rebalance_dates = monthly_rebalance_dates(etf_prices.index, cfg.rebalance_freq)
    regime_df = rolling_regime_probabilities(ml_dataset, rebalance_dates, cfg.ml_threshold, cfg.rolling_train_months)

    best_cfg, leaderboard = optimize_parameters(etf_prices, benchmark_prices, atr_values, regime_df, cfg)

    final_result = run_backtest(etf_prices, benchmark_prices, atr_values, regime_df, best_cfg)
    export_outputs(final_result, leaderboard, best_cfg)

    last_date = final_result.weights.index.max()
    last_weights = final_result.weights.loc[last_date]
    last_prob = float(final_result.regime["ml_prob"].asof(last_date)) if not final_result.regime.empty else 0.0
    risk_on = bool(final_result.regime["regime"].asof(last_date)) if not final_result.regime.empty else False
    msg = build_signal_message(last_weights, last_prob, risk_on)

    if send_notifications:
        send_telegram(msg)

    print("=== Metrics ===")
    for k, v in final_result.metrics.items():
        print(f"{k}: {v:.4f}")
    print("\n=== Example Monthly Signal ===")
    print(msg)


if __name__ == "__main__":
    main(send_notifications=False)
