from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Tuple


@dataclass
class AppConfig:
    etfs: List[str] = field(
        default_factory=lambda: ["XDEM.DE", "EQQQ.L", "IWDA.AS", "IUIT.L", "SGLD.L", "IEGA.L"]
    )
    benchmark: str = "^GSPC"
    defensive_assets: Tuple[str, str] = ("SGLD.L", "IEGA.L")
    start_date: str = "2005-01-01"
    end_date: str | None = None

    momentum_windows: Dict[str, int] = field(default_factory=lambda: {"m3": 63, "m6": 126, "m12": 252})
    momentum_weights: Dict[str, float] = field(default_factory=lambda: {"m3": 0.3, "m6": 0.3, "m12": 0.4})
    vol_window: int = 20
    atr_window: int = 14
    atr_multiplier: float = 2.0

    top_n: int = 2
    base_allocations: Tuple[float, float] = (0.6, 0.4)
    max_weight_per_asset: float = 0.6

    ma_filter_window: int = 200
    ml_threshold: float = 0.6
    rolling_train_months: int = 60

    rebalance_freq: str = "M"
    initial_capital: float = 100_000.0
    risk_free_rate: float = 0.01

    output_dir: Path = Path("outputs")
    log_level: str = "INFO"


DEFAULT_GRID = {
    "w_m3": [0.2, 0.3, 0.4],
    "w_m6": [0.2, 0.3, 0.4],
    "vol_window": [20, 40, 60],
    "atr_multiplier": [1.5, 2.0, 2.5],
    "ml_threshold": [0.55, 0.6, 0.65],
}
