"""
Inline strategy example for --algotext option.

This demonstrates how to pass a strategy directly as text.
"""

INLINE_STRATEGY = '''
from trading_platform.core.strategy import Strategy
from trading_platform.utils.indicators import rsi

class InlineStrategy(Strategy):
    def __init__(self):
        super().__init__(name="InlineStrategy")
        self.rsi_period = 14

    def on_data(self, data):
        orders = []
        for symbol, df in data.items():
            if len(df) < self.rsi_period + 5:
                continue

            rsi_val = rsi(df['close'], self.rsi_period)
            current_rsi = rsi_val.iloc[-1]

            has_position = self.portfolio.has_position(symbol)

            if current_rsi < 30 and not has_position:
                orders.append(self.buy(symbol, 100))
            elif current_rsi > 70 and has_position:
                orders.append(self.close_position(symbol))

        return orders
'''


if __name__ == '__main__':
    print("Copy and paste the following for --algotext option:")
    print()
    print(INLINE_STRATEGY)
