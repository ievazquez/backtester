# Strategy Development Guide

Comprehensive guide to developing trading strategies.

## Strategy Lifecycle

```python
from trading_platform.core.strategy import Strategy

class MyStrategy(Strategy):
    def __init__(self):
        super().__init__(name="MyStrategy")
        # Initialize parameters
        self.param1 = 20
        self.param2 = 50

    def on_start(self):
        """Called once when strategy starts"""
        self.log("Strategy starting...")
        # Load models, initialize indicators, etc.

    def on_data(self, data):
        """Called on each new data point"""
        # Main strategy logic goes here
        # Return Order or list of Orders

    def on_order_filled(self, order):
        """Called when an order fills"""
        # Update stops, track positions, etc.

    def on_order_cancelled(self, order):
        """Called when an order is cancelled"""
        # Handle cancellation logic

    def on_stop(self):
        """Called when strategy stops"""
        self.log("Strategy stopping...")
        # Cleanup, save state, etc.
```

## Accessing Data

### Current Data

```python
def on_data(self, data):
    # data is a dictionary: {symbol: DataFrame}

    # Get data for specific symbol
    df = data['AAPL']

    # Access OHLCV columns
    current_close = df['close'].iloc[-1]
    current_high = df['high'].iloc[-1]
    current_volume = df['volume'].iloc[-1]

    # Get historical data (all data up to current time)
    last_10_closes = df['close'].tail(10)
```

### Multiple Symbols

```python
def on_data(self, data):
    for symbol, df in data.items():
        # Process each symbol
        price = df['close'].iloc[-1]
        print(f"{symbol}: ${price:.2f}")
```

## Using Technical Indicators

### Built-in Indicators

```python
from trading_platform.utils.indicators import sma, ema, rsi, macd, bollinger_bands

def on_data(self, data):
    df = data['AAPL']

    # Simple Moving Average
    sma_20 = sma(df['close'], 20)

    # Exponential Moving Average
    ema_12 = ema(df['close'], 12)

    # RSI
    rsi_14 = rsi(df['close'], 14)

    # MACD
    macd_line, signal, histogram = macd(df['close'])

    # Bollinger Bands
    upper, middle, lower = bollinger_bands(df['close'], 20, 2.0)

    # Get current values
    current_rsi = rsi_14.iloc[-1]
    current_macd = macd_line.iloc[-1]
```

### Custom Indicators

```python
def calculate_custom_indicator(self, data):
    """Example: Custom momentum indicator"""
    # Your custom calculation
    momentum = data['close'].pct_change(periods=10)
    return momentum

def on_data(self, data):
    df = data['AAPL']

    custom_ind = self.calculate_custom_indicator(df)
    current_value = custom_ind.iloc[-1]
```

## Order Management

### Creating Orders

```python
# Market orders
buy_order = self.buy('AAPL', 100)
sell_order = self.sell('AAPL', 100)

# Limit orders
from trading_platform.core.order import OrderType

limit_buy = self.buy(
    'AAPL',
    100,
    order_type=OrderType.LIMIT,
    limit_price=150.00
)

# Stop orders
stop_sell = self.sell(
    'AAPL',
    100,
    order_type=OrderType.STOP,
    stop_price=145.00
)
```

### Position Management

```python
# Check if we have a position
if self.portfolio.has_position('AAPL'):
    # Get position details
    position = self.portfolio.get_position('AAPL')
    print(f"Quantity: {position.quantity}")
    print(f"Avg Price: {position.average_price}")
    print(f"P&L: {position.total_pnl()}")

# Get position quantity
quantity = self.get_position_quantity('AAPL')

# Close a position
close_order = self.close_position('AAPL')

# Close all positions
orders = self.close_all_positions()
```

## Strategy Patterns

### 1. Trend Following

```python
class TrendFollowing(Strategy):
    def __init__(self):
        super().__init__()
        self.ma_period = 50

    def on_data(self, data):
        df = data['AAPL']

        ma = sma(df['close'], self.ma_period)
        price = df['close'].iloc[-1]

        # Buy when price crosses above MA
        if price > ma.iloc[-1] and not self.portfolio.has_position('AAPL'):
            return self.buy('AAPL', 100)

        # Sell when price crosses below MA
        elif price < ma.iloc[-1] and self.portfolio.has_position('AAPL'):
            return self.sell('AAPL', 100)
```

### 2. Mean Reversion

```python
class MeanReversion(Strategy):
    def __init__(self):
        super().__init__()
        self.bb_period = 20
        self.bb_std = 2.0

    def on_data(self, data):
        df = data['AAPL']

        upper, middle, lower = bollinger_bands(
            df['close'],
            self.bb_period,
            self.bb_std
        )

        price = df['close'].iloc[-1]

        # Buy when price touches lower band
        if price <= lower.iloc[-1] and not self.portfolio.has_position('AAPL'):
            return self.buy('AAPL', 100)

        # Sell when price touches upper band
        elif price >= upper.iloc[-1] and self.portfolio.has_position('AAPL'):
            return self.sell('AAPL', 100)
```

### 3. Momentum

```python
class Momentum(Strategy):
    def __init__(self):
        super().__init__()
        self.rsi_period = 14

    def on_data(self, data):
        df = data['AAPL']

        rsi_val = rsi(df['close'], self.rsi_period)

        # Buy when RSI < 30 (oversold)
        if rsi_val.iloc[-1] < 30 and not self.portfolio.has_position('AAPL'):
            return self.buy('AAPL', 100)

        # Sell when RSI > 70 (overbought)
        elif rsi_val.iloc[-1] > 70 and self.portfolio.has_position('AAPL'):
            return self.sell('AAPL', 100)
```

### 4. Multi-Timeframe

```python
class MultiTimeframe(Strategy):
    def __init__(self):
        super().__init__()
        self.slow_ma = 200  # Daily
        self.fast_ma = 20   # Daily

    def on_data(self, data):
        df = data['AAPL']

        # Long-term trend (slow MA)
        long_trend = sma(df['close'], self.slow_ma)
        # Short-term signal (fast MA)
        short_signal = sma(df['close'], self.fast_ma)

        price = df['close'].iloc[-1]

        # Only buy if long-term trend is bullish
        if price > long_trend.iloc[-1]:
            # Use short-term signal for entry
            if price > short_signal.iloc[-1] and not self.portfolio.has_position('AAPL'):
                return self.buy('AAPL', 100)

        # Sell on short-term signal regardless of trend
        if price < short_signal.iloc[-1] and self.portfolio.has_position('AAPL'):
            return self.sell('AAPL', 100)
```

## Advanced Techniques

### Dynamic Position Sizing

```python
def calculate_position_size(self, symbol, data):
    """Calculate position size based on volatility"""
    from trading_platform.utils.indicators import atr

    df = data[symbol]
    atr_val = atr(df['high'], df['low'], df['close'], 14).iloc[-1]

    # Risk-based sizing
    risk_per_trade = self.portfolio.total_equity() * 0.02  # 2% risk
    position_size = risk_per_trade / atr_val

    return int(position_size)

def on_data(self, data):
    df = data['AAPL']

    if buy_signal:
        size = self.calculate_position_size('AAPL', data)
        return self.buy('AAPL', size)
```

### Portfolio Rebalancing

```python
class PortfolioStrategy(Strategy):
    def __init__(self):
        super().__init__()
        self.rebalance_days = 0
        self.rebalance_frequency = 20  # Rebalance every 20 days

    def on_data(self, data):
        self.rebalance_days += 1

        if self.rebalance_days < self.rebalance_frequency:
            return

        self.rebalance_days = 0

        # Calculate target weights
        targets = self.calculate_targets(data)

        # Rebalance to targets
        return self.rebalance_to_targets(targets)

    def calculate_targets(self, data):
        """Calculate target weights for each symbol"""
        # Example: Equal weight
        symbols = list(data.keys())
        weight = 1.0 / len(symbols)
        return {symbol: weight for symbol in symbols}

    def rebalance_to_targets(self, targets):
        """Generate orders to reach target weights"""
        orders = []
        equity = self.portfolio.total_equity()

        for symbol, target_weight in targets.items():
            target_value = equity * target_weight
            current_value = self.get_position_value(symbol)

            diff = target_value - current_value
            # Generate buy/sell orders based on diff
            # ...

        return orders
```

### Stop Loss and Take Profit

```python
class WithStops(Strategy):
    def __init__(self):
        super().__init__()
        self.stop_loss_pct = 0.02  # 2% stop loss
        self.take_profit_pct = 0.05  # 5% take profit

    def on_order_filled(self, order):
        """Set stops when position opened"""
        if order.side == OrderSide.BUY:
            position = self.portfolio.get_position(order.symbol)

            # Calculate stop and target prices
            stop_price = position.average_price * (1 - self.stop_loss_pct)
            target_price = position.average_price * (1 + self.take_profit_pct)

            # Store for checking on each bar
            self.set_parameter(f'{order.symbol}_stop', stop_price)
            self.set_parameter(f'{order.symbol}_target', target_price)

    def on_data(self, data):
        orders = []

        for symbol, df in data.items():
            if not self.portfolio.has_position(symbol):
                continue

            price = df['close'].iloc[-1]
            stop = self.get_parameter(f'{symbol}_stop')
            target = self.get_parameter(f'{symbol}_target')

            # Check stops
            if stop and price <= stop:
                self.log(f"Stop loss hit for {symbol}")
                orders.append(self.close_position(symbol))

            # Check target
            elif target and price >= target:
                self.log(f"Take profit hit for {symbol}")
                orders.append(self.close_position(symbol))

        return orders
```

## Testing Strategies

### Parameter Optimization

```python
# Test different parameter combinations
params = [
    {'short_ma': 10, 'long_ma': 30},
    {'short_ma': 20, 'long_ma': 50},
    {'short_ma': 30, 'long_ma': 100},
]

results = []

for param_set in params:
    strategy = MyStrategy(**param_set)

    engine = BacktestEngine(
        strategy=strategy,
        symbols=['AAPL'],
        start_date=start_date,
        end_date=end_date
    )

    result = engine.run()
    results.append({
        'params': param_set,
        'return': result.total_return,
        'sharpe': result.sharpe_ratio
    })

# Find best parameters
best = max(results, key=lambda x: x['sharpe'])
print(f"Best params: {best['params']}")
```

### Walk-Forward Analysis

```python
from datetime import datetime, timedelta

def walk_forward_test(strategy_class, symbols, start, end, train_period, test_period):
    """Perform walk-forward analysis"""
    current = start
    results = []

    while current < end:
        # Training period
        train_end = current + timedelta(days=train_period)

        # Test period
        test_start = train_end
        test_end = min(test_start + timedelta(days=test_period), end)

        # Optimize on training data
        optimized_params = optimize_parameters(
            strategy_class,
            symbols,
            current,
            train_end
        )

        # Test on out-of-sample data
        strategy = strategy_class(**optimized_params)
        engine = BacktestEngine(
            strategy=strategy,
            symbols=symbols,
            start_date=test_start,
            end_date=test_end
        )

        result = engine.run()
        results.append(result)

        current = test_end

    return results
```

## Best Practices

### 1. Avoid Overfitting

- Use simple strategies
- Test on out-of-sample data
- Don't over-optimize parameters
- Verify strategy logic makes sense

### 2. Handle Edge Cases

```python
def on_data(self, data):
    # Check data availability
    if 'AAPL' not in data:
        return

    df = data['AAPL']

    # Check sufficient data
    if len(df) < self.min_periods:
        return

    # Check for NaN values
    if df['close'].iloc[-1] != df['close'].iloc[-1]:  # NaN check
        return

    # Continue with strategy logic...
```

### 3. Maintain State Carefully

```python
class StatefulStrategy(Strategy):
    def on_start(self):
        # Initialize state variables
        self.trade_count = 0
        self.last_trade_date = None

    def on_order_filled(self, order):
        # Update state
        self.trade_count += 1
        self.last_trade_date = self.current_time
```

### 4. Log Important Events

```python
def on_data(self, data):
    # Log signals
    if buy_signal:
        self.log(f"BUY signal generated: {conditions}")

    # Log portfolio status periodically
    if self.current_time.day == 1:  # First of month
        self.log(f"Portfolio: {self.portfolio.summary()}")
```

## Common Mistakes

1. **Look-Ahead Bias**: Using future data
2. **Overfitting**: Too many parameters
3. **Ignoring Costs**: Not accounting for commissions/slippage
4. **Position Sizing**: Not managing position sizes
5. **No Risk Management**: Missing stops or limits

## Next Steps

- Review example strategies in `examples/`
- Read [Backtesting Guide](backtesting.md) for testing
- See [Live Trading Guide](live_trading.md) for deployment
- Join community for strategy ideas and feedback
