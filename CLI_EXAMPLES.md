# Trading Platform CLI Examples

This document provides example command lines for using the Trading Platform CLI.

## Prerequisites

```bash
# Install the platform
cd /home/user/backtester
pip install -e .

# Verify installation
trading-platform --help
```

## Backtesting Examples

### 1. Basic Backtest (Single Symbol)

```bash
trading-platform run \
  -f examples/cli_test_strategy.py \
  -s 2020-01-01 \
  -e 2023-12-31 \
  --symbols AAPL \
  --capital-base 100000
```

### 2. Multiple Symbols

```bash
trading-platform run \
  -f examples/cli_test_strategy.py \
  -s 2020-01-01 \
  -e 2023-12-31 \
  --symbols AAPL,GOOGL,MSFT \
  --capital-base 100000
```

### 3. Save Results to File

```bash
trading-platform run \
  -f examples/cli_test_strategy.py \
  -s 2020-01-01 \
  -e 2023-12-31 \
  --symbols AAPL,GOOGL \
  --capital-base 100000 \
  -o results.txt
```

This will create:
- `results.txt` - Performance summary
- `results_equity.csv` - Equity curve data
- `results_trades.csv` - Trade history

### 4. Custom Commission and Slippage

```bash
trading-platform run \
  -f examples/cli_test_strategy.py \
  -s 2020-01-01 \
  -e 2023-12-31 \
  --symbols AAPL \
  --commission 0.002 \
  --slippage 0.001 \
  --capital-base 100000
```

### 5. Hourly Data Frequency

```bash
trading-platform run \
  -f examples/cli_test_strategy.py \
  -s 2023-01-01 \
  -e 2023-12-31 \
  --symbols AAPL \
  --data-frequency hourly \
  --capital-base 100000
```

### 6. With Plotting

```bash
trading-platform run \
  -f examples/cli_test_strategy.py \
  -s 2020-01-01 \
  -e 2023-12-31 \
  --symbols AAPL \
  --capital-base 100000 \
  --plot
```

### 7. Metrics Only (Concise Output)

```bash
trading-platform run \
  -f examples/cli_test_strategy.py \
  -s 2020-01-01 \
  -e 2023-12-31 \
  --symbols AAPL \
  --capital-base 100000 \
  --metrics-only
```

### 8. Use CSV Data Provider

```bash
# First, prepare CSV files in a directory
# Files should be named: AAPL.csv, GOOGL.csv, etc.
# Format: timestamp,open,high,low,close,volume

trading-platform run \
  -f examples/cli_test_strategy.py \
  -s 2020-01-01 \
  -e 2023-12-31 \
  --symbols AAPL \
  --data-provider csv \
  --csv-dir ./my_data \
  --capital-base 100000
```

### 9. Disable Caching

```bash
trading-platform run \
  -f examples/cli_test_strategy.py \
  -s 2020-01-01 \
  -e 2023-12-31 \
  --symbols AAPL \
  --no-cache \
  --capital-base 100000
```

### 10. Using Inline Strategy Text

```bash
trading-platform run \
  -t "from trading_platform.core.strategy import Strategy
from trading_platform.utils.indicators import sma

class QuickStrategy(Strategy):
    def on_data(self, data):
        df = data['AAPL']
        if len(df) < 20:
            return
        ma = sma(df['close'], 20)
        if df['close'].iloc[-1] > ma.iloc[-1]:
            if not self.portfolio.has_position('AAPL'):
                return self.buy('AAPL', 100)" \
  -s 2023-01-01 \
  -e 2023-12-31 \
  --symbols AAPL \
  --capital-base 100000
```

## Live Trading Examples

**⚠️ WARNING: These examples use real money in live mode. Always test with --paper first!**

### 1. Paper Trading (Interactive Brokers)

```bash
# Make sure IB TWS/Gateway is running on paper trading mode
trading-platform live \
  -f examples/cli_test_strategy.py \
  --broker ib \
  --symbols AAPL \
  --paper
```

### 2. Paper Trading (OANDA)

```bash
# Set environment variables first:
export OANDA_API_TOKEN="your_token_here"
export OANDA_ACCOUNT_ID="your_account_id"

trading-platform live \
  -f examples/cli_test_strategy.py \
  --broker oanda \
  --symbols EUR_USD \
  --paper
```

### 3. Live Trading with Risk Limits

```bash
# LIVE TRADING - USE WITH EXTREME CAUTION
trading-platform live \
  -f examples/cli_test_strategy.py \
  --broker ib \
  --symbols AAPL \
  --max-position-size 0.05 \
  --max-daily-loss 0.02 \
  --update-interval 5.0
```

### 4. Multiple Symbols Live

```bash
trading-platform live \
  -f examples/cli_test_strategy.py \
  --broker ib \
  --symbols AAPL,GOOGL,MSFT \
  --paper \
  --max-position-size 0.10
```

## Advanced Examples

### Complete Backtest Workflow

```bash
# 1. Run backtest
trading-platform run \
  -f examples/momentum_strategy.py \
  -s 2020-01-01 \
  -e 2023-12-31 \
  --symbols AAPL,GOOGL,MSFT \
  --capital-base 100000 \
  -o backtest_results.txt \
  --plot

# 2. Review results
cat backtest_results.txt

# 3. Check equity curve
head backtest_results_equity.csv

# 4. Analyze trades
head backtest_results_trades.csv

# 5. If satisfied, test in paper trading
trading-platform live \
  -f examples/momentum_strategy.py \
  --broker ib \
  --symbols AAPL,GOOGL,MSFT \
  --paper
```

### Test Same Strategy Different Periods

```bash
# Bull market
trading-platform run \
  -f examples/cli_test_strategy.py \
  -s 2020-01-01 \
  -e 2021-12-31 \
  --symbols AAPL \
  -o bull_market.txt

# Bear market
trading-platform run \
  -f examples/cli_test_strategy.py \
  -s 2022-01-01 \
  -e 2022-12-31 \
  --symbols AAPL \
  -o bear_market.txt

# Compare
diff bull_market.txt bear_market.txt
```

## Environment Variables

### OANDA

```bash
export OANDA_API_TOKEN="your_oanda_api_token"
export OANDA_ACCOUNT_ID="your_oanda_account_id"
```

### Darwinex

```bash
export DARWINEX_ACCOUNT_ID="your_mt5_account"
export DARWINEX_PASSWORD="your_mt5_password"
```

### Alpha Vantage

```bash
export ALPHAVANTAGE_API_KEY="your_alphavantage_key"
```

## Tips

1. **Always start with paper trading** before going live
2. **Test on historical data first** with multiple market conditions
3. **Start small** - use low capital and position sizes initially
4. **Monitor closely** - especially in the first days of live trading
5. **Keep logs** - save results to files for analysis
6. **Use stop losses** - implement proper risk management in your strategy

## Getting Help

```bash
# General help
trading-platform --help

# Help for run command
trading-platform run --help

# Help for live command
trading-platform live --help
```
