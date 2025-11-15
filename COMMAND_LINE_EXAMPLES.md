# Trading Platform - Líneas de Comando para Probar

Este documento contiene líneas de comando listas para copiar y ejecutar, similares a las opciones de Zipline.

## 📋 Requisitos Previos

```bash
cd /home/user/backtester
pip install numpy pandas scipy matplotlib click tqdm python-dateutil pytz
```

## 🚀 Ejemplos Básicos

### 1. Backtest Simple (1 símbolo)
```bash
python -m trading_platform.cli run \
  -f examples/cli_test_strategy.py \
  -s 2023-01-01 \
  -e 2023-12-31 \
  --symbols AAPL \
  --capital-base 100000
```

### 2. Backtest con Múltiples Símbolos
```bash
python -m trading_platform.cli run \
  -f examples/momentum_strategy.py \
  -s 2020-01-01 \
  -e 2023-12-31 \
  --symbols AAPL,GOOGL,MSFT \
  --capital-base 100000
```

### 3. Guardar Resultados en Archivo
```bash
python -m trading_platform.cli run \
  -f examples/cli_test_strategy.py \
  -s 2020-01-01 \
  -e 2023-12-31 \
  --symbols AAPL,GOOGL \
  --capital-base 100000 \
  -o resultados_backtest.txt
```

## 📊 Ejemplos con Opciones Avanzadas

### 4. Con Comisiones y Slippage Personalizados
```bash
python -m trading_platform.cli run \
  -f examples/cli_test_strategy.py \
  -s 2020-01-01 \
  -e 2023-12-31 \
  --symbols AAPL \
  --capital-base 100000 \
  --commission 0.002 \
  --slippage 0.001
```

### 5. Frecuencia de Datos Horaria
```bash
python -m trading_platform.cli run \
  -f examples/cli_test_strategy.py \
  -s 2023-11-01 \
  -e 2023-12-31 \
  --symbols AAPL \
  --data-frequency hourly \
  --capital-base 100000
```

### 6. Con Gráfico de Equity Curve
```bash
python -m trading_platform.cli run \
  -f examples/cli_test_strategy.py \
  -s 2020-01-01 \
  -e 2023-12-31 \
  --symbols AAPL \
  --capital-base 100000 \
  --plot
```

### 7. Solo Métricas (Salida Resumida)
```bash
python -m trading_platform.cli run \
  -f examples/cli_test_strategy.py \
  -s 2023-01-01 \
  -e 2023-12-31 \
  --symbols AAPL \
  --capital-base 100000 \
  --metrics-only
```

### 8. Portafolio Multi-Asset
```bash
python -m trading_platform.cli run \
  -f examples/multi_asset_strategy.py \
  -s 2020-01-01 \
  -e 2023-12-31 \
  --symbols AAPL,GOOGL,JPM,XOM,JNJ,GLD,TLT \
  --capital-base 200000 \
  -o portfolio_diversificado.txt \
  --plot
```

## 🎯 Mapeo de Opciones Zipline → Trading Platform

| Zipline | Trading Platform | Descripción |
|---------|------------------|-------------|
| `-f, --algofile FILENAME` | `-f, --algofile PATH` | ✅ Archivo con la estrategia |
| `-t, --algotext TEXT` | `-t, --algotext TEXT` | ✅ Código de estrategia inline |
| `--data-frequency [daily\|minute]` | `--data-frequency [daily\|hourly\|minute]` | ✅ Frecuencia de datos |
| `--capital-base FLOAT` | `--capital-base FLOAT` | ✅ Capital inicial (default: 100000) |
| `-b, --bundle BUNDLE-NAME` | `--symbols TEXT` | 📝 Símbolos directos (más simple) |
| `-s, --start DATE` | `-s, --start TEXT` | ✅ Fecha inicio (YYYY-MM-DD) |
| `-e, --end DATE` | `-e, --end TEXT` | ✅ Fecha fin (YYYY-MM-DD) |
| `-o, --output FILENAME` | `-o, --output PATH` | ✅ Archivo de salida |
| N/A | `--commission FLOAT` | ➕ Tasa de comisión (default: 0.001) |
| N/A | `--slippage FLOAT` | ➕ Tasa de slippage (default: 0.0005) |
| N/A | `--data-provider [yahoo\|alphavantage\|csv]` | ➕ Proveedor de datos |
| N/A | `--plot` | ➕ Mostrar gráficos |
| N/A | `--metrics-only` | ➕ Solo métricas |
| `--no-benchmark` | N/A | 📌 Benchmark opcional |

## 💡 Ejemplos Comparativos

### Zipline Original:
```bash
zipline run \
  -f my_strategy.py \
  -s 2020-01-01 \
  -e 2023-12-31 \
  -b quandl \
  --capital-base 100000 \
  -o results.pkl
```

### Trading Platform Equivalente:
```bash
python -m trading_platform.cli run \
  -f examples/cli_test_strategy.py \
  -s 2020-01-01 \
  -e 2023-12-31 \
  --symbols AAPL,GOOGL,MSFT \
  --capital-base 100000 \
  -o results.txt
```

### Ventajas vs Zipline:
✅ No requiere ingestión de datos previa
✅ Símbolos directos sin bundles
✅ Múltiples proveedores de datos integrados
✅ Trading en vivo incorporado
✅ Resultados en formato texto legible

## 🔧 Opciones Completas del Comando `run`

```
Options:
  -f, --algofile PATH             Archivo con la estrategia
  -t, --algotext TEXT             Código de estrategia como texto
  --data-frequency [daily|hourly|minute]
                                  Frecuencia de datos [default: daily]
  --capital-base FLOAT            Capital inicial [default: 100000.0]
  -s, --start TEXT                Fecha inicio (YYYY-MM-DD) [requerido]
  -e, --end TEXT                  Fecha fin (YYYY-MM-DD) [requerido]
  --symbols TEXT                  Símbolos separados por comas [requerido]
  -o, --output PATH               Archivo de salida
  --commission FLOAT              Tasa de comisión [default: 0.001]
  --slippage FLOAT                Tasa de slippage [default: 0.0005]
  --data-provider [yahoo|alphavantage|csv]
                                  Proveedor de datos [default: yahoo]
  --csv-dir PATH                  Directorio con archivos CSV
  --no-cache                      Deshabilitar caché de datos
  --plot                          Mostrar gráfico de equity curve
  --metrics-only                  Solo mostrar métricas de rendimiento
  --help                          Mostrar ayuda
```

## 📈 Ejemplo de Salida

```
============================================================
TRADING PLATFORM BACKTEST
============================================================
Strategy: CLITestStrategy
Symbols: AAPL, GOOGL
Period: 2020-01-01 to 2023-12-31
Capital: $100,000.00
Data Frequency: daily
============================================================

Loading historical data for 2 symbols...
Running backtest from 2020-01-01 to 2023-12-31
Total periods: 1006
100%|████████████████████████| 1006/1006 [00:05<00:00, 178.32it/s]

Backtest complete!

======================================================================
PERFORMANCE METRICS
======================================================================

RETURNS
----------------------------------------------------------------------
  Initial Capital:        $    100,000.00
  Final Equity:           $    145,234.56
  Total Return:                     45.23%
  Annualized Return:                12.45%
  Total P&L:              $     45,234.56

RISK METRICS
----------------------------------------------------------------------
  Volatility (Ann.):                18.32%
  Sharpe Ratio:                      0.68
  Sortino Ratio:                     0.95
  Max Drawdown:                     15.67%
  Max DD Duration:                     123 days
  Current Drawdown:                  3.45%

TRADING STATISTICS
----------------------------------------------------------------------
  Total Trades:                         87
  Winners:                              54
  Losers:                               33
  Win Rate:                         62.07%
  Average Win:             $        956.78
  Average Loss:            $        478.23
  Profit Factor:                     2.13
  Open Positions:                        1
======================================================================
```

## 🎓 Tutorial Paso a Paso

### Paso 1: Verificar instalación
```bash
python -m trading_platform.cli --help
```

### Paso 2: Ejecutar ejemplo simple
```bash
python -m trading_platform.cli run \
  -f examples/cli_test_strategy.py \
  -s 2023-01-01 \
  -e 2023-12-31 \
  --symbols AAPL \
  --capital-base 10000
```

### Paso 3: Guardar resultados
```bash
python -m trading_platform.cli run \
  -f examples/cli_test_strategy.py \
  -s 2023-01-01 \
  -e 2023-12-31 \
  --symbols AAPL \
  --capital-base 10000 \
  -o mi_primer_backtest.txt
```

### Paso 4: Ver resultados guardados
```bash
cat mi_primer_backtest.txt
cat mi_primer_backtest_equity.csv
cat mi_primer_backtest_trades.csv
```

### Paso 5: Probar con múltiples símbolos
```bash
python -m trading_platform.cli run \
  -f examples/momentum_strategy.py \
  -s 2023-01-01 \
  -e 2023-12-31 \
  --symbols AAPL,GOOGL,MSFT \
  --capital-base 50000 \
  -o multi_symbol.txt \
  --plot
```

## ⚠️ Notas Importantes

1. **Fechas**: Siempre usar formato YYYY-MM-DD
2. **Símbolos**: Separar con comas, sin espacios (AAPL,GOOGL,MSFT)
3. **Capital**: En dólares, sin símbolos (100000, no $100,000)
4. **Comisión/Slippage**: Como decimal (0.001 = 0.1%)
5. **Data Frequency**: Para minute/hourly necesitas períodos más cortos

## 🆘 Ayuda

```bash
# Ayuda general
python -m trading_platform.cli --help

# Ayuda comando run
python -m trading_platform.cli run --help

# Ayuda comando live (trading en vivo)
python -m trading_platform.cli live --help
```

## 📚 Recursos Adicionales

- `QUICKSTART_CLI.md` - Guía de inicio rápido
- `CLI_EXAMPLES.md` - Ejemplos avanzados completos
- `docs/` - Documentación detallada
- `examples/` - Estrategias de ejemplo

---

**¿Listo para empezar?** Copia cualquiera de estos comandos y ejecútalos. ¡Así de fácil! 🚀
