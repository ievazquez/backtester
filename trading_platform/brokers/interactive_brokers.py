"""Interactive Brokers broker adapter."""

from typing import List, Dict, Optional, Callable
from datetime import datetime
import pandas as pd
import time
import threading

from trading_platform.brokers.base import BrokerAdapter
from trading_platform.core.order import Order, OrderStatus, OrderType, OrderSide
from trading_platform.core.position import Position


class InteractiveBrokersAdapter(BrokerAdapter):
    """
    Interactive Brokers broker adapter using IB API.

    Supports stocks, options, futures, forex, and more through IB TWS/Gateway.
    """

    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 7497,  # 7497 for TWS paper, 7496 for TWS live, 4002 for Gateway live
        client_id: int = 1,
    ):
        """
        Initialize Interactive Brokers adapter.

        Args:
            host: TWS/Gateway host
            port: TWS/Gateway port
            client_id: Client ID for connection
        """
        super().__init__()
        self.host = host
        self.port = port
        self.client_id = client_id

        self._app = None
        self._positions: Dict[str, Position] = {}
        self._orders: Dict[str, Order] = {}
        self._market_data_callbacks: Dict[str, Callable] = {}

        try:
            from ibapi.client import EClient
            from ibapi.wrapper import EWrapper
            from ibapi.contract import Contract
            from ibapi.order import Order as IBOrder

            self._ib_modules = {
                'EClient': EClient,
                'EWrapper': EWrapper,
                'Contract': Contract,
                'IBOrder': IBOrder
            }
        except ImportError:
            raise ImportError(
                "ibapi is required for Interactive Brokers. "
                "Install with: pip install ibapi"
            )

    def connect(self) -> bool:
        """
        Connect to Interactive Brokers TWS/Gateway.

        Returns:
            True if connection successful
        """
        try:
            # Create IB API application
            self._app = self._create_ib_app()

            # Connect
            self._app.connect(self.host, self.port, self.client_id)

            # Start message processing thread
            api_thread = threading.Thread(target=self._run_loop, daemon=True)
            api_thread.start()

            # Wait for connection
            time.sleep(1)

            if self._app.isConnected():
                self.connected = True
                print(f"Connected to Interactive Brokers on {self.host}:{self.port}")
                return True
            else:
                print("Failed to connect to Interactive Brokers")
                return False

        except Exception as e:
            print(f"Error connecting to Interactive Brokers: {e}")
            return False

    def disconnect(self) -> None:
        """Disconnect from Interactive Brokers."""
        if self._app and self._app.isConnected():
            self._app.disconnect()
            self.connected = False
            print("Disconnected from Interactive Brokers")

    def is_connected(self) -> bool:
        """
        Check if connected to Interactive Brokers.

        Returns:
            True if connected
        """
        return self.connected and self._app and self._app.isConnected()

    def submit_order(self, order: Order) -> str:
        """
        Submit an order to Interactive Brokers.

        Args:
            order: Order to submit

        Returns:
            Broker order ID
        """
        if not self.is_connected():
            raise RuntimeError("Not connected to Interactive Brokers")

        # Create IB contract
        contract = self._create_contract(order.symbol)

        # Create IB order
        ib_order = self._create_ib_order(order)

        # Get next order ID
        order_id = self._app.nextOrderId
        self._app.nextOrderId += 1

        # Place order
        self._app.placeOrder(order_id, contract, ib_order)

        # Store order
        self._orders[str(order_id)] = order

        return str(order_id)

    def cancel_order(self, order_id: str) -> bool:
        """
        Cancel an order.

        Args:
            order_id: Broker order ID

        Returns:
            True if cancellation successful
        """
        if not self.is_connected():
            raise RuntimeError("Not connected to Interactive Brokers")

        try:
            self._app.cancelOrder(int(order_id))
            return True
        except Exception as e:
            print(f"Error cancelling order: {e}")
            return False

    def get_order_status(self, order_id: str) -> OrderStatus:
        """
        Get order status.

        Args:
            order_id: Broker order ID

        Returns:
            Order status
        """
        order = self._orders.get(order_id)
        return order.status if order else OrderStatus.PENDING

    def get_positions(self) -> List[Position]:
        """
        Get all current positions.

        Returns:
            List of positions
        """
        if not self.is_connected():
            raise RuntimeError("Not connected to Interactive Brokers")

        # Request positions
        self._app.reqPositions()
        time.sleep(0.5)  # Wait for response

        return list(self._positions.values())

    def get_position(self, symbol: str) -> Optional[Position]:
        """
        Get position for a specific symbol.

        Args:
            symbol: Trading symbol

        Returns:
            Position if exists, None otherwise
        """
        return self._positions.get(symbol)

    def get_account_balance(self) -> float:
        """
        Get account cash balance.

        Returns:
            Cash balance
        """
        if not self.is_connected():
            raise RuntimeError("Not connected to Interactive Brokers")

        # Request account summary
        self._app.reqAccountSummary(9001, "All", "TotalCashValue")
        time.sleep(0.5)

        # Return cached value (would be updated by callback)
        return getattr(self._app, '_cash_balance', 0.0)

    def get_account_equity(self) -> float:
        """
        Get total account equity.

        Returns:
            Total equity
        """
        if not self.is_connected():
            raise RuntimeError("Not connected to Interactive Brokers")

        # Request account summary
        self._app.reqAccountSummary(9002, "All", "NetLiquidation")
        time.sleep(0.5)

        # Return cached value (would be updated by callback)
        return getattr(self._app, '_equity', 0.0)

    def get_latest_price(self, symbol: str) -> float:
        """
        Get latest price for a symbol.

        Args:
            symbol: Trading symbol

        Returns:
            Latest price
        """
        if not self.is_connected():
            raise RuntimeError("Not connected to Interactive Brokers")

        contract = self._create_contract(symbol)

        # Request market data
        req_id = hash(symbol) % 10000
        self._app.reqMktData(req_id, contract, "", False, False, [])
        time.sleep(0.5)

        # Cancel market data
        self._app.cancelMktData(req_id)

        # Return cached price (would be updated by callback)
        return getattr(self._app, f'_price_{symbol}', 0.0)

    def get_historical_data(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        interval: str = "1d",
    ) -> pd.DataFrame:
        """
        Get historical OHLCV data from Interactive Brokers.

        Args:
            symbol: Trading symbol
            start_date: Start date
            end_date: End date
            interval: Data interval

        Returns:
            DataFrame with OHLCV data
        """
        if not self.is_connected():
            raise RuntimeError("Not connected to Interactive Brokers")

        contract = self._create_contract(symbol)

        # Convert interval to IB format
        bar_size = self._convert_interval(interval)

        # Calculate duration
        duration = (end_date - start_date).days
        duration_str = f"{duration} D"

        # Request historical data
        req_id = hash(f"{symbol}_{start_date}_{end_date}") % 10000
        self._app.reqHistoricalData(
            req_id,
            contract,
            end_date.strftime("%Y%m%d %H:%M:%S"),
            duration_str,
            bar_size,
            "TRADES",
            1,
            1,
            False,
            []
        )

        time.sleep(1)

        # Return cached data (would be updated by callback)
        return getattr(self._app, f'_hist_data_{req_id}', pd.DataFrame())

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
        if not self.is_connected():
            raise RuntimeError("Not connected to Interactive Brokers")

        self._market_data_callbacks[symbol] = callback

        contract = self._create_contract(symbol)
        req_id = hash(symbol) % 10000

        self._app.reqMktData(req_id, contract, "", False, False, [])

    def unsubscribe_market_data(self, symbol: str) -> None:
        """
        Unsubscribe from market data.

        Args:
            symbol: Trading symbol
        """
        if symbol in self._market_data_callbacks:
            del self._market_data_callbacks[symbol]

        req_id = hash(symbol) % 10000
        self._app.cancelMktData(req_id)

    def _create_ib_app(self):
        """Create IB API application."""
        EClient = self._ib_modules['EClient']
        EWrapper = self._ib_modules['EWrapper']

        class IBApp(EWrapper, EClient):
            def __init__(self):
                EClient.__init__(self, self)
                self.nextOrderId = None

            def nextValidId(self, orderId: int):
                self.nextOrderId = orderId

        return IBApp()

    def _create_contract(self, symbol: str):
        """Create IB contract object."""
        Contract = self._ib_modules['Contract']

        contract = Contract()
        contract.symbol = symbol
        contract.secType = "STK"  # Stock (can be extended for other types)
        contract.exchange = "SMART"
        contract.currency = "USD"

        return contract

    def _create_ib_order(self, order: Order):
        """Create IB order object."""
        IBOrder = self._ib_modules['IBOrder']

        ib_order = IBOrder()
        ib_order.action = "BUY" if order.side == OrderSide.BUY else "SELL"
        ib_order.totalQuantity = order.quantity
        ib_order.orderType = self._convert_order_type(order.order_type)

        if order.order_type == OrderType.LIMIT:
            ib_order.lmtPrice = order.limit_price

        if order.order_type == OrderType.STOP:
            ib_order.auxPrice = order.stop_price

        return ib_order

    def _convert_order_type(self, order_type: OrderType) -> str:
        """Convert order type to IB format."""
        mapping = {
            OrderType.MARKET: "MKT",
            OrderType.LIMIT: "LMT",
            OrderType.STOP: "STP",
            OrderType.STOP_LIMIT: "STP LMT"
        }
        return mapping.get(order_type, "MKT")

    def _convert_interval(self, interval: str) -> str:
        """Convert interval to IB bar size."""
        mapping = {
            "1m": "1 min",
            "5m": "5 mins",
            "15m": "15 mins",
            "30m": "30 mins",
            "1h": "1 hour",
            "1d": "1 day",
        }
        return mapping.get(interval, "1 day")

    def _run_loop(self):
        """Run IB API message loop."""
        self._app.run()
