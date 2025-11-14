"""
Momentum Strategy Example

This example demonstrates a momentum-based trading strategy using
RSI and MACD indicators.
"""

from datetime import datetime
from trading_platform.core.strategy import Strategy
from trading_platform.backtesting.engine import BacktestEngine
from trading_platform.utils.indicators import rsi, macd


class MomentumStrategy(Strategy):
    """
    Momentum Strategy using RSI and MACD.

    Buy when:
    - RSI < 30 (oversold) and rising
    - MACD crosses above signal line

    Sell when:
    - RSI > 70 (overbought) and falling
    - MACD crosses below signal line
    """

    def __init__(
        self,
        rsi_period: int = 14,
        rsi_oversold: float = 30,
        rsi_overbought: float = 70,
        position_size_pct: float = 0.2  # 20% of portfolio per trade
    ):
        """
        Initialize strategy.

        Args:
            rsi_period: RSI calculation period
            rsi_oversold: RSI oversold threshold
            rsi_overbought: RSI overbought threshold
            position_size_pct: Position size as percentage of portfolio
        """
        super().__init__(name="MomentumStrategy")
        self.rsi_period = rsi_period
        self.rsi_oversold = rsi_oversold
        self.rsi_overbought = rsi_overbought
        self.position_size_pct = position_size_pct

    def on_start(self):
        """Called when strategy starts."""
        self.log(f"Starting Momentum Strategy")
        self.log(f"RSI: period={self.rsi_period}, oversold={self.rsi_oversold}, overbought={self.rsi_overbought}")

    def on_data(self, data):
        """
        Called on each new data point.

        Args:
            data: Dictionary of symbol -> DataFrame
        """
        orders = []

        for symbol in ['AAPL', 'GOOGL', 'MSFT']:
            if symbol not in data:
                continue

            df = data[symbol]

            # Need enough data
            if len(df) < 50:
                continue

            # Calculate indicators
            rsi_values = rsi(df['close'], self.rsi_period)
            macd_line, signal_line, histogram = macd(df['close'])

            # Get recent values
            current_rsi = rsi_values.iloc[-1]
            prev_rsi = rsi_values.iloc[-2]

            current_macd = macd_line.iloc[-1]
            prev_macd = macd_line.iloc[-2]
            current_signal = signal_line.iloc[-1]
            prev_signal = signal_line.iloc[-2]

            # Check for signals
            macd_bullish_cross = prev_macd <= prev_signal and current_macd > current_signal
            macd_bearish_cross = prev_macd >= prev_signal and current_macd < current_signal

            rsi_oversold = current_rsi < self.rsi_oversold and current_rsi > prev_rsi
            rsi_overbought = current_rsi > self.rsi_overbought and current_rsi < prev_rsi

            has_position = self.portfolio.has_position(symbol)
            current_price = df['close'].iloc[-1]

            # Calculate position size
            portfolio_value = self.portfolio.total_equity()
            position_value = portfolio_value * self.position_size_pct
            quantity = int(position_value / current_price)

            # Trading logic
            if (rsi_oversold or macd_bullish_cross) and not has_position and quantity > 0:
                # Buy signal
                order = self.buy(symbol, quantity)
                self.log(f"BUY {symbol}: {quantity} shares @ ${current_price:.2f} (RSI: {current_rsi:.2f})")
                orders.append(order)

            elif (rsi_overbought or macd_bearish_cross) and has_position:
                # Sell signal
                position = self.portfolio.get_position(symbol)
                if position:
                    order = self.sell(symbol, abs(position.quantity))
                    self.log(f"SELL {symbol}: {abs(position.quantity)} shares @ ${current_price:.2f} (RSI: {current_rsi:.2f})")
                    orders.append(order)

        return orders

    def on_order_filled(self, order):
        """Called when an order is filled."""
        position = self.portfolio.get_position(order.symbol)
        if position:
            self.log(f"Position updated: {position}")


def main():
    """Run the backtest."""
    # Create strategy
    strategy = MomentumStrategy(
        rsi_period=14,
        rsi_oversold=30,
        rsi_overbought=70,
        position_size_pct=0.15  # 15% per position
    )

    # Create backtest engine
    engine = BacktestEngine(
        strategy=strategy,
        symbols=['AAPL', 'GOOGL', 'MSFT'],
        start_date=datetime(2020, 1, 1),
        end_date=datetime(2023, 12, 31),
        initial_capital=100000,
        commission=0.001,
        slippage=0.0005,
    )

    # Run backtest
    print("Running backtest...")
    results = engine.run()

    # Print results
    print("\n" + engine.summary())
    print("\n" + results.summary())

    # Get trades
    trades_df = engine.get_orders_df()
    print("\nTrade History:")
    print(trades_df.to_string())

    # Plot results
    try:
        results.plot_equity_curve()
        results.plot_returns_distribution()
    except Exception as e:
        print(f"Could not plot results: {e}")


if __name__ == "__main__":
    main()
