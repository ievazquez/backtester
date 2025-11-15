# Quick Start - Command Line Interface

This guide shows you how to use the Trading Platform from the command line, similar to Zipline.

## Installation

```bash
cd /home/user/backtester

# Install core dependencies
pip install numpy pandas scipy matplotlib click tqdm python-dateutil pytz

# Optional: Install data providers
pip install yfinance alpha-vantage

# Optional: Install broker APIs (for live trading)
pip install ibapi oandapyV20
```

## Basic Usage

### 1. Run Your First Backtest

```bash
python -m trading_platform.quantline run \
  -f examples/cli_test_strategy.py \
  -s 2023-01-01 \
  -e 2023-12-31 \
  --symbols AAPL \
  --capital-base 100000
```

**Output:**
```
============================================================
TRADING PLATFORM BACKTEST
============================================================
Strategy: CLITestStrategy
Symbols: AAPL
Period: 2023-01-01 to 2023-12-31
Capital: $100,000.00
Data Frequency: daily
============================================================

Loading historical data for 1 symbols...
Preload complete
Running backtest from 2023-01-01 00:00:00 to 2023-12-31 00:00:00
Total periods: 251
100%|████████████████████████████████| 251/251 [00:02<00:00, 112.50it/s]

Backtest complete!

[Performance metrics displayed here]
```

### 2. Multiple Symbols

```bash
python -m trading_platform.quantline run \
  -f examples/momentum_strategy.py \
  -s 2020-01-01 \
  -e 2023-12-31 \
  --symbols AAPL,GOOGL,MSFT \
  --capital-base 100000
```

### 3. Save Results to File

```bash
python -m trading_platform.quantline run \
  -f examples/cli_test_strategy.py \
  -s 2020-01-01 \
  -e 2023-12-31 \
  --symbols AAPL,GOOGL \
  --capital-base 100000 \
  -o my_backtest_results.txt
```

This creates:
- `my_backtest_results.txt` - Full performance report
- `my_backtest_results_equity.csv` - Equity curve data
- `my_backtest_results_trades.csv` - All trades

### 4. With Custom Parameters

```bash
python -m trading_platform.quantline run \
  -f examples/cli_test_strategy.py \
  -s 2020-01-01 \
  -e 2023-12-31 \
  --symbols AAPL \
  --capital-base 50000 \
  --commission 0.002 \
  --slippage 0.001 \
  --data-frequency daily
```

## All Available Options

### Backtest Command (`run`)

```bash
python -m trading_platform.quantline run --help
```

**Required Options:**
- `-f, --algofile PATH` - Path to your strategy file
- `-s, --start TEXT` - Start date (YYYY-MM-DD)
- `-e, --end TEXT` - End date (YYYY-MM-DD)
- `--symbols TEXT` - Comma-separated symbols (e.g., AAPL,GOOGL)

**Optional Parameters:**
- `--capital-base FLOAT` - Starting capital (default: 100000)
- `--commission FLOAT` - Commission rate (default: 0.001 = 0.1%)
- `--slippage FLOAT` - Slippage rate (default: 0.0005 = 0.05%)
- `--data-frequency [daily|hourly|minute]` - Data interval (default: daily)
- `--data-provider [yahoo|alphavantage|csv]` - Data source (default: yahoo)
- `-o, --output PATH` - Save results to file
- `--plot` - Show equity curve plot
- `--metrics-only` - Only show performance metrics
- `--no-cache` - Don't cache downloaded data

### Live Trading Command (`live`)

⚠️ **WARNING: Only use after thorough testing!**

```bash
python -m trading_platform.quantline live \
  -f examples/cli_test_strategy.py \
  --broker ib \
  --symbols AAPL \
  --paper
```

**Required Options:**
- `-f, --algofile PATH` - Path to your strategy file
- `--broker [ib|oanda|darwinex]` - Broker to use
- `--symbols TEXT` - Comma-separated symbols

**Optional Parameters:**
- `--paper` - Use paper trading mode (RECOMMENDED)
- `--max-position-size FLOAT` - Max position size (default: 0.1 = 10%)
- `--max-daily-loss FLOAT` - Max daily loss (default: 0.05 = 5%)
- `--update-interval FLOAT` - Update interval in seconds (default: 1.0)

## Complete Examples

### Example 1: Simple Backtest

```bash
# Test a moving average strategy on Apple stock
python -m trading_platform.quantline run \
  -f examples/simple_ma_crossover.py \
  -s 2020-01-01 \
  -e 2023-12-31 \
  --symbols AAPL \
  --capital-base 100000
```

### Example 2: Multi-Symbol Portfolio

```bash
# Test momentum strategy across multiple tech stocks
python -m trading_platform.quantline run \
  -f examples/momentum_strategy.py \
  -s 2020-01-01 \
  -e 2023-12-31 \
  --symbols AAPL,GOOGL,MSFT,AMZN \
  --capital-base 200000 \
  -o tech_momentum.txt
```

### Example 3: Save and Plot

```bash
# Run backtest, save results, and show plot
python -m trading_platform.quantline run \
  -f examples/multi_asset_strategy.py \
  -s 2020-01-01 \
  -e 2023-12-31 \
  --symbols AAPL,GOOGL,JPM,XOM,JNJ,GLD,TLT \
  --capital-base 100000 \
  -o portfolio_results.txt \
  --plot
```

### Example 4: Custom Commission/Slippage

```bash
# Simulate higher trading costs
python -m trading_platform.quantline run \
  -f examples/cli_test_strategy.py \
  -s 2020-01-01 \
  -e 2023-12-31 \
  --symbols AAPL \
  --commission 0.005 \
  --slippage 0.002 \
  --capital-base 100000
```

### Example 5: Metrics Only (Quick Check)

```bash
# Just show performance metrics
python -m trading_platform.quantline run \
  -f examples/cli_test_strategy.py \
  -s 2023-01-01 \
  -e 2023-12-31 \
  --symbols AAPL \
  --metrics-only
```

## Comparison with Zipline

Our CLI is similar to Zipline but with some differences:

| Feature | Zipline | Trading Platform |
|---------|---------|------------------|
| Strategy file | `-f, --algofile` | `-f, --algofile` ✓ |
| Algorithm text | `-t, --algotext` | `-t, --algotext` ✓ |
| Start date | `-s, --start` | `-s, --start` ✓ |
| End date | `-e, --end` | `-e, --end` ✓ |
| Capital | `--capital-base` | `--capital-base` ✓ |
| Data frequency | `--data-frequency` | `--data-frequency` ✓ |
| Output | `-o, --output` | `-o, --output` ✓ |
| Symbols | `--bundle` | `--symbols` (simpler!) |
| Live trading | Not built-in | `live` command ✓ |

### Key Differences:

1. **Symbols**: We use `--symbols AAPL,GOOGL` instead of data bundles
2. **Data Provider**: Direct integration with Yahoo Finance, Alpha Vantage
3. **Live Trading**: Built-in live trading support with `live` command
4. **Simpler**: No need for data ingestion - just specify symbols!

## Tips

1. **Start Small**: Begin with one symbol and short time period
2. **Save Results**: Always use `-o` to save results for analysis
3. **Test Thoroughly**: Run backtests on different time periods
4. **Paper Trading First**: Use `--paper` before live trading
5. **Monitor Costs**: Adjust `--commission` and `--slippage` to match your broker

## Need Help?

```bash
# General help
python -m trading_platform.quantline --help

# Help for run command
python -m trading_platform.quantline run --help

# Help for live command
python -m trading_platform.quantline live --help
```

## Next Steps

1. Try the examples in `examples/` directory
2. Read `CLI_EXAMPLES.md` for more advanced usage
3. Check `docs/` for detailed documentation
4. Create your own strategy based on examples

Happy Trading! 🚀
