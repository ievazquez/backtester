"""Portfolio management for the trading platform."""

from typing import Dict, List, Optional
from datetime import datetime
import pandas as pd

from trading_platform.core.position import Position
from trading_platform.core.order import Order, OrderSide


class Portfolio:
    """
    Manages portfolio positions, cash, and performance tracking.

    Attributes:
        initial_capital: Starting capital
        cash: Current available cash
        positions: Dictionary of positions by symbol
        closed_positions: List of closed positions for analysis
        orders: List of all orders
        equity_curve: Historical equity values
    """

    def __init__(self, initial_capital: float = 100000.0):
        """
        Initialize portfolio.

        Args:
            initial_capital: Starting capital
        """
        if initial_capital <= 0:
            raise ValueError("Initial capital must be positive")

        self.initial_capital = initial_capital
        self.cash = initial_capital
        self.positions: Dict[str, Position] = {}
        self.closed_positions: List[Position] = []
        self.orders: List[Order] = []
        self.equity_curve: List[Dict] = []
        self._transactions: List[Dict] = []

    def update_position(
        self,
        symbol: str,
        quantity: float,
        price: float,
        commission: float = 0.0,
        timestamp: Optional[datetime] = None,
    ) -> None:
        """
        Update a position with a new trade.

        Args:
            symbol: Trading symbol
            quantity: Trade quantity (positive for buy, negative for sell)
            price: Trade price
            commission: Commission paid
            timestamp: Trade timestamp
        """
        # Create position if it doesn't exist
        if symbol not in self.positions:
            self.positions[symbol] = Position(symbol=symbol)

        position = self.positions[symbol]

        # Update cash
        cash_flow = -quantity * price - commission
        self.cash += cash_flow

        # Update position
        position.update(quantity, price, commission)

        # Record transaction
        self._transactions.append({
            'timestamp': timestamp or datetime.now(),
            'symbol': symbol,
            'quantity': quantity,
            'price': price,
            'commission': commission,
            'cash_flow': cash_flow
        })

        # If position is closed, move to closed_positions
        if position.is_closed() and position.trades:
            self.closed_positions.append(position)
            del self.positions[symbol]

    def update_prices(self, prices: Dict[str, float], timestamp: Optional[datetime] = None) -> None:
        """
        Update current prices for all positions.

        Args:
            prices: Dictionary of symbol -> price
            timestamp: Update timestamp
        """
        for symbol, position in self.positions.items():
            if symbol in prices:
                position.current_price = prices[symbol]

        # Record equity curve
        self.equity_curve.append({
            'timestamp': timestamp or datetime.now(),
            'equity': self.total_equity(),
            'cash': self.cash,
            'positions_value': self.positions_value()
        })

    def has_position(self, symbol: str) -> bool:
        """
        Check if portfolio has a position in a symbol.

        Args:
            symbol: Trading symbol

        Returns:
            True if position exists and is open
        """
        return symbol in self.positions and not self.positions[symbol].is_closed()

    def get_position(self, symbol: str) -> Optional[Position]:
        """
        Get position for a symbol.

        Args:
            symbol: Trading symbol

        Returns:
            Position if it exists, None otherwise
        """
        return self.positions.get(symbol)

    def positions_value(self) -> float:
        """
        Calculate total market value of all positions.

        Returns:
            Total positions value
        """
        return sum(pos.market_value() for pos in self.positions.values())

    def total_equity(self) -> float:
        """
        Calculate total portfolio equity.

        Returns:
            Total equity (cash + positions value)
        """
        return self.cash + self.positions_value()

    def unrealized_pnl(self) -> float:
        """
        Calculate total unrealized profit/loss.

        Returns:
            Total unrealized P&L
        """
        return sum(pos.unrealized_pnl() for pos in self.positions.values())

    def realized_pnl(self) -> float:
        """
        Calculate total realized profit/loss.

        Returns:
            Total realized P&L (from both open and closed positions)
        """
        open_realized = sum(pos.realized_pnl for pos in self.positions.values())
        closed_realized = sum(pos.realized_pnl for pos in self.closed_positions)
        return open_realized + closed_realized

    def total_pnl(self) -> float:
        """
        Calculate total profit/loss.

        Returns:
            Total P&L (realized + unrealized)
        """
        return self.realized_pnl() + self.unrealized_pnl()

    def total_return(self) -> float:
        """
        Calculate total return as percentage.

        Returns:
            Total return percentage
        """
        return ((self.total_equity() - self.initial_capital) / self.initial_capital) * 100

    def get_equity_curve_df(self) -> pd.DataFrame:
        """
        Get equity curve as a DataFrame.

        Returns:
            DataFrame with equity curve data
        """
        if not self.equity_curve:
            return pd.DataFrame()

        df = pd.DataFrame(self.equity_curve)
        if 'timestamp' in df.columns:
            df.set_index('timestamp', inplace=True)
        return df

    def get_transactions_df(self) -> pd.DataFrame:
        """
        Get all transactions as a DataFrame.

        Returns:
            DataFrame with transaction data
        """
        if not self._transactions:
            return pd.DataFrame()

        df = pd.DataFrame(self._transactions)
        if 'timestamp' in df.columns:
            df.set_index('timestamp', inplace=True)
        return df

    def summary(self) -> Dict:
        """
        Get portfolio summary statistics.

        Returns:
            Dictionary with summary statistics
        """
        return {
            'initial_capital': self.initial_capital,
            'cash': self.cash,
            'positions_value': self.positions_value(),
            'total_equity': self.total_equity(),
            'unrealized_pnl': self.unrealized_pnl(),
            'realized_pnl': self.realized_pnl(),
            'total_pnl': self.total_pnl(),
            'total_return_pct': self.total_return(),
            'num_open_positions': len(self.positions),
            'num_closed_positions': len(self.closed_positions),
            'num_transactions': len(self._transactions)
        }

    def __repr__(self) -> str:
        """String representation of the portfolio."""
        return (
            f"Portfolio(equity={self.total_equity():.2f}, cash={self.cash:.2f}, "
            f"positions={len(self.positions)}, return={self.total_return():.2f}%)"
        )
