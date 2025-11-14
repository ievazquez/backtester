# Live Trading Guide

Guide to deploying strategies for live trading with proper risk management.

## Safety First

**IMPORTANT WARNINGS:**

1. **Always start with paper trading** (simulated trading with fake money)
2. **Test thoroughly** in backtesting before going live
3. **Start small** - use small position sizes initially
4. **Monitor closely** - especially in the first days
5. **Have kill switches** - know how to stop the system
6. **Understand the risks** - you can lose money

## Supported Brokers

### Interactive Brokers

```python
from trading_platform.brokers.interactive_brokers import InteractiveBrokersAdapter

broker = InteractiveBrokersAdapter(
    host='127.0.0.1',
    port=7497,  # 7497=paper, 7496=live TWS, 4002=live Gateway
    client_id=1
)
```

**Prerequisites:**
- Install IB TWS or IB Gateway
- Enable API connections in settings
- Install ibapi: `pip install ibapi`

### OANDA

```python
from trading_platform.brokers.oanda import OANDAAdapter

broker = OANDAAdapter(
    api_token='YOUR_API_TOKEN',
    account_id='YOUR_ACCOUNT_ID',
    environment='practice'  # or 'live'
)
```

**Prerequisites:**
- Create OANDA account
- Generate API token
- Install oandapyV20: `pip install oandapyV20`

### Darwinex

```python
from trading_platform.brokers.darwinex import DarwinexAdapter

broker = DarwinexAdapter(
    account_id='YOUR_MT5_ACCOUNT',
    password='YOUR_PASSWORD',
    server='Darwinex-Demo'  # or 'Darwinex-Live'
)
```

**Prerequisites:**
- Create Darwinex account
- Install MetaTrader 5: `pip install MetaTrader5`

## Basic Live Trading

### 1. Setup

```python
from trading_platform.execution.engine import LiveTradingEngine
from trading_platform.brokers.interactive_brokers import InteractiveBrokersAdapter
from my_strategy import MyStrategy

# Create broker connection
broker = InteractiveBrokersAdapter(
    host='127.0.0.1',
    port=7497,  # Paper trading
    client_id=1
)

# Create strategy
strategy = MyStrategy()

# Create live engine
engine = LiveTradingEngine(
    strategy=strategy,
    broker=broker,
    symbols=['AAPL', 'GOOGL'],
    update_interval=1.0  # Update every second
)
```

### 2. Risk Management

```python
# Configure risk management
risk_config = {
    'max_position_size': 0.1,      # Max 10% per position
    'max_portfolio_risk': 0.02,    # Max 2% risk per trade
    'max_daily_loss': 0.05,        # Max 5% daily loss
    'max_total_exposure': 1.0,     # Max 100% exposure
    'enable_stops': True           # Enable automatic stops
}

engine = LiveTradingEngine(
    strategy=strategy,
    broker=broker,
    symbols=['AAPL'],
    risk_manager_config=risk_config
)
```

### 3. Start Trading

```python
# Start live trading
engine.start()

# Trading loop will run in background thread
# Press Ctrl+C to stop, or call:
# engine.stop()
```

## Risk Management

### Position Sizing

The risk manager automatically validates orders:

```python
# This order may be rejected if it violates risk rules
order = self.buy('AAPL', 1000)  # Might be too large

# Better: Let risk manager calculate size
from trading_platform.execution.risk_manager import RiskManager

risk_mgr = RiskManager(max_position_size=0.1)
size = risk_mgr.calculate_position_size(
    symbol='AAPL',
    portfolio=self.portfolio,
    current_price=current_price,
    stop_loss_price=stop_price  # Optional
)

order = self.buy('AAPL', size)
```

### Daily Loss Limits

```python
# Engine automatically tracks daily P&L
# Trading stops if max_daily_loss is hit

# Check current daily P&L
status = engine.get_status()
risk_summary = status['risk_manager']
print(risk_summary['daily_pnl'])
```

### Position Limits

```python
risk_config = {
    'max_position_size': 0.1,  # No position > 10% of portfolio
    'max_total_exposure': 0.8, # Total positions < 80% of portfolio
}
```

## Order Management

### Order Types

```python
# Market order (default)
order = self.buy('AAPL', 100)

# Limit order
from trading_platform.core.order import OrderType

order = self.buy(
    'AAPL',
    100,
    order_type=OrderType.LIMIT,
    limit_price=150.00
)

# Stop order
order = self.sell(
    'AAPL',
    100,
    order_type=OrderType.STOP,
    stop_price=145.00
)
```

### Order Callbacks

```python
class MyStrategy(Strategy):
    def on_order_filled(self, order):
        """Called when order fills"""
        print(f"Order filled: {order}")

        # Update stop loss
        position = self.portfolio.get_position(order.symbol)
        if position:
            stop_price = position.average_price * 0.98  # 2% stop
            # Place stop order...

    def on_order_cancelled(self, order):
        """Called when order cancelled"""
        print(f"Order cancelled: {order}")
        # Handle cancellation...
```

### Manual Order Control

```python
# Get order manager
order_mgr = engine.order_manager

# Get pending orders
pending = order_mgr.get_pending_orders()

# Cancel specific order
order_mgr.cancel_order(order_id)

# Get order status
order = order_mgr.get_order(order_id)
print(order.status)
```

## Monitoring

### Real-Time Status

```python
import time

engine.start()

# Monitor in loop
while True:
    status = engine.get_status()

    portfolio = status['portfolio']
    print(f"Equity: ${portfolio['total_equity']:,.2f}")
    print(f"P&L: ${portfolio['total_pnl']:,.2f}")
    print(f"Open Positions: {portfolio['num_open_positions']}")

    time.sleep(60)  # Update every minute
```

### Logging

```python
class MyStrategy(Strategy):
    def on_data(self, data):
        # Log important events
        self.log(f"Processing data at {self.current_time}")

        # Log trades
        if trade_signal:
            self.log(f"Trade signal: BUY {symbol}")
```

### Alerts

```python
def on_order_filled(self, order):
    # Send email/SMS alert (implement with your provider)
    send_alert(f"Order filled: {order}")

def on_data(self, data):
    # Check for large drawdown
    pnl_pct = (self.portfolio.total_pnl() /
               self.portfolio.initial_capital) * 100

    if pnl_pct < -5:
        send_alert(f"WARNING: Drawdown {pnl_pct:.2f}%")
```

## Best Practices

### 1. Gradual Deployment

```python
# Phase 1: Backtest
backtest_engine = BacktestEngine(...)
results = backtest_engine.run()

# Phase 2: Paper trade for 2-4 weeks
paper_engine = LiveTradingEngine(
    strategy=strategy,
    broker=paper_broker,  # Paper trading
    symbols=symbols
)
paper_engine.start()

# Phase 3: Live with small size
live_engine = LiveTradingEngine(
    strategy=strategy,
    broker=live_broker,
    symbols=symbols[:1],  # Start with 1 symbol
    risk_manager_config={
        'max_position_size': 0.05  # Start small
    }
)
```

### 2. Connection Handling

```python
# Check connection before starting
if not broker.is_connected():
    broker.connect()

if not broker.is_connected():
    raise RuntimeError("Failed to connect to broker")

# Periodic connection check
def check_connection():
    if not broker.is_connected():
        print("Connection lost! Attempting reconnect...")
        broker.connect()
```

### 3. Error Handling

```python
class RobustStrategy(Strategy):
    def on_data(self, data):
        try:
            # Your strategy logic
            ...
        except Exception as e:
            self.log(f"Error in strategy: {e}")
            # Don't crash - log and continue

    def on_order_filled(self, order):
        try:
            # Handle fill
            ...
        except Exception as e:
            self.log(f"Error handling fill: {e}")
```

### 4. Graceful Shutdown

```python
import signal

def signal_handler(sig, frame):
    print('\nShutting down gracefully...')
    engine.stop()
    broker.disconnect()
    exit(0)

signal.signal(signal.SIGINT, signal_handler)

engine.start()
```

## Troubleshooting

### Connection Issues

```python
# IB: Check TWS/Gateway is running
# OANDA: Verify API token and account ID
# All: Check firewall settings

# Test connection
if broker.connect():
    print("Connected successfully")
    balance = broker.get_account_balance()
    print(f"Account balance: ${balance:,.2f}")
else:
    print("Connection failed")
```

### Order Rejections

```python
# Check account balance
balance = broker.get_account_balance()
print(f"Available cash: ${balance:,.2f}")

# Check position limits
equity = broker.get_account_equity()
max_position_value = equity * 0.1  # 10% limit
order_value = quantity * price

if order_value > max_position_value:
    print("Order exceeds position limit")
```

### Data Issues

```python
# Verify market data subscription
price = broker.get_latest_price('AAPL')
if price == 0:
    print("No market data for AAPL")
```

## Kill Switches

Always have multiple ways to stop trading:

1. **Keyboard**: Ctrl+C
2. **Code**: `engine.stop()`
3. **Broker**: Manual intervention through broker platform
4. **System**: Kill the Python process

```python
# Emergency stop function
def emergency_stop():
    """Stop everything immediately"""
    engine.stop()

    # Cancel all pending orders
    for order in engine.order_manager.get_pending_orders():
        engine.order_manager.cancel_order(order.order_id)

    # Close all positions (if desired)
    # strategy.close_all_positions()

    broker.disconnect()
```

## Disclaimer

Live trading involves substantial risk of loss. This platform is provided as-is without any warranties. Always:

- Test thoroughly before going live
- Start with paper trading
- Use proper risk management
- Never risk more than you can afford to lose
- Understand all risks involved

See `examples/` for complete working examples.
