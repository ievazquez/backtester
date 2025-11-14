"""Base broker adapter interface."""

from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Callable
from datetime import datetime
import pandas as pd

from trading_platform.core.order import Order, OrderStatus
from trading_platform.core.position import Position


class BrokerAdapter(ABC):
    """
    Abstract base class for broker adapters.

    All broker integrations should implement this interface.
    """

    def __init__(self):
        """Initialize broker adapter."""
        self.connected = False
        self.account_id: Optional[str] = None

    @abstractmethod
    def connect(self) -> bool:
        """
        Connect to the broker.

        Returns:
            True if connection successful
        """
        pass

    @abstractmethod
    def disconnect(self) -> None:
        """Disconnect from the broker."""
        pass

    @abstractmethod
    def is_connected(self) -> bool:
        """
        Check if connected to broker.

        Returns:
            True if connected
        """
        pass

    @abstractmethod
    def submit_order(self, order: Order) -> str:
        """
        Submit an order to the broker.

        Args:
            order: Order to submit

        Returns:
            Broker order ID
        """
        pass

    @abstractmethod
    def cancel_order(self, order_id: str) -> bool:
        """
        Cancel an order.

        Args:
            order_id: Broker order ID

        Returns:
            True if cancellation successful
        """
        pass

    @abstractmethod
    def get_order_status(self, order_id: str) -> OrderStatus:
        """
        Get order status.

        Args:
            order_id: Broker order ID

        Returns:
            Order status
        """
        pass

    @abstractmethod
    def get_positions(self) -> List[Position]:
        """
        Get all current positions.

        Returns:
            List of positions
        """
        pass

    @abstractmethod
    def get_position(self, symbol: str) -> Optional[Position]:
        """
        Get position for a specific symbol.

        Args:
            symbol: Trading symbol

        Returns:
            Position if exists, None otherwise
        """
        pass

    @abstractmethod
    def get_account_balance(self) -> float:
        """
        Get account cash balance.

        Returns:
            Cash balance
        """
        pass

    @abstractmethod
    def get_account_equity(self) -> float:
        """
        Get total account equity.

        Returns:
            Total equity
        """
        pass

    @abstractmethod
    def get_latest_price(self, symbol: str) -> float:
        """
        Get latest price for a symbol.

        Args:
            symbol: Trading symbol

        Returns:
            Latest price
        """
        pass

    @abstractmethod
    def get_historical_data(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        interval: str = "1d",
    ) -> pd.DataFrame:
        """
        Get historical OHLCV data.

        Args:
            symbol: Trading symbol
            start_date: Start date
            end_date: End date
            interval: Data interval

        Returns:
            DataFrame with OHLCV data
        """
        pass

    @abstractmethod
    def subscribe_market_data(
        self,
        symbol: str,
        callback: Callable[[str, Dict], None]
    ) -> None:
        """
        Subscribe to real-time market data.

        Args:
            symbol: Trading symbol
            callback: Callback function(symbol, data_dict)
        """
        pass

    @abstractmethod
    def unsubscribe_market_data(self, symbol: str) -> None:
        """
        Unsubscribe from market data.

        Args:
            symbol: Trading symbol
        """
        pass

    def get_account_summary(self) -> Dict:
        """
        Get account summary.

        Returns:
            Dictionary with account information
        """
        return {
            'account_id': self.account_id,
            'cash': self.get_account_balance(),
            'equity': self.get_account_equity(),
            'connected': self.is_connected()
        }

    def __repr__(self) -> str:
        """String representation."""
        status = "connected" if self.connected else "disconnected"
        return f"{self.__class__.__name__}({status})"
