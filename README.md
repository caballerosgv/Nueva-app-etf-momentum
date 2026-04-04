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

## Manual paso a paso: instalación y ejecución

### 0) Prerrequisitos

- Sistema operativo recomendado: Linux/macOS (en Windows, usar WSL o PowerShell adaptando comandos).
- Python 3.10+.
- `pip` y `venv` habilitados.
- Conexión a internet para descargar datos de mercado y dependencias.

Verificación rápida:

```bash
python --version
pip --version
```

### 1) Clonar el repositorio

```bash
git clone <URL_DEL_REPOSITORIO>
cd Nueva-app-etf-momentum
```

> Si ya lo tienes descargado, entra directamente a la carpeta del proyecto.

### 2) Crear y activar entorno virtual

```bash
python -m venv .venv
source .venv/bin/activate
```

En Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 3) Instalar dependencias

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4) (Opcional) Configurar variables de entorno para Telegram

Si quieres recibir notificaciones automáticas de señal mensual, define:

```bash
export TELEGRAM_BOT_TOKEN="..."
export TELEGRAM_CHAT_ID="..."
```

En Windows PowerShell:

```powershell
$env:TELEGRAM_BOT_TOKEN="..."
$env:TELEGRAM_CHAT_ID="..."
```

### 5) Ejecutar el pipeline principal

```bash
python main.py
```

Esta ejecución realiza, en orden:

1. Descarga de datos históricos.
2. Construcción de features.
3. Entrenamiento rolling del modelo ML.
4. Optimización de hiperparámetros.
5. Backtest final.
6. Exportación de resultados en `outputs/`.
7. Impresión de señal mensual de ejemplo.

### 6) Revisar resultados

Al finalizar, revisa la carpeta `outputs/` con los artefactos principales:

- `equity_curve.csv` (estrategia vs benchmark)
- `metrics.csv` (CAGR, MaxDD, Sharpe, Vol, Sortino)
- `weights.csv`
- `trades.csv`
- `regime.csv`
- `optimizer_leaderboard.csv`

### 7) Ejecutar el dashboard

Con el entorno virtual aún activo:

```bash
streamlit run dashboard.py
```

Luego abre en tu navegador la URL local que muestra Streamlit (habitualmente `http://localhost:8501`).

### 8) Ejecución mensual automatizada (cron / VPS)

Ya existe un script preparado:

```bash
bash scripts/run_monthly.sh
```

Ejemplo de cron (primer día de mes, 08:00 UTC):

```cron
0 8 1 * * /ruta/al/repo/scripts/run_monthly.sh >> /ruta/al/repo/cron.log 2>&1
```

### 9) Solución rápida de problemas

- **Error de dependencias**: ejecuta `pip install -r requirements.txt` otra vez con el entorno virtual activado.
- **No se abre Streamlit**: verifica que el proceso siga corriendo y usa la URL que imprime en terminal.
- **Sin notificaciones Telegram**: confirma token/chat_id válidos y que el bot tenga acceso al chat.
- **Datos incompletos**: vuelve a lanzar `python main.py` cuando haya conectividad estable.

## Ejecución rápida (resumen)

Si ya conoces el flujo, estos son los comandos mínimos:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python main.py
streamlit run dashboard.py
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
