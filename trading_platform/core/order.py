"""Order management classes for the trading platform."""

from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
import uuid


class OrderType(Enum):
    """Order types supported by the platform."""
    MARKET = "MARKET"
    LIMIT = "LIMIT"
    STOP = "STOP"
    STOP_LIMIT = "STOP_LIMIT"


class OrderSide(Enum):
    """Order side (buy or sell)."""
    BUY = "BUY"
    SELL = "SELL"


class OrderStatus(Enum):
    """Order status."""
    PENDING = "PENDING"
    SUBMITTED = "SUBMITTED"
    FILLED = "FILLED"
    PARTIALLY_FILLED = "PARTIALLY_FILLED"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"


@dataclass
class Order:
    """
    Represents a trading order.

    Attributes:
        symbol: Trading symbol/ticker
        side: Buy or sell
        quantity: Number of units to trade
        order_type: Type of order (market, limit, etc.)
        limit_price: Limit price for limit orders
        stop_price: Stop price for stop orders
        time_in_force: Time in force (DAY, GTC, etc.)
        order_id: Unique order identifier
        created_at: Order creation timestamp
        filled_at: Order fill timestamp
        status: Current order status
        filled_quantity: Quantity that has been filled
        average_fill_price: Average price at which order was filled
    """

    symbol: str
    side: OrderSide
    quantity: float
    order_type: OrderType = OrderType.MARKET
    limit_price: Optional[float] = None
    stop_price: Optional[float] = None
    time_in_force: str = "DAY"
    order_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: datetime = field(default_factory=datetime.now)
    filled_at: Optional[datetime] = None
    status: OrderStatus = OrderStatus.PENDING
    filled_quantity: float = 0.0
    average_fill_price: Optional[float] = None

    def __post_init__(self):
        """Validate order parameters."""
        if self.quantity <= 0:
            raise ValueError("Order quantity must be positive")

        if self.order_type == OrderType.LIMIT and self.limit_price is None:
            raise ValueError("Limit price required for limit orders")

        if self.order_type == OrderType.STOP and self.stop_price is None:
            raise ValueError("Stop price required for stop orders")

        if self.order_type == OrderType.STOP_LIMIT and (
            self.limit_price is None or self.stop_price is None
        ):
            raise ValueError("Both limit and stop prices required for stop-limit orders")

    def fill(self, quantity: float, price: float, timestamp: datetime = None) -> None:
        """
        Fill the order (partially or completely).

        Args:
            quantity: Quantity to fill
            price: Fill price
            timestamp: Fill timestamp
        """
        if quantity <= 0:
            raise ValueError("Fill quantity must be positive")

        if self.filled_quantity + quantity > self.quantity:
            raise ValueError("Fill quantity exceeds order quantity")

        # Update filled quantity and average fill price
        total_cost = (self.average_fill_price or 0) * self.filled_quantity + price * quantity
        self.filled_quantity += quantity
        self.average_fill_price = total_cost / self.filled_quantity

        # Update status
        if self.filled_quantity >= self.quantity:
            self.status = OrderStatus.FILLED
            self.filled_at = timestamp or datetime.now()
        else:
            self.status = OrderStatus.PARTIALLY_FILLED

    def cancel(self) -> None:
        """Cancel the order."""
        if self.status in [OrderStatus.FILLED, OrderStatus.CANCELLED]:
            raise ValueError(f"Cannot cancel order with status {self.status}")

        self.status = OrderStatus.CANCELLED

    def is_filled(self) -> bool:
        """Check if order is completely filled."""
        return self.status == OrderStatus.FILLED

    def is_open(self) -> bool:
        """Check if order is still open."""
        return self.status in [OrderStatus.PENDING, OrderStatus.SUBMITTED, OrderStatus.PARTIALLY_FILLED]

    def remaining_quantity(self) -> float:
        """Get remaining quantity to be filled."""
        return self.quantity - self.filled_quantity

    def __repr__(self) -> str:
        """String representation of the order."""
        return (
            f"Order(id={self.order_id[:8]}..., {self.side.value} {self.quantity} {self.symbol} "
            f"@ {self.order_type.value}, status={self.status.value})"
        )
