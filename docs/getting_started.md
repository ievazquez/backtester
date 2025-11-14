# Getting Started with Trading Platform

This guide will help you get up and running with the Trading Platform.

## Installation

### Prerequisites

- Python 3.8 or higher
- pip package manager

### Install from Source

```bash
git clone <repository-url>
cd backtester
pip install -e .
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

## Quick Start

### 1. Create Your First Strategy

```python
from trading_platform.core.strategy import Strategy
from trading_platform.utils.indicators import sma

class MyStrategy(Strategy):
    def __init__(self):
        super().__init__(name="MyStrategy")
        self.short_window = 20
        self.long_window = 50

    def on_data(self, data):
        # Get price data
        df = data['AAPL']

        # Calculate indicators
        short_ma = sma(df['close'], self.short_window)
        long_ma = sma(df['close'], self.long_window)

        # Trading logic
        if short_ma.iloc[-1] > long_ma.iloc[-1]:
            if not self.portfolio.has_position('AAPL'):
                return self.buy('AAPL', 100)
        else:
            if self.portfolio.has_position('AAPL'):
                return self.sell('AAPL', 100)
```

### 2. Run a Backtest

```python
from datetime import datetime
from trading_platform.backtesting.engine import BacktestEngine

# Create engine
engine = BacktestEngine(
    strategy=MyStrategy(),
    symbols=['AAPL'],
    start_date=datetime(2020, 1, 1),
    end_date=datetime(2023, 12, 31),
    initial_capital=100000
)

# Run backtest
results = engine.run()

# View results
print(results.summary())
results.plot_equity_curve()
```

### 3. Go Live (Paper Trading Recommended First!)

```python
from trading_platform.execution.engine import LiveTradingEngine
from trading_platform.brokers.interactive_brokers import InteractiveBrokersAdapter

# Connect to broker
broker = InteractiveBrokersAdapter(
    host='127.0.0.1',
    port=7497,  # Paper trading port
    client_id=1
)

# Create live engine
engine = LiveTradingEngine(
    strategy=MyStrategy(),
    broker=broker,
    symbols=['AAPL'],
    risk_manager_config={
        'max_position_size': 0.1,
        'max_daily_loss': 0.02
    }
)

# Start trading
engine.start()

# Stop when done (or use Ctrl+C)
# engine.stop()
```

## Project Structure

```
backtester/
├── trading_platform/     # Main package
│   ├── core/            # Core components
│   ├── backtesting/     # Backtesting engine
│   ├── data/            # Data management
│   ├── brokers/         # Broker integrations
│   ├── execution/       # Live trading
│   └── utils/           # Utilities
├── examples/            # Example strategies
├── docs/               # Documentation
└── tests/              # Unit tests
```

## Core Concepts

### 1. Strategy

The `Strategy` class is the foundation of all trading logic. Override these methods:

- `on_start()`: Called when strategy initializes
- `on_data(data)`: Called on each new data point (implement your logic here)
- `on_order_filled(order)`: Called when order executes
- `on_stop()`: Called when strategy stops

### 2. Portfolio

The `Portfolio` class manages:
- Cash balance
- Open positions
- Transaction history
- Performance tracking

### 3. Orders

Create orders using convenience methods:
- `self.buy(symbol, quantity)`: Market buy order
- `self.sell(symbol, quantity)`: Market sell order
- `self.close_position(symbol)`: Close existing position

### 4. Data

Historical data is provided as pandas DataFrames with columns:
- `open`: Opening price
- `high`: High price
- `low`: Low price
- `close`: Closing price
- `volume`: Trading volume

## Next Steps

- Read the [Backtesting Guide](backtesting.md) for detailed backtesting features
- Check out [Strategy Development](strategy_development.md) for advanced patterns
- Review [Live Trading Guide](live_trading.md) before going live
- Explore the `examples/` directory for complete implementations

## Support

- Documentation: See `docs/` directory
- Examples: See `examples/` directory
- Issues: Report on GitHub

## Safety Notice

**Important**: Always test strategies thoroughly in backtesting and paper trading before deploying with real capital. Trading involves substantial risk of loss.
