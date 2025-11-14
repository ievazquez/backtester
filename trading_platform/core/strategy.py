"""Base strategy class for the trading platform."""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from datetime import datetime
import pandas as pd

from trading_platform.core.portfolio import Portfolio
from trading_platform.core.order import Order, OrderType, OrderSide


class Strategy(ABC):
    """
    Abstract base class for trading strategies.

    All trading strategies should inherit from this class and implement
    the required methods.
    """

    def __init__(self, name: str = None):
        """
        Initialize strategy.

        Args:
            name: Strategy name (defaults to class name)
        """
        self.name = name or self.__class__.__name__
        self.portfolio: Optional[Portfolio] = None
        self.current_time: Optional[datetime] = None
        self.current_data: Dict[str, pd.DataFrame] = {}
        self.parameters: Dict[str, Any] = {}
        self._initialized = False

    def initialize(self, portfolio: Portfolio) -> None:
        """
        Initialize strategy with a portfolio.

        This is called by the backtesting or live trading engine.

        Args:
            portfolio: Portfolio instance to use
        """
        self.portfolio = portfolio
        self._initialized = True
        self.on_start()

    def on_start(self) -> None:
        """
        Called when strategy starts.

        Override this method to perform initialization tasks like
        setting parameters, loading models, etc.
        """
        pass

    @abstractmethod
    def on_data(self, data: Dict[str, pd.DataFrame]) -> None:
        """
        Called when new data is available.

        This is the main method where strategy logic should be implemented.

        Args:
            data: Dictionary mapping symbols to their OHLCV data
        """
        pass

    def on_order_filled(self, order: Order) -> None:
        """
        Called when an order is filled.

        Override this method to handle order fill events.

        Args:
            order: The filled order
        """
        pass

    def on_order_cancelled(self, order: Order) -> None:
        """
        Called when an order is cancelled.

        Override this method to handle order cancellation events.

        Args:
            order: The cancelled order
        """
        pass

    def on_stop(self) -> None:
        """
        Called when strategy stops.

        Override this method to perform cleanup tasks.
        """
        pass

    # Convenience methods for placing orders

    def buy(
        self,
        symbol: str,
        quantity: float,
        order_type: OrderType = OrderType.MARKET,
        limit_price: Optional[float] = None,
        stop_price: Optional[float] = None,
    ) -> Order:
        """
        Create a buy order.

        Args:
            symbol: Trading symbol
            quantity: Quantity to buy
            order_type: Type of order
            limit_price: Limit price (for limit orders)
            stop_price: Stop price (for stop orders)

        Returns:
            Created order
        """
        if not self._initialized:
            raise RuntimeError("Strategy not initialized")

        order = Order(
            symbol=symbol,
            side=OrderSide.BUY,
            quantity=quantity,
            order_type=order_type,
            limit_price=limit_price,
            stop_price=stop_price,
        )

        return order

    def sell(
        self,
        symbol: str,
        quantity: float,
        order_type: OrderType = OrderType.MARKET,
        limit_price: Optional[float] = None,
        stop_price: Optional[float] = None,
    ) -> Order:
        """
        Create a sell order.

        Args:
            symbol: Trading symbol
            quantity: Quantity to sell
            order_type: Type of order
            limit_price: Limit price (for limit orders)
            stop_price: Stop price (for stop orders)

        Returns:
            Created order
        """
        if not self._initialized:
            raise RuntimeError("Strategy not initialized")

        order = Order(
            symbol=symbol,
            side=OrderSide.SELL,
            quantity=quantity,
            order_type=order_type,
            limit_price=limit_price,
            stop_price=stop_price,
        )

        return order

    def close_position(self, symbol: str) -> Optional[Order]:
        """
        Close an existing position.

        Args:
            symbol: Trading symbol

        Returns:
            Order to close the position, or None if no position exists
        """
        if not self._initialized:
            raise RuntimeError("Strategy not initialized")

        position = self.portfolio.get_position(symbol)
        if position is None or position.is_closed():
            return None

        # Create order in opposite direction
        if position.is_long():
            return self.sell(symbol, abs(position.quantity))
        else:
            return self.buy(symbol, abs(position.quantity))

    def close_all_positions(self) -> List[Order]:
        """
        Close all open positions.

        Returns:
            List of orders to close all positions
        """
        if not self._initialized:
            raise RuntimeError("Strategy not initialized")

        orders = []
        for symbol in list(self.portfolio.positions.keys()):
            order = self.close_position(symbol)
            if order is not None:
                orders.append(order)

        return orders

    def get_position_quantity(self, symbol: str) -> float:
        """
        Get current position quantity for a symbol.

        Args:
            symbol: Trading symbol

        Returns:
            Position quantity (0 if no position)
        """
        if not self._initialized:
            return 0.0

        position = self.portfolio.get_position(symbol)
        return position.quantity if position else 0.0

    def get_position_value(self, symbol: str) -> float:
        """
        Get current position value for a symbol.

        Args:
            symbol: Trading symbol

        Returns:
            Position market value (0 if no position)
        """
        if not self._initialized:
            return 0.0

        position = self.portfolio.get_position(symbol)
        return position.market_value() if position else 0.0

    def set_parameter(self, name: str, value: Any) -> None:
        """
        Set a strategy parameter.

        Args:
            name: Parameter name
            value: Parameter value
        """
        self.parameters[name] = value

    def get_parameter(self, name: str, default: Any = None) -> Any:
        """
        Get a strategy parameter.

        Args:
            name: Parameter name
            default: Default value if parameter not found

        Returns:
            Parameter value
        """
        return self.parameters.get(name, default)

    def log(self, message: str) -> None:
        """
        Log a message.

        Args:
            message: Message to log
        """
        timestamp = self.current_time or datetime.now()
        print(f"[{timestamp}] {self.name}: {message}")

    def __repr__(self) -> str:
        """String representation of the strategy."""
        return f"Strategy(name={self.name})"
