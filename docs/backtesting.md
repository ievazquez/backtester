# Backtesting Guide

Comprehensive guide to backtesting strategies with the Trading Platform.

## Overview

The backtesting engine simulates historical trading with:
- Event-driven architecture for realistic simulation
- Commission and slippage modeling
- Multiple data providers
- Comprehensive performance metrics

## Basic Backtesting

### Minimal Example

```python
from datetime import datetime
from trading_platform.backtesting.engine import BacktestEngine
from trading_platform.core.strategy import Strategy

class SimpleStrategy(Strategy):
    def on_data(self, data):
        # Your strategy logic
        pass

engine = BacktestEngine(
    strategy=SimpleStrategy(),
    symbols=['AAPL'],
    start_date=datetime(2020, 1, 1),
    end_date=datetime(2023, 12, 31),
    initial_capital=100000
)

results = engine.run()
```

## Configuration Options

### BacktestEngine Parameters

```python
engine = BacktestEngine(
    strategy=my_strategy,           # Your strategy instance
    symbols=['AAPL', 'GOOGL'],     # List of symbols
    start_date=datetime(2020, 1, 1),  # Start date
    end_date=datetime(2023, 12, 31),   # End date
    initial_capital=100000,         # Starting capital
    data_provider=None,             # Custom data provider (optional)
    commission=0.001,               # 0.1% commission per trade
    slippage=0.0005,               # 0.05% slippage
    use_cache=True,                # Cache historical data
    interval='1d'                  # Data interval
)
```

### Data Intervals

Supported intervals:
- `'1m'`: 1 minute
- `'5m'`: 5 minutes
- `'15m'`: 15 minutes
- `'30m'`: 30 minutes
- `'1h'`: 1 hour
- `'4h'`: 4 hours
- `'1d'`: 1 day (default)

## Data Providers

### Yahoo Finance (Default)

```python
from trading_platform.data.providers import YahooFinanceProvider

provider = YahooFinanceProvider()
engine = BacktestEngine(
    strategy=strategy,
    symbols=['AAPL'],
    start_date=start_date,
    end_date=end_date,
    data_provider=provider
)
```

### Alpha Vantage

```python
from trading_platform.data.providers import AlphaVantageProvider

provider = AlphaVantageProvider(api_key='YOUR_API_KEY')
engine = BacktestEngine(
    strategy=strategy,
    symbols=['AAPL'],
    start_date=start_date,
    end_date=end_date,
    data_provider=provider
)
```

### CSV Files

```python
from trading_platform.data.providers import CSVDataProvider

provider = CSVDataProvider(data_dir='./my_data')
# Expects files named: AAPL.csv, GOOGL.csv, etc.
# CSV format: timestamp,open,high,low,close,volume

engine = BacktestEngine(
    strategy=strategy,
    symbols=['AAPL'],
    start_date=start_date,
    end_date=end_date,
    data_provider=provider
)
```

## Performance Metrics

### Available Metrics

```python
results = engine.run()
metrics = results.get_metrics()

# Returns dictionary with:
# - total_return_pct: Total return percentage
# - annualized_return_pct: Annualized return
# - volatility_pct: Annualized volatility
# - sharpe_ratio: Risk-adjusted return
# - sortino_ratio: Downside risk-adjusted return
# - max_drawdown_pct: Maximum drawdown
# - win_rate_pct: Percentage of winning trades
# - profit_factor: Ratio of gross profit to gross loss
```

### Print Summary

```python
print(results.summary())
```

Output example:
```
======================================================================
PERFORMANCE METRICS
======================================================================

RETURNS
----------------------------------------------------------------------
  Initial Capital:        $    100,000.00
  Final Equity:           $    152,345.67
  Total Return:                     52.35%
  Annualized Return:                14.23%
  Total P&L:              $     52,345.67

RISK METRICS
----------------------------------------------------------------------
  Volatility (Ann.):                18.45%
  Sharpe Ratio:                      0.77
  Sortino Ratio:                     1.12
  Max Drawdown:                     12.34%
  Max DD Duration:                     87 days
  Current Drawdown:                  2.15%

TRADING STATISTICS
----------------------------------------------------------------------
  Total Trades:                        142
  Winners:                              87
  Losers:                               55
  Win Rate:                         61.27%
  Average Win:             $        876.54
  Average Loss:            $        432.10
  Profit Factor:                     2.15
  Open Positions:                       2
======================================================================
```

## Visualization

### Equity Curve

```python
results.plot_equity_curve()
# Displays equity curve and drawdown chart
```

### Returns Distribution

```python
results.plot_returns_distribution()
# Displays histogram of daily returns
```

### Save Plots

```python
results.plot_equity_curve(save_path='equity_curve.png')
results.plot_returns_distribution(save_path='returns_dist.png')
```

## Advanced Features

### Multiple Symbols

```python
symbols = ['AAPL', 'GOOGL', 'MSFT', 'AMZN']

engine = BacktestEngine(
    strategy=strategy,
    symbols=symbols,
    start_date=start_date,
    end_date=end_date
)
```

### Transaction History

```python
# Get all orders
orders_df = engine.get_orders_df()
print(orders_df)

# Get portfolio transactions
transactions_df = engine.portfolio.get_transactions_df()
print(transactions_df)
```

### Equity Curve Data

```python
equity_df = engine.portfolio.get_equity_curve_df()
# DataFrame with columns: equity, cash, positions_value
```

## Commission and Slippage

### Commission Models

```python
# Percentage-based (default)
commission = 0.001  # 0.1% per trade

# Fixed per-share (implementation example)
class PerShareCommission:
    def calculate(self, quantity, price):
        return quantity * 0.01  # $0.01 per share
```

### Slippage Models

```python
# Percentage-based (default)
slippage = 0.0005  # 0.05% slippage

# Custom slippage (future implementation)
# Can be extended for volume-based, spread-based, etc.
```

## Tips for Effective Backtesting

### 1. Use Sufficient Data

```python
# Ensure enough warmup period for indicators
if len(df) < self.lookback_period:
    return  # Skip until we have enough data
```

### 2. Avoid Look-Ahead Bias

```python
# Good: Use .iloc[-1] for current bar
current_price = df['close'].iloc[-1]

# Bad: Using future data
# Don't use df['close'].iloc[0] if time is ascending
```

### 3. Handle Missing Data

```python
def on_data(self, data):
    if 'AAPL' not in data:
        return  # Symbol data not available

    df = data['AAPL']
    if df.empty:
        return  # No data for this period
```

### 4. Test Multiple Periods

```python
# Test across different market conditions
periods = [
    (datetime(2020, 1, 1), datetime(2020, 12, 31)),  # Bull market
    (datetime(2022, 1, 1), datetime(2022, 12, 31)),  # Bear market
    (datetime(2018, 1, 1), datetime(2023, 12, 31)),  # Full cycle
]

for start, end in periods:
    engine = BacktestEngine(...)
    results = engine.run()
    print(f"{start.year}-{end.year}: {results.total_return:.2f}%")
```

## Common Pitfalls

1. **Overfitting**: Don't over-optimize for past data
2. **Insufficient Data**: Test with multi-year datasets
3. **Ignoring Costs**: Always include realistic commissions and slippage
4. **Survivorship Bias**: Be aware of delisted stocks
5. **Look-Ahead Bias**: Never use future information

## Next Steps

- Review [Strategy Development](strategy_development.md) for strategy patterns
- See `examples/` for complete strategy implementations
- Read [Live Trading Guide](live_trading.md) for going live
