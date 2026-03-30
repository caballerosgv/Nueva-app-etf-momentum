from __future__ import annotations

import pandas as pd
import streamlit as st


def run_dashboard(output_dir: str = "outputs") -> None:
    st.set_page_config(page_title="ETF Momentum IA", layout="wide")
    st.title("Dashboard ETF Momentum + IA")

    leaderboard = pd.read_csv(f"{output_dir}/optimizer_leaderboard.csv")
    metrics = pd.read_csv(f"{output_dir}/metrics.csv")
    equity = pd.read_csv(f"{output_dir}/equity_curve.csv", parse_dates=["date"]).set_index("date")
    weights = pd.read_csv(f"{output_dir}/weights.csv", parse_dates=["date"]).set_index("date")
    regime = pd.read_csv(f"{output_dir}/regime.csv", parse_dates=["date"]).set_index("date")

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
    run_dashboard()
