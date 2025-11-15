"""
Example strategy for CLI testing.

This is a simple moving average crossover strategy that can be run
from the command line.
"""

from trading_platform.core.strategy import Strategy
from trading_platform.utils.indicators import sma


class CLITestStrategy(Strategy):
    """
    Simple MA Crossover Strategy for CLI testing.

    Parameters:
        short_window: Short-term MA period (default: 20)
        long_window: Long-term MA period (default: 50)
    """

    def __init__(self, short_window=20, long_window=50):
        super().__init__(name="CLITestStrategy")
        self.short_window = short_window
        self.long_window = long_window

    def on_start(self):
        """Called when strategy starts."""
        self.log(f"Strategy starting with MA periods: {self.short_window}/{self.long_window}")

    def on_data(self, data):
        """Main strategy logic."""
        orders = []

        for symbol, df in data.items():
            # Need enough data
            if len(df) < self.long_window:
                continue

            # Calculate indicators
            short_ma = sma(df['close'], self.short_window)
            long_ma = sma(df['close'], self.long_window)

            # Get current and previous values
            curr_short = short_ma.iloc[-1]
            curr_long = long_ma.iloc[-1]
            prev_short = short_ma.iloc[-2]
            prev_long = long_ma.iloc[-2]

            # Detect crossovers
            bullish_cross = prev_short <= prev_long and curr_short > curr_long
            bearish_cross = prev_short >= prev_long and curr_short < curr_long

            has_position = self.portfolio.has_position(symbol)
            current_price = df['close'].iloc[-1]

            # Calculate position size (10% of portfolio)
            equity = self.portfolio.total_equity()
            position_value = equity * 0.10
            quantity = int(position_value / current_price)

            # Trading logic
            if bullish_cross and not has_position and quantity > 0:
                self.log(f"BUY signal: {symbol} @ ${current_price:.2f}")
                orders.append(self.buy(symbol, quantity))

            elif bearish_cross and has_position:
                position = self.portfolio.get_position(symbol)
                if position:
                    self.log(f"SELL signal: {symbol} @ ${current_price:.2f}")
                    orders.append(self.sell(symbol, abs(position.quantity)))

        return orders

    def on_order_filled(self, order):
        """Called when order fills."""
        self.log(f"Order filled: {order.side.value} {order.quantity} {order.symbol}")

    def on_stop(self):
        """Called when strategy stops."""
        self.log("Strategy completed")
        summary = self.portfolio.summary()
        self.log(f"Final equity: ${summary['total_equity']:,.2f}")
        self.log(f"Total return: {summary['total_return_pct']:.2f}%")
