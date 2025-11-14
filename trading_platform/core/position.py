"""Position management for the trading platform."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional


@dataclass
class Position:
    """
    Represents a trading position in a security.

    Attributes:
        symbol: Trading symbol/ticker
        quantity: Current position quantity (positive for long, negative for short)
        average_price: Average entry price
        current_price: Current market price
        opened_at: Position open timestamp
        closed_at: Position close timestamp (if closed)
        realized_pnl: Realized profit/loss
        commissions: Total commissions paid
        trades: List of trade records for this position
    """

    symbol: str
    quantity: float = 0.0
    average_price: float = 0.0
    current_price: float = 0.0
    opened_at: Optional[datetime] = None
    closed_at: Optional[datetime] = None
    realized_pnl: float = 0.0
    commissions: float = 0.0
    trades: List[dict] = field(default_factory=list)

    def update(self, quantity: float, price: float, commission: float = 0.0) -> None:
        """
        Update position with a new trade.

        Args:
            quantity: Trade quantity (positive for buy, negative for sell)
            price: Trade price
            commission: Commission paid
        """
        timestamp = datetime.now()

        # Record the trade
        self.trades.append({
            'timestamp': timestamp,
            'quantity': quantity,
            'price': price,
            'commission': commission
        })

        # Update commissions
        self.commissions += commission

        # Calculate new position
        old_quantity = self.quantity
        new_quantity = old_quantity + quantity

        # Opening or adding to position
        if old_quantity == 0:
            # Opening new position
            self.quantity = quantity
            self.average_price = price
            self.opened_at = timestamp
        elif (old_quantity > 0 and quantity > 0) or (old_quantity < 0 and quantity < 0):
            # Adding to existing position (same direction)
            total_cost = abs(old_quantity) * self.average_price + abs(quantity) * price
            self.quantity = new_quantity
            self.average_price = total_cost / abs(self.quantity)
        else:
            # Reducing or closing position (opposite direction)
            quantity_closed = min(abs(old_quantity), abs(quantity))

            # Calculate realized P&L
            if old_quantity > 0:  # Long position being reduced/closed
                pnl = quantity_closed * (price - self.average_price)
            else:  # Short position being reduced/closed
                pnl = quantity_closed * (self.average_price - price)

            self.realized_pnl += pnl - commission

            # Update quantity
            self.quantity = new_quantity

            # If position is closed
            if abs(new_quantity) < 1e-10:
                self.quantity = 0.0
                self.closed_at = timestamp
            # If position reversed
            elif (old_quantity > 0 and new_quantity < 0) or (old_quantity < 0 and new_quantity > 0):
                self.average_price = price
                self.opened_at = timestamp

    def unrealized_pnl(self) -> float:
        """
        Calculate unrealized profit/loss at current price.

        Returns:
            Unrealized P&L
        """
        if self.quantity == 0:
            return 0.0

        if self.quantity > 0:  # Long position
            return self.quantity * (self.current_price - self.average_price)
        else:  # Short position
            return abs(self.quantity) * (self.average_price - self.current_price)

    def total_pnl(self) -> float:
        """
        Calculate total profit/loss (realized + unrealized).

        Returns:
            Total P&L
        """
        return self.realized_pnl + self.unrealized_pnl() - self.commissions

    def market_value(self) -> float:
        """
        Calculate current market value of the position.

        Returns:
            Market value
        """
        return abs(self.quantity) * self.current_price

    def cost_basis(self) -> float:
        """
        Calculate cost basis of the position.

        Returns:
            Cost basis
        """
        return abs(self.quantity) * self.average_price

    def is_long(self) -> bool:
        """Check if position is long."""
        return self.quantity > 0

    def is_short(self) -> bool:
        """Check if position is short."""
        return self.quantity < 0

    def is_closed(self) -> bool:
        """Check if position is closed."""
        return abs(self.quantity) < 1e-10

    def return_pct(self) -> float:
        """
        Calculate return percentage.

        Returns:
            Return as percentage
        """
        if self.cost_basis() == 0:
            return 0.0

        return (self.total_pnl() / self.cost_basis()) * 100

    def __repr__(self) -> str:
        """String representation of the position."""
        direction = "LONG" if self.is_long() else "SHORT" if self.is_short() else "CLOSED"
        return (
            f"Position({direction} {abs(self.quantity)} {self.symbol} "
            f"@ {self.average_price:.2f}, P&L: {self.total_pnl():.2f})"
        )
