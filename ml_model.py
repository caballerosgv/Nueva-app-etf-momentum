from __future__ import annotations

import logging

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier

LOGGER = logging.getLogger(__name__)


FEATURE_COLUMNS = [
    "mom3",
    "mom6",
    "mom12",
    "vol20",
    "vol60",
    "rsi14",
    "drawdown126",
    "spx_above_ma200",
    "ma_slope20",
]


def build_regime_dataset(feature_frame: pd.DataFrame, benchmark_returns: pd.Series) -> pd.DataFrame:
    ds = feature_frame.copy()
    ds["target"] = (benchmark_returns.shift(-21) > 0).astype(int)
    ds = ds.dropna(subset=FEATURE_COLUMNS + ["target"])
    return ds


def rolling_regime_probabilities(
    dataset: pd.DataFrame,
    rebalance_dates: pd.DatetimeIndex,
    threshold: float,
    train_months: int,
) -> pd.DataFrame:
    rows = []
    model = RandomForestClassifier(
        n_estimators=300,
        max_depth=5,
        random_state=42,
        class_weight="balanced_subsample",
    )

    for dt in rebalance_dates:
        train_end = dataset.index.get_indexer([dt], method="ffill")[0]
        if train_end <= 0:
            continue
        train_slice = dataset.iloc[:train_end]
        min_obs = max(252, train_months * 21)
        if len(train_slice) < min_obs:
            continue

        x_train = train_slice[FEATURE_COLUMNS]
        y_train = train_slice["target"]
        if y_train.nunique() < 2:
            continue

        model.fit(x_train, y_train)

        test_loc = dataset.index.get_indexer([dt], method="ffill")[0]
        x_test = dataset.iloc[[test_loc]][FEATURE_COLUMNS]
        prob = float(model.predict_proba(x_test)[0, 1])
        regime = int(prob > threshold)
        rows.append({"date": dt, "ml_prob": prob, "regime": regime})

    out = pd.DataFrame(rows).set_index("date") if rows else pd.DataFrame(columns=["ml_prob", "regime"])
    LOGGER.info("ML predictions generated for %d rebalance dates", len(out))
    return out
