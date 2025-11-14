"""
Multi-Asset Portfolio Strategy Example

This example demonstrates a diversified portfolio strategy that
trades across multiple asset classes with risk management.
"""

from datetime import datetime
from typing import Dict
import pandas as pd

from trading_platform.core.strategy import Strategy
from trading_platform.backtesting.engine import BacktestEngine
from trading_platform.utils.indicators import sma, atr


class MultiAssetStrategy(Strategy):
    """
    Multi-Asset Portfolio Strategy.

    Allocates capital across multiple assets based on momentum
    and volatility, with position sizing based on ATR.
    """

    def __init__(
        self,
        lookback_period: int = 50,
        rebalance_frequency: int = 20,  # days
        max_positions: int = 5,
        target_volatility: float = 0.15  # 15% annualized
    ):
        """
        Initialize strategy.

        Args:
            lookback_period: Period for momentum calculation
            rebalance_frequency: How often to rebalance (in days)
            max_positions: Maximum number of positions to hold
            target_volatility: Target portfolio volatility
        """
        super().__init__(name="MultiAssetStrategy")
        self.lookback_period = lookback_period
        self.rebalance_frequency = rebalance_frequency
        self.max_positions = max_positions
        self.target_volatility = target_volatility
        self.days_since_rebalance = 0

    def on_start(self):
        """Called when strategy starts."""
        self.log(f"Multi-Asset Strategy starting")
        self.log(f"Max positions: {self.max_positions}, Target vol: {self.target_volatility}")

    def on_data(self, data: Dict[str, pd.DataFrame]):
        """
        Called on each new data point.

        Args:
            data: Dictionary of symbol -> DataFrame
        """
        # Increment days counter
        self.days_since_rebalance += 1

        # Only rebalance at specified frequency
        if self.days_since_rebalance < self.rebalance_frequency:
            return

        # Reset counter
        self.days_since_rebalance = 0

        # Need enough data
        symbols_with_data = []
        for symbol, df in data.items():
            if len(df) >= self.lookback_period:
                symbols_with_data.append(symbol)

        if len(symbols_with_data) == 0:
            return

        # Calculate momentum and volatility for each symbol
        rankings = []

        for symbol in symbols_with_data:
            df = data[symbol]

            # Calculate momentum (return over lookback period)
            momentum = (df['close'].iloc[-1] / df['close'].iloc[-self.lookback_period] - 1) * 100

            # Calculate volatility (using ATR)
            atr_val = atr(df['high'], df['low'], df['close'], 20).iloc[-1]
            volatility = atr_val / df['close'].iloc[-1]  # Normalized ATR

            # Calculate moving average trend
            ma = sma(df['close'], 50).iloc[-1]
            above_ma = df['close'].iloc[-1] > ma

            rankings.append({
                'symbol': symbol,
                'momentum': momentum,
                'volatility': volatility,
                'above_ma': above_ma,
                'price': df['close'].iloc[-1]
            })

        # Sort by momentum (descending)
        rankings = sorted(rankings, key=lambda x: x['momentum'], reverse=True)

        # Filter: only consider stocks above their 50-day MA
        rankings = [r for r in rankings if r['above_ma']]

        # Select top N positions
        selected = rankings[:self.max_positions]

        if len(selected) == 0:
            # No valid positions, close all
            return self.close_all_positions()

        # Close positions not in selected list
        orders = []
        selected_symbols = {r['symbol'] for r in selected}

        for symbol in list(self.portfolio.positions.keys()):
            if symbol not in selected_symbols:
                order = self.close_position(symbol)
                if order:
                    self.log(f"Closing position: {symbol}")
                    orders.append(order)

        # Calculate position sizes based on volatility
        total_weight = 0
        for rank in selected:
            # Inverse volatility weighting
            rank['weight'] = 1.0 / rank['volatility']
            total_weight += rank['weight']

        # Normalize weights
        for rank in selected:
            rank['weight'] /= total_weight

        # Calculate target position sizes
        portfolio_value = self.portfolio.total_equity()

        for rank in selected:
            symbol = rank['symbol']
            target_value = portfolio_value * rank['weight']
            target_quantity = int(target_value / rank['price'])

            # Get current position
            current_quantity = self.get_position_quantity(symbol)

            # Calculate adjustment needed
            adjustment = target_quantity - current_quantity

            if abs(adjustment) > 0:
                if adjustment > 0:
                    order = self.buy(symbol, abs(adjustment))
                    self.log(f"BUY {symbol}: {abs(adjustment)} shares (weight: {rank['weight']*100:.1f}%)")
                else:
                    order = self.sell(symbol, abs(adjustment))
                    self.log(f"SELL {symbol}: {abs(adjustment)} shares")

                orders.append(order)

        return orders

    def on_stop(self):
        """Called when strategy stops."""
        self.log("Strategy stopped")
        self.log(f"Final portfolio: {self.portfolio.summary()}")


def main():
    """Run the backtest."""
    # Create strategy
    strategy = MultiAssetStrategy(
        lookback_period=60,
        rebalance_frequency=20,
        max_positions=5,
        target_volatility=0.15
    )

    # Portfolio of stocks, ETFs
    symbols = [
        'AAPL',   # Tech
        'GOOGL',  # Tech
        'JPM',    # Finance
        'XOM',    # Energy
        'JNJ',    # Healthcare
        'GLD',    # Gold ETF
        'TLT',    # Treasury ETF
    ]

    # Create backtest engine
    engine = BacktestEngine(
        strategy=strategy,
        symbols=symbols,
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

    # Print portfolio composition
    print("\nFinal Portfolio Positions:")
    for symbol, position in engine.portfolio.positions.items():
        print(f"  {symbol}: {position}")

    # Plot results
    try:
        results.plot_equity_curve()
    except Exception as e:
        print(f"Could not plot results: {e}")


if __name__ == "__main__":
    main()
