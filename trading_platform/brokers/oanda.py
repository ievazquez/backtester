"""OANDA broker adapter."""

from typing import List, Dict, Optional, Callable
from datetime import datetime
import pandas as pd

from trading_platform.brokers.base import BrokerAdapter
from trading_platform.core.order import Order, OrderStatus, OrderType, OrderSide
from trading_platform.core.position import Position


class OANDAAdapter(BrokerAdapter):
    """
    OANDA broker adapter using OANDA v20 API.

    Supports forex and CFD trading.
    """

    def __init__(
        self,
        api_token: str,
        account_id: str,
        environment: str = "practice",  # "practice" or "live"
    ):
        """
        Initialize OANDA adapter.

        Args:
            api_token: OANDA API token
            account_id: OANDA account ID
            environment: "practice" for demo or "live" for production
        """
        super().__init__()
        self.api_token = api_token
        self.account_id = account_id
        self.environment = environment

        # API endpoints
        if environment == "practice":
            self.api_url = "https://api-fxpractice.oanda.com"
            self.stream_url = "https://stream-fxpractice.oanda.com"
        else:
            self.api_url = "https://api-fxtrade.oanda.com"
            self.stream_url = "https://stream-fxtrade.oanda.com"

        self._positions: Dict[str, Position] = {}
        self._orders: Dict[str, Order] = {}
        self._streaming_threads: Dict[str, any] = {}

        try:
            import oandapyV20
            import oandapyV20.endpoints.accounts as accounts
            import oandapyV20.endpoints.orders as orders
            import oandapyV20.endpoints.positions as positions
            import oandapyV20.endpoints.pricing as pricing
            import oandapyV20.endpoints.instruments as instruments

            self._oanda_client = oandapyV20.API(
                access_token=api_token,
                environment=environment
            )

            self._oanda_modules = {
                'accounts': accounts,
                'orders': orders,
                'positions': positions,
                'pricing': pricing,
                'instruments': instruments
            }

        except ImportError:
            raise ImportError(
                "oandapyV20 is required for OANDA. "
                "Install with: pip install oandapyV20"
            )

    def connect(self) -> bool:
        """
        Connect to OANDA (validate credentials).

        Returns:
            True if connection successful
        """
        try:
            # Test connection by getting account details
            accounts = self._oanda_modules['accounts']
            request = accounts.AccountDetails(accountID=self.account_id)
            self._oanda_client.request(request)

            self.connected = True
            print(f"Connected to OANDA ({self.environment})")
            return True

        except Exception as e:
            print(f"Error connecting to OANDA: {e}")
            return False

    def disconnect(self) -> None:
        """Disconnect from OANDA."""
        # Stop all streaming connections
        for thread in self._streaming_threads.values():
            if hasattr(thread, 'stop'):
                thread.stop()

        self._streaming_threads.clear()
        self.connected = False
        print("Disconnected from OANDA")

    def is_connected(self) -> bool:
        """
        Check if connected to OANDA.

        Returns:
            True if connected
        """
        return self.connected

    def submit_order(self, order: Order) -> str:
        """
        Submit an order to OANDA.

        Args:
            order: Order to submit

        Returns:
            Broker order ID
        """
        if not self.is_connected():
            raise RuntimeError("Not connected to OANDA")

        orders_module = self._oanda_modules['orders']

        # Create order data
        order_data = {
            "order": {
                "instrument": self._convert_symbol(order.symbol),
                "units": str(int(order.quantity)) if order.side == OrderSide.BUY else str(-int(order.quantity)),
                "type": self._convert_order_type(order.order_type),
                "timeInForce": "FOK" if order.order_type == OrderType.MARKET else "GTC",
            }
        }

        # Add price for limit orders
        if order.order_type == OrderType.LIMIT:
            order_data["order"]["price"] = str(order.limit_price)

        # Add stop price for stop orders
        if order.order_type == OrderType.STOP:
            order_data["order"]["priceBound"] = str(order.stop_price)

        # Submit order
        request = orders_module.OrderCreate(accountID=self.account_id, data=order_data)
        response = self._oanda_client.request(request)

        # Get order ID
        broker_order_id = response.get("orderFillTransaction", {}).get("id", "")

        # Store order
        self._orders[broker_order_id] = order

        return broker_order_id

    def cancel_order(self, order_id: str) -> bool:
        """
        Cancel an order.

        Args:
            order_id: Broker order ID

        Returns:
            True if cancellation successful
        """
        if not self.is_connected():
            raise RuntimeError("Not connected to OANDA")

        try:
            orders_module = self._oanda_modules['orders']
            request = orders_module.OrderCancel(accountID=self.account_id, orderID=order_id)
            self._oanda_client.request(request)
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
        if not self.is_connected():
            raise RuntimeError("Not connected to OANDA")

        try:
            orders_module = self._oanda_modules['orders']
            request = orders_module.OrderDetails(accountID=self.account_id, orderID=order_id)
            response = self._oanda_client.request(request)

            status = response.get("order", {}).get("state", "")
            return self._convert_order_status(status)

        except Exception as e:
            print(f"Error getting order status: {e}")
            return OrderStatus.PENDING

    def get_positions(self) -> List[Position]:
        """
        Get all current positions.

        Returns:
            List of positions
        """
        if not self.is_connected():
            raise RuntimeError("Not connected to OANDA")

        positions_module = self._oanda_modules['positions']
        request = positions_module.OpenPositions(accountID=self.account_id)
        response = self._oanda_client.request(request)

        positions = []
        for pos_data in response.get("positions", []):
            position = self._parse_position(pos_data)
            if position:
                positions.append(position)
                self._positions[position.symbol] = position

        return positions

    def get_position(self, symbol: str) -> Optional[Position]:
        """
        Get position for a specific symbol.

        Args:
            symbol: Trading symbol

        Returns:
            Position if exists, None otherwise
        """
        if not self.is_connected():
            raise RuntimeError("Not connected to OANDA")

        try:
            positions_module = self._oanda_modules['positions']
            instrument = self._convert_symbol(symbol)
            request = positions_module.PositionDetails(accountID=self.account_id, instrument=instrument)
            response = self._oanda_client.request(request)

            return self._parse_position(response.get("position", {}))

        except Exception:
            return None

    def get_account_balance(self) -> float:
        """
        Get account cash balance.

        Returns:
            Cash balance
        """
        if not self.is_connected():
            raise RuntimeError("Not connected to OANDA")

        accounts = self._oanda_modules['accounts']
        request = accounts.AccountSummary(accountID=self.account_id)
        response = self._oanda_client.request(request)

        return float(response.get("account", {}).get("balance", 0))

    def get_account_equity(self) -> float:
        """
        Get total account equity.

        Returns:
            Total equity
        """
        if not self.is_connected():
            raise RuntimeError("Not connected to OANDA")

        accounts = self._oanda_modules['accounts']
        request = accounts.AccountSummary(accountID=self.account_id)
        response = self._oanda_client.request(request)

        return float(response.get("account", {}).get("NAV", 0))

    def get_latest_price(self, symbol: str) -> float:
        """
        Get latest price for a symbol.

        Args:
            symbol: Trading symbol

        Returns:
            Latest price
        """
        if not self.is_connected():
            raise RuntimeError("Not connected to OANDA")

        pricing = self._oanda_modules['pricing']
        instrument = self._convert_symbol(symbol)

        params = {"instruments": instrument}
        request = pricing.PricingInfo(accountID=self.account_id, params=params)
        response = self._oanda_client.request(request)

        prices = response.get("prices", [])
        if prices:
            # Return mid price
            bid = float(prices[0].get("bids", [{}])[0].get("price", 0))
            ask = float(prices[0].get("asks", [{}])[0].get("price", 0))
            return (bid + ask) / 2

        return 0.0

    def get_historical_data(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        interval: str = "1d",
    ) -> pd.DataFrame:
        """
        Get historical OHLCV data from OANDA.

        Args:
            symbol: Trading symbol
            start_date: Start date
            end_date: End date
            interval: Data interval

        Returns:
            DataFrame with OHLCV data
        """
        if not self.is_connected():
            raise RuntimeError("Not connected to OANDA")

        instruments = self._oanda_modules['instruments']
        instrument = self._convert_symbol(symbol)

        params = {
            "from": start_date.isoformat() + "Z",
            "to": end_date.isoformat() + "Z",
            "granularity": self._convert_interval(interval),
        }

        request = instruments.InstrumentsCandles(instrument=instrument, params=params)
        response = self._oanda_client.request(request)

        # Parse candles
        candles_data = []
        for candle in response.get("candles", []):
            if candle.get("complete"):
                mid = candle.get("mid", {})
                candles_data.append({
                    'timestamp': pd.to_datetime(candle['time']),
                    'open': float(mid.get('o', 0)),
                    'high': float(mid.get('h', 0)),
                    'low': float(mid.get('l', 0)),
                    'close': float(mid.get('c', 0)),
                    'volume': int(candle.get('volume', 0))
                })

        df = pd.DataFrame(candles_data)
        if not df.empty:
            df.set_index('timestamp', inplace=True)

        return df

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
            raise RuntimeError("Not connected to OANDA")

        # Implementation would use OANDA streaming API
        print(f"Market data streaming for {symbol} (implementation pending)")

    def unsubscribe_market_data(self, symbol: str) -> None:
        """
        Unsubscribe from market data.

        Args:
            symbol: Trading symbol
        """
        if symbol in self._streaming_threads:
            thread = self._streaming_threads[symbol]
            if hasattr(thread, 'stop'):
                thread.stop()
            del self._streaming_threads[symbol]

    def _convert_symbol(self, symbol: str) -> str:
        """Convert symbol to OANDA format (e.g., EUR_USD)."""
        # If already in OANDA format, return as is
        if "_" in symbol:
            return symbol

        # Convert common forex pairs
        if len(symbol) == 6:
            return f"{symbol[:3]}_{symbol[3:]}"

        return symbol

    def _convert_order_type(self, order_type: OrderType) -> str:
        """Convert order type to OANDA format."""
        mapping = {
            OrderType.MARKET: "MARKET",
            OrderType.LIMIT: "LIMIT",
            OrderType.STOP: "STOP",
            OrderType.STOP_LIMIT: "STOP"
        }
        return mapping.get(order_type, "MARKET")

    def _convert_order_status(self, oanda_status: str) -> OrderStatus:
        """Convert OANDA order status to platform format."""
        mapping = {
            "PENDING": OrderStatus.PENDING,
            "FILLED": OrderStatus.FILLED,
            "TRIGGERED": OrderStatus.SUBMITTED,
            "CANCELLED": OrderStatus.CANCELLED,
        }
        return mapping.get(oanda_status, OrderStatus.PENDING)

    def _convert_interval(self, interval: str) -> str:
        """Convert interval to OANDA granularity."""
        mapping = {
            "1m": "M1",
            "5m": "M5",
            "15m": "M15",
            "30m": "M30",
            "1h": "H1",
            "4h": "H4",
            "1d": "D",
        }
        return mapping.get(interval, "D")

    def _parse_position(self, pos_data: Dict) -> Optional[Position]:
        """Parse OANDA position data."""
        if not pos_data:
            return None

        instrument = pos_data.get("instrument", "")
        long_units = float(pos_data.get("long", {}).get("units", 0))
        short_units = float(pos_data.get("short", {}).get("units", 0))

        net_units = long_units + short_units  # short_units is negative

        if abs(net_units) < 1e-10:
            return None

        avg_price = 0
        if net_units > 0:
            avg_price = float(pos_data.get("long", {}).get("averagePrice", 0))
        else:
            avg_price = float(pos_data.get("short", {}).get("averagePrice", 0))

        unrealized_pl = float(pos_data.get("unrealizedPL", 0))

        position = Position(
            symbol=instrument.replace("_", ""),
            quantity=net_units,
            average_price=avg_price
        )
        position.realized_pnl = unrealized_pl

        return position
