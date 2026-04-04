# Sistema Cuantitativo ETF Momentum + IA (Nivel Institucional)

Este repositorio implementa un **pipeline completo de trading sistemático** para ETFs, con:

- Backtest histórico multi-año (desde 2005 o máximo disponible).
- Optimización automática por grid-search.
- Clasificación de régimen de mercado con ML (RandomForest rolling).
- Gestión de riesgo institucional (filtro de mercado, control de volatilidad, ATR stop, límites de exposición).
- Señales mensuales listas para notificación por Telegram.
- Dashboard Streamlit para monitoreo operativo.

## Universo

- ETFs: `XDEM.DE`, `EQQQ.L`, `IWDA.AS`, `IUIT.L`, `SGLD.L`, `IEGA.L`
- Benchmark y filtro macro: `^GSPC`

## Arquitectura

- `config.py`: configuración centralizada.
- `data.py`: descarga de series (close + OHLC) y calendario de rebalanceo.
- `features.py`: features cuantitativas (momentum, volatilidad, RSI, drawdown, ATR, slope MA).
- `signals.py`: score momentum ajustado por volatilidad + ranking.
- `ml_model.py`: dataset de régimen y entrenamiento rolling (walk-forward).
- `risk.py`: utilidades de control de riesgo.
- `portfolio.py`: asignación base + ajuste por volatilidad inversa.
- `backtest.py`: simulador mensual con stops dinámicos y métricas.
- `optimizer.py`: optimización de pesos/umbrales/ATR/ventana de vol.
- `execution.py`: mensajería de señal y envío por Telegram.
- `dashboard.py`: tablero Streamlit.
- `main.py`: orquestador extremo a extremo.
- `scripts/run_monthly.sh`: script para cron/VPS.

## Lógica de estrategia

### 1) Momentum multi-horizonte

- Ventanas: 3M (63), 6M (126), 12M (252).
- Score:
  `Score = w3*M3 + w6*M6 + w12*M12`
- Ajuste:
  `Adjusted Score = Score / Volatilidad(20d)`
- Selección: top 2 activos.
- Base: 60/40 (se mezcla con weighting inverso a volatilidad).

### 2) Filtro de mercado y modo defensivo

- Si S&P500 `< MA200` o ML detecta régimen desfavorable:
  - 50% `SGLD.L`
  - 50% `IEGA.L`

### 3) ML de régimen (no predicción de precios)

- Clasifica `1=favorable`, `0=desfavorable`.
- Features usadas:
  - momentum 3/6/12M
  - vol 20d y 60d
  - RSI(14)
  - drawdown 126d
  - S&P500 sobre MA200
  - pendiente MA(200)
- Modelo: `RandomForestClassifier`.
- Entrenamiento rolling walk-forward para evitar leakage.
- Lógica:
  - `prob > threshold` => risk-on momentum.
  - otro caso => defensivo.

### 4) Gestión de riesgo avanzada

- Volatility-control vía pesos inversos a volatilidad.
- Stop dinámico por activo: `Precio_entrada - ATR(14) * multiplicador`.
- Cap de exposición: máximo 60% por activo.

## Instalación (PowerShell)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

> Si también trabajas en Linux/macOS, puedes usar `source .venv/bin/activate`.

## Ejecución principal

```powershell
python .\main.py
```

Esto ejecuta:

1. Descarga de datos históricos.
2. Construcción de features.
3. Entrenamiento rolling ML.
4. Optimización de hiperparámetros.
5. Backtest final.
6. Export de resultados a `outputs/`.
7. Impresión de señal mensual ejemplo.

## Dashboard

```powershell
streamlit run .\dashboard.py
```

Si los archivos de salida están en otra ruta:

```powershell
streamlit run .\dashboard.py -- --output-dir "C:\ruta\a\outputs"
```

## Salidas generadas

En `outputs/`:

- `equity_curve.csv` (estrategia vs benchmark)
- `metrics.csv` (CAGR, MaxDD, Sharpe, Vol, Sortino)
- `weights.csv`
- `trades.csv`
- `regime.csv`
- `optimizer_leaderboard.csv`

## Telegram

Definir variables de entorno:

```bash
export TELEGRAM_BOT_TOKEN="..."
export TELEGRAM_CHAT_ID="..."
```

Luego activar notificaciones en `main.py` llamando:

```python
main(send_notifications=True)
```

## Automatización mensual (cron / VPS)

Scripts preparados:

```bash
scripts/run_monthly.sh
```

```powershell
.\scripts\run_monthly.ps1
```

Ejemplo de cron (primer día de mes, 08:00 UTC):

```cron
0 8 1 * * /ruta/al/repo/scripts/run_monthly.sh >> /ruta/al/repo/cron.log 2>&1
```

## Ejemplo de señal mensual

```json
{
  "estado_mercado": "FAVORABLE",
  "probabilidad_ml": 0.7134,
  "pesos": {
    "IWDA.AS": 60.0,
    "EQQQ.L": 40.0
  },
  "nivel_riesgo": "ALTO"
}
```

## Recomendaciones de despliegue institucional

1. Ejecutar en VPS Linux con `systemd` + cron monitorizado.
2. Persistir outputs en almacenamiento versionado (S3/Blob) y registrar hash del dataset.
3. Añadir costos de transacción/slippage por broker antes de live.
4. Versionar parámetros óptimos por fecha de corte.
5. Incluir alertas de salud operativa (fallo de datos/API/latencia).
6. Añadir pruebas de estrés (2008, 2020, 2022) y validaciones de robustez por subperiodos.
