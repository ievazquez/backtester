"""
Simple Moving Average Crossover Strategy Example

This example demonstrates a basic trend-following strategy using
moving average crossovers.
"""

from datetime import datetime
from trading_platform.core.strategy import Strategy
from trading_platform.backtesting.engine import BacktestEngine
from trading_platform.utils.indicators import sma


class SimpleMAStrategy(Strategy):
    """
    Simple Moving Average Crossover Strategy.

    Buy when short-term MA crosses above long-term MA.
    Sell when short-term MA crosses below long-term MA.
    """

    def __init__(self, short_window: int = 20, long_window: int = 50):
        """
        Initialize strategy.

        Args:
            short_window: Short-term moving average period
            long_window: Long-term moving average period
        """
        super().__init__(name="SimpleMAStrategy")
        self.short_window = short_window
        self.long_window = long_window
        self.position_size = 100  # shares per trade

    def on_start(self):
        """Called when strategy starts."""
        self.log(f"Starting with short_window={self.short_window}, long_window={self.long_window}")

    def on_data(self, data):
        """
        Called on each new data point.

        Args:
            data: Dictionary of symbol -> DataFrame
        """
        # Get data for AAPL
        if 'AAPL' not in data:
            return

        df = data['AAPL']

        # Need enough data for indicators
        if len(df) < self.long_window:
            return

        # Calculate moving averages
        short_ma = sma(df['close'], self.short_window)
        long_ma = sma(df['close'], self.long_window)

        # Get latest values
        current_short = short_ma.iloc[-1]
        current_long = long_ma.iloc[-1]
        prev_short = short_ma.iloc[-2]
        prev_long = long_ma.iloc[-2]

        # Check for crossover
        bullish_cross = prev_short <= prev_long and current_short > current_long
        bearish_cross = prev_short >= prev_long and current_short < current_long

        # Trading logic
        has_position = self.portfolio.has_position('AAPL')

        if bullish_cross and not has_position:
            # Buy signal
            order = self.buy('AAPL', self.position_size)
            self.log(f"BUY signal: {self.position_size} shares @ ${df['close'].iloc[-1]:.2f}")
            return order

        elif bearish_cross and has_position:
            # Sell signal
            order = self.sell('AAPL', self.position_size)
            self.log(f"SELL signal: {self.position_size} shares @ ${df['close'].iloc[-1]:.2f}")
            return order

    def on_order_filled(self, order):
        """Called when an order is filled."""
        self.log(f"Order filled: {order.side.value} {order.quantity} {order.symbol}")


def main():
    """Run the backtest."""
    # Create strategy
    strategy = SimpleMAStrategy(short_window=20, long_window=50)

    # Create backtest engine
    engine = BacktestEngine(
        strategy=strategy,
        symbols=['AAPL'],
        start_date=datetime(2020, 1, 1),
        end_date=datetime(2023, 12, 31),
        initial_capital=100000,
        commission=0.001,  # 0.1% commission
        slippage=0.0005,   # 0.05% slippage
    )

    # Run backtest
    print("Running backtest...")
    results = engine.run()

    # Print results
    print("\n" + engine.summary())
    print("\n" + results.summary())

    # Plot results
    try:
        results.plot_equity_curve()
    except Exception as e:
        print(f"Could not plot results: {e}")


if __name__ == "__main__":
    main()
