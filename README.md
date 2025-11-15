# Trading Platform

A comprehensive Python-based trading platform for quantitative traders and technical analysis researchers.

**QuantLine CLI**: Zipline-inspired command-line interface for backtesting and live trading.

## Features

### 1. Backtesting Engine (Priority 1)
- **Historical Data Support**: Seamless integration with multiple data providers
- **Event-Driven Architecture**: Realistic simulation of market conditions
- **Performance Metrics**: Comprehensive analytics including Sharpe ratio, drawdown, returns
- **Multi-Timeframe Support**: Test strategies across different timeframes
- **Multi-Asset Support**: Stocks, forex, cryptocurrencies, and commodities

### 2. Live Trading Execution (Priority 2)
- **Broker Integration**: Interactive Brokers, OANDA, and Darwinex
- **Real-Time Order Management**: Fast, reliable order execution
- **Position Tracking**: Real-time portfolio monitoring
- **Risk Controls**: Built-in risk management and safeguards

### 3. Strategy Development Interface (Priority 3)
- **Intuitive API**: Easy-to-use strategy development framework
- **Multi-Language Support**: Python, C#, and F# (Python implemented first)
- **Parameter Optimization**: Built-in tools for strategy optimization
- **Extensive Documentation**: Guides for both novice and advanced traders

## Installation

```bash
pip install -e .
```

## Quick Start

### Command Line Interface (Zipline-style)

Run a backtest from the command line:

```bash
# Basic backtest
python -m trading_platform.quantline run \
  -f examples/cli_test_strategy.py \
  -s 2020-01-01 \
  -e 2023-12-31 \
  --symbols AAPL \
  --capital-base 100000

# Multiple symbols with output
python -m trading_platform.quantline run \
  -f examples/momentum_strategy.py \
  -s 2020-01-01 \
  -e 2023-12-31 \
  --symbols AAPL,GOOGL,MSFT \
  --capital-base 100000 \
  -o results.txt \
  --plot
```

See [COMMAND_LINE_EXAMPLES.md](COMMAND_LINE_EXAMPLES.md) for more CLI examples.

### Python API - Backtesting Example

```python
from trading_platform.core.strategy import Strategy
from trading_platform.backtesting.engine import BacktestEngine
from trading_platform.data.providers import YahooFinanceProvider
import pandas as pd

class SimpleMAStrategy(Strategy):
    def __init__(self, short_window=20, long_window=50):
        super().__init__()
        self.short_window = short_window
        self.long_window = long_window

    def on_data(self, data):
        # Calculate moving averages
        short_ma = data['close'].rolling(self.short_window).mean()
        long_ma = data['close'].rolling(self.long_window).mean()

        # Generate signals
        if short_ma.iloc[-1] > long_ma.iloc[-1] and not self.portfolio.has_position('AAPL'):
            self.buy('AAPL', 100)
        elif short_ma.iloc[-1] < long_ma.iloc[-1] and self.portfolio.has_position('AAPL'):
            self.sell('AAPL', 100)

# Run backtest
engine = BacktestEngine(
    strategy=SimpleMAStrategy(),
    symbols=['AAPL'],
    start_date='2020-01-01',
    end_date='2023-12-31',
    initial_capital=100000
)

results = engine.run()
print(results.summary())
```

### Live Trading Example

```python
from trading_platform.execution.engine import LiveTradingEngine
from trading_platform.brokers.interactive_brokers import InteractiveBrokersAdapter

# Initialize broker connection
broker = InteractiveBrokersAdapter(
    host='127.0.0.1',
    port=7497,
    client_id=1
)

# Initialize live trading engine
engine = LiveTradingEngine(
    strategy=SimpleMAStrategy(),
    broker=broker,
    symbols=['AAPL'],
    risk_manager_config={
        'max_position_size': 0.1,  # 10% of portfolio
        'max_daily_loss': 0.02      # 2% daily loss limit
    }
)

# Start live trading
engine.start()
```

## Architecture

The platform follows a modular, event-driven architecture:

- **Core**: Base classes for strategies, portfolios, orders, and positions
- **Backtesting**: Event-driven backtesting engine with historical data simulation
- **Data**: Data providers and management for historical and live data
- **Brokers**: Adapter pattern for multiple broker integrations
- **Execution**: Live trading engine with order and risk management
- **Utils**: Technical indicators and helper functions

## Supported Brokers

- **Interactive Brokers**: Full support for stocks, options, futures, forex
- **OANDA**: Forex and CFD trading
- **Darwinex**: Forex trading with strategy sharing capabilities

## Supported Data Providers

- **Primary**: Yahoo Finance, Alpha Vantage, Interactive Brokers
- **Crypto**: Binance, Coinbase, Kraken
- **Forex**: OANDA, Darwinex
- **Others**: Quandl, IEX Cloud

## Documentation

- [COMMAND_LINE_EXAMPLES.md](COMMAND_LINE_EXAMPLES.md) - 🇪🇸 Ejemplos CLI en español
- [QUICKSTART_CLI.md](QUICKSTART_CLI.md) - CLI Quick Start Guide
- [CLI_EXAMPLES.md](CLI_EXAMPLES.md) - Advanced CLI Examples
- [Getting Started](docs/getting_started.md) - Getting started with Python API
- [Backtesting Guide](docs/backtesting.md) - Detailed backtesting guide
- [Live Trading Guide](docs/live_trading.md) - Live trading deployment
- [Strategy Development](docs/strategy_development.md) - Strategy patterns

## Examples

See the `examples/` directory for complete strategy implementations:

- `cli_test_strategy.py`: Simple MA crossover for CLI
- `simple_ma_crossover.py`: Moving average crossover strategy
- `momentum_strategy.py`: Momentum-based trading strategy
- `multi_asset_strategy.py`: Portfolio strategy across multiple assets

## CLI Usage

```bash
# Get help
python -m trading_platform.quantline --help

# Backtest help
python -m trading_platform.quantline run --help

# Live trading help
python -m trading_platform.quantline live --help
```

## Testing

```bash
pytest tests/
```

## License

MIT License

## Contributing

Contributions welcome! Please read our contributing guidelines before submitting PRs.

## Disclaimer

This software is for educational and research purposes only. Trading involves substantial risk of loss. Use at your own risk.
