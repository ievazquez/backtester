"""Darwinex broker adapter."""

from typing import List, Dict, Optional, Callable
from datetime import datetime
import pandas as pd

from trading_platform.brokers.base import BrokerAdapter
from trading_platform.core.order import Order, OrderStatus
from trading_platform.core.position import Position


class DarwinexAdapter(BrokerAdapter):
    """
    Darwinex broker adapter.

    Darwinex is a forex broker with unique features for strategy sharing.
    This adapter uses their MetaTrader 5 integration.

    Note: Darwinex primarily uses MT5, so this adapter would integrate
    through the MetaTrader 5 Python API.
    """

    def __init__(
        self,
        account_id: str,
        password: str,
        server: str = "Darwinex-Demo",  # or "Darwinex-Live"
    ):
        """
        Initialize Darwinex adapter.

        Args:
            account_id: MT5 account ID
            password: MT5 account password
            server: MT5 server name
        """
        super().__init__()
        self.account_id = account_id
        self.password = password
        self.server = server

        self._positions: Dict[str, Position] = {}
        self._orders: Dict[str, Order] = {}

        try:
            import MetaTrader5 as mt5
            self.mt5 = mt5
        except ImportError:
            raise ImportError(
                "MetaTrader5 is required for Darwinex. "
                "Install with: pip install MetaTrader5"
            )

    def connect(self) -> bool:
        """
        Connect to Darwinex via MetaTrader 5.

        Returns:
            True if connection successful
        """
        try:
            # Initialize MT5
            if not self.mt5.initialize():
                print(f"MT5 initialization failed: {self.mt5.last_error()}")
                return False

            # Login
            authorized = self.mt5.login(
                login=int(self.account_id),
                password=self.password,
                server=self.server
            )

            if not authorized:
                print(f"MT5 login failed: {self.mt5.last_error()}")
                return False

            self.connected = True
            print(f"Connected to Darwinex via MT5 ({self.server})")
            return True

        except Exception as e:
            print(f"Error connecting to Darwinex: {e}")
            return False

    def disconnect(self) -> None:
        """Disconnect from Darwinex."""
        if self.connected:
            self.mt5.shutdown()
            self.connected = False
            print("Disconnected from Darwinex")

    def is_connected(self) -> bool:
        """
        Check if connected to Darwinex.

        Returns:
            True if connected
        """
        return self.connected

    def submit_order(self, order: Order) -> str:
        """
        Submit an order to Darwinex.

        Args:
            order: Order to submit

        Returns:
            Broker order ID
        """
        if not self.is_connected():
            raise RuntimeError("Not connected to Darwinex")

        # Prepare order request
        symbol = order.symbol
        lot = order.quantity / 100000  # Convert to lots (standard for forex)

        # Get symbol info
        symbol_info = self.mt5.symbol_info(symbol)
        if symbol_info is None:
            raise ValueError(f"Symbol {symbol} not found")

        # Prepare request
        request = {
            "action": self.mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": lot,
            "type": self._convert_order_type(order),
            "deviation": 10,
            "magic": 234000,
            "comment": "Trading Platform Order",
            "type_time": self.mt5.ORDER_TIME_GTC,
            "type_filling": self.mt5.ORDER_FILLING_IOC,
        }

        # Add price for limit orders
        if order.limit_price:
            request["price"] = order.limit_price

        if order.stop_price:
            request["sl"] = order.stop_price

        # Send order
        result = self.mt5.order_send(request)

        if result.retcode != self.mt5.TRADE_RETCODE_DONE:
            raise RuntimeError(f"Order failed: {result.comment}")

        # Store order
        broker_order_id = str(result.order)
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
            raise RuntimeError("Not connected to Darwinex")

        try:
            request = {
                "action": self.mt5.TRADE_ACTION_REMOVE,
                "order": int(order_id),
            }

            result = self.mt5.order_send(request)
            return result.retcode == self.mt5.TRADE_RETCODE_DONE

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
        # Check if order exists in history
        from_date = datetime(2020, 1, 1)
        to_date = datetime.now()

        orders = self.mt5.history_orders_get(from_date, to_date)

        for order in orders:
            if str(order.ticket) == order_id:
                return self._convert_mt5_order_state(order.state)

        return OrderStatus.PENDING

    def get_positions(self) -> List[Position]:
        """
        Get all current positions.

        Returns:
            List of positions
        """
        if not self.is_connected():
            raise RuntimeError("Not connected to Darwinex")

        positions = []
        mt5_positions = self.mt5.positions_get()

        if mt5_positions is not None:
            for mt5_pos in mt5_positions:
                position = self._parse_mt5_position(mt5_pos)
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
            raise RuntimeError("Not connected to Darwinex")

        mt5_positions = self.mt5.positions_get(symbol=symbol)

        if mt5_positions and len(mt5_positions) > 0:
            return self._parse_mt5_position(mt5_positions[0])

        return None

    def get_account_balance(self) -> float:
        """
        Get account cash balance.

        Returns:
            Cash balance
        """
        if not self.is_connected():
            raise RuntimeError("Not connected to Darwinex")

        account_info = self.mt5.account_info()
        return account_info.balance if account_info else 0.0

    def get_account_equity(self) -> float:
        """
        Get total account equity.

        Returns:
            Total equity
        """
        if not self.is_connected():
            raise RuntimeError("Not connected to Darwinex")

        account_info = self.mt5.account_info()
        return account_info.equity if account_info else 0.0

    def get_latest_price(self, symbol: str) -> float:
        """
        Get latest price for a symbol.

        Args:
            symbol: Trading symbol

        Returns:
            Latest price
        """
        if not self.is_connected():
            raise RuntimeError("Not connected to Darwinex")

        tick = self.mt5.symbol_info_tick(symbol)
        if tick:
            return (tick.bid + tick.ask) / 2

        return 0.0

    def get_historical_data(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        interval: str = "1d",
    ) -> pd.DataFrame:
        """
        Get historical OHLCV data from Darwinex.

        Args:
            symbol: Trading symbol
            start_date: Start date
            end_date: End date
            interval: Data interval

        Returns:
            DataFrame with OHLCV data
        """
        if not self.is_connected():
            raise RuntimeError("Not connected to Darwinex")

        # Convert interval to MT5 timeframe
        timeframe = self._convert_interval(interval)

        # Get rates
        rates = self.mt5.copy_rates_range(symbol, timeframe, start_date, end_date)

        if rates is None or len(rates) == 0:
            return pd.DataFrame()

        # Convert to DataFrame
        df = pd.DataFrame(rates)
        df['timestamp'] = pd.to_datetime(df['time'], unit='s')
        df = df[['timestamp', 'open', 'high', 'low', 'close', 'tick_volume']]
        df.columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
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
        # MT5 doesn't have traditional subscription model
        # Would need to implement polling
        print(f"Market data streaming for {symbol} (polling-based)")

    def unsubscribe_market_data(self, symbol: str) -> None:
        """
        Unsubscribe from market data.

        Args:
            symbol: Trading symbol
        """
        pass

    def _convert_order_type(self, order: Order) -> int:
        """Convert order to MT5 order type."""
        from trading_platform.core.order import OrderSide, OrderType

        if order.order_type == OrderType.MARKET:
            return self.mt5.ORDER_TYPE_BUY if order.side == OrderSide.BUY else self.mt5.ORDER_TYPE_SELL
        elif order.order_type == OrderType.LIMIT:
            return self.mt5.ORDER_TYPE_BUY_LIMIT if order.side == OrderSide.BUY else self.mt5.ORDER_TYPE_SELL_LIMIT
        elif order.order_type == OrderType.STOP:
            return self.mt5.ORDER_TYPE_BUY_STOP if order.side == OrderSide.BUY else self.mt5.ORDER_TYPE_SELL_STOP

        return self.mt5.ORDER_TYPE_BUY

    def _convert_mt5_order_state(self, state: int) -> OrderStatus:
        """Convert MT5 order state to platform status."""
        # MT5 order states
        if state == 1:  # ORDER_STATE_PLACED
            return OrderStatus.SUBMITTED
        elif state == 2:  # ORDER_STATE_FILLED
            return OrderStatus.FILLED
        elif state == 3:  # ORDER_STATE_CANCELLED
            return OrderStatus.CANCELLED
        else:
            return OrderStatus.PENDING

    def _convert_interval(self, interval: str) -> int:
        """Convert interval to MT5 timeframe."""
        mapping = {
            "1m": self.mt5.TIMEFRAME_M1,
            "5m": self.mt5.TIMEFRAME_M5,
            "15m": self.mt5.TIMEFRAME_M15,
            "30m": self.mt5.TIMEFRAME_M30,
            "1h": self.mt5.TIMEFRAME_H1,
            "4h": self.mt5.TIMEFRAME_H4,
            "1d": self.mt5.TIMEFRAME_D1,
        }
        return mapping.get(interval, self.mt5.TIMEFRAME_D1)

    def _parse_mt5_position(self, mt5_pos) -> Position:
        """Parse MT5 position to platform Position."""
        # MT5 position type: 0=buy, 1=sell
        quantity = mt5_pos.volume * 100000  # Convert lots to units

        if mt5_pos.type == 1:  # Sell position
            quantity = -quantity

        position = Position(
            symbol=mt5_pos.symbol,
            quantity=quantity,
            average_price=mt5_pos.price_open
        )

        position.current_price = mt5_pos.price_current
        position.realized_pnl = mt5_pos.profit

        return position
