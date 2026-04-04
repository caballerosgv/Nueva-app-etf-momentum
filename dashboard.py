from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd
import streamlit as st


REQUIRED_OUTPUTS = [
    "optimizer_leaderboard.csv",
    "metrics.csv",
    "equity_curve.csv",
    "weights.csv",
    "regime.csv",
]


def _resolve_output_dir(output_dir: str) -> Path:
    candidates = [Path(output_dir), Path(__file__).resolve().parent / output_dir]
    for candidate in candidates:
        if candidate.exists() and candidate.is_dir():
            return candidate
    return candidates[-1]


def run_dashboard(output_dir: str = "outputs") -> None:
    st.set_page_config(page_title="ETF Momentum IA", layout="wide")
    st.title("Dashboard ETF Momentum + IA")

    output_path = _resolve_output_dir(output_dir)
    missing_files = [name for name in REQUIRED_OUTPUTS if not (output_path / name).exists()]

    if missing_files:
        st.error(
            "No se encontraron todos los archivos necesarios en "
            f"'{output_path}'. Ejecuta primero 'python .\\main.py' desde PowerShell para generar outputs/."
        )
        st.caption("Archivos faltantes: " + ", ".join(missing_files))
        st.caption(
            "Si tus archivos están en otra ruta, inicia el dashboard con: "
            "`streamlit run dashboard.py -- --output-dir \"C:\\ruta\\a\\outputs\"`."
        )
        st.stop()

    leaderboard = pd.read_csv(output_path / "optimizer_leaderboard.csv")
    metrics = pd.read_csv(output_path / "metrics.csv")
    equity = pd.read_csv(output_path / "equity_curve.csv", parse_dates=["date"]).set_index("date")
    weights = pd.read_csv(output_path / "weights.csv", parse_dates=["date"]).set_index("date")
    regime = pd.read_csv(output_path / "regime.csv", parse_dates=["date"]).set_index("date")

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Ranking Optimización")
        st.dataframe(leaderboard.head(15), use_container_width=True)

    with col2:
        st.subheader("Métricas")
        st.dataframe(metrics, use_container_width=True)

    st.subheader("Curva Equity vs Benchmark")
    st.line_chart(equity[["strategy", "benchmark"]])

    st.subheader("Drawdown")
    drawdown = equity["strategy"] / equity["strategy"].cummax() - 1
    st.area_chart(drawdown)

    st.subheader("Pesos actuales")
    st.bar_chart(weights.tail(1).T)

    st.subheader("Estado IA")
    st.line_chart(regime[["ml_prob"]])


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Dashboard ETF Momentum + IA")
    parser.add_argument("--output-dir", default="outputs", help="Ruta a la carpeta de outputs")
    args = parser.parse_args()
    run_dashboard(output_dir=args.output_dir)
