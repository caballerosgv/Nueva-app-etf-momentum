from __future__ import annotations

import json
import logging
import os

import pandas as pd
import requests

LOGGER = logging.getLogger(__name__)


def build_signal_message(weights: pd.Series, regime_prob: float, risk_on: bool) -> str:
    risk_level = "ALTO" if risk_on else "DEFENSIVO"
    w_dict = {k: round(float(v) * 100, 2) for k, v in weights[weights > 0].items()}
    payload = {
        "estado_mercado": "FAVORABLE" if risk_on else "DESFAVORABLE",
        "probabilidad_ml": round(regime_prob, 4),
        "pesos": w_dict,
        "nivel_riesgo": risk_level,
    }
    return "📊 Señal mensual ETF Momentum\n" + json.dumps(payload, ensure_ascii=False, indent=2)


def send_telegram(message: str, token: str | None = None, chat_id: str | None = None) -> bool:
    token = token or os.getenv("TELEGRAM_BOT_TOKEN")
    chat_id = chat_id or os.getenv("TELEGRAM_CHAT_ID")

    if not token or not chat_id:
        LOGGER.warning("Telegram not configured; skipping notification")
        return False

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {"chat_id": chat_id, "text": message}
    response = requests.post(url, json=payload, timeout=10)
    response.raise_for_status()
    return True
