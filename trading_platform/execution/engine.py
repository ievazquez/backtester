"""Live trading execution engine."""

from typing import List, Dict, Optional
from datetime import datetime
import time
import threading

from trading_platform.core.strategy import Strategy
from trading_platform.core.portfolio import Portfolio
from trading_platform.core.order import Order
from trading_platform.brokers.base import BrokerAdapter
from trading_platform.execution.order_manager import OrderManager
from trading_platform.execution.risk_manager import RiskManager


class LiveTradingEngine:
    """
    Live trading execution engine.

    Executes strategies in real-time with integrated risk management
    and order execution.
    """

    def __init__(
        self,
        strategy: Strategy,
        broker: BrokerAdapter,
        symbols: List[str],
        risk_manager_config: Optional[Dict] = None,
        update_interval: float = 1.0,  # seconds
    ):
        """
        Initialize live trading engine.

        Args:
            strategy: Trading strategy
            broker: Broker adapter
            symbols: List of symbols to trade
            risk_manager_config: Risk manager configuration
            update_interval: Update interval in seconds
        """
        self.strategy = strategy
        self.broker = broker
        self.symbols = symbols
        self.update_interval = update_interval

        # Initialize components
        self.order_manager = OrderManager(broker)
        self.risk_manager = RiskManager(**(risk_manager_config or {}))

        # Portfolio initialization (will be synced with broker)
        self.portfolio: Optional[Portfolio] = None

        # State
        self.running = False
        self._main_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()

        # Market data
        self.current_prices: Dict[str, float] = {}
        self.market_data_callbacks: Dict[str, callable] = {}

    def start(self) -> None:
        """Start live trading."""
        if self.running:
            print("Live trading already running")
            return

        print("=" * 60)
        print("STARTING LIVE TRADING")
        print("=" * 60)

        # Connect to broker
        if not self.broker.is_connected():
            print("Connecting to broker...")
            if not self.broker.connect():
                raise RuntimeError("Failed to connect to broker")

        # Sync portfolio with broker
        self._sync_portfolio()

        # Initialize strategy
        self.strategy.initialize(self.portfolio)

        # Start order monitoring
        self.order_manager.start_monitoring()

        # Register order callbacks
        self.order_manager.register_callback('on_fill', self._on_order_filled)
        self.order_manager.register_callback('on_cancel', self._on_order_cancelled)

        # Subscribe to market data
        self._subscribe_market_data()

        # Start main loop
        self.running = True
        self._stop_event.clear()

        self._main_thread = threading.Thread(target=self._main_loop, daemon=False)
        self._main_thread.start()

        print(f"Live trading started for {len(self.symbols)} symbols")
        print(f"Strategy: {self.strategy.name}")
        print(f"Initial Equity: ${self.portfolio.total_equity():,.2f}")
        print("=" * 60)

    def stop(self) -> None:
        """Stop live trading."""
        if not self.running:
            print("Live trading not running")
            return

        print("\n" + "=" * 60)
        print("STOPPING LIVE TRADING")
        print("=" * 60)

        # Stop main loop
        self.running = False
        self._stop_event.set()

        # Wait for main thread to finish
        if self._main_thread:
            self._main_thread.join(timeout=10)

        # Stop order monitoring
        self.order_manager.stop_monitoring()

        # Unsubscribe from market data
        self._unsubscribe_market_data()

        # Call strategy's on_stop
        self.strategy.on_stop()

        # Print final summary
        print(f"\nFinal Equity: ${self.portfolio.total_equity():,.2f}")
        print(f"Total Return: {self.portfolio.total_return():.2f}%")
        print(f"Total Trades: {len(self.order_manager.filled_orders)}")
        print("=" * 60)

    def _main_loop(self) -> None:
        """Main trading loop."""
        while self.running and not self._stop_event.is_set():
            try:
                # Update current time
                self.strategy.current_time = datetime.now()

                # Update market prices
                self._update_prices()

                # Update portfolio
                self.portfolio.update_prices(self.current_prices, datetime.now())

                # Update risk manager
                self.risk_manager.update_daily_pnl(
                    datetime.now(),
                    self.portfolio.total_pnl()
                )

                # Call strategy
                orders = self.strategy.on_data(self.strategy.current_data)

                # Process strategy orders
                if orders:
                    if isinstance(orders, Order):
                        self._process_strategy_order(orders)
                    elif isinstance(orders, list):
                        for order in orders:
                            self._process_strategy_order(order)

                # Sleep until next update
                time.sleep(self.update_interval)

            except KeyboardInterrupt:
                print("\nReceived interrupt signal")
                break
            except Exception as e:
                print(f"Error in main loop: {e}")
                import traceback
                traceback.print_exc()
                time.sleep(self.update_interval)

    def _sync_portfolio(self) -> None:
        """Sync portfolio with broker account."""
        print("Syncing portfolio with broker...")

        # Get account info
        cash = self.broker.get_account_balance()
        equity = self.broker.get_account_equity()

        # Create portfolio
        self.portfolio = Portfolio(initial_capital=equity)
        self.portfolio.cash = cash

        # Get positions
        positions = self.broker.get_positions()
        for position in positions:
            self.portfolio.positions[position.symbol] = position

        print(f"Portfolio synced: ${equity:,.2f} equity, {len(positions)} positions")

    def _update_prices(self) -> None:
        """Update current market prices."""
        for symbol in self.symbols:
            try:
                price = self.broker.get_latest_price(symbol)
                self.current_prices[symbol] = price
            except Exception as e:
                print(f"Error getting price for {symbol}: {e}")

    def _subscribe_market_data(self) -> None:
        """Subscribe to market data for all symbols."""
        for symbol in self.symbols:
            try:
                def callback(sym, data):
                    if 'price' in data:
                        self.current_prices[sym] = data['price']

                self.broker.subscribe_market_data(symbol, callback)
            except Exception as e:
                print(f"Error subscribing to {symbol}: {e}")

    def _unsubscribe_market_data(self) -> None:
        """Unsubscribe from market data."""
        for symbol in self.symbols:
            try:
                self.broker.unsubscribe_market_data(symbol)
            except Exception as e:
                print(f"Error unsubscribing from {symbol}: {e}")

    def _process_strategy_order(self, order: Order) -> None:
        """
        Process an order from the strategy.

        Args:
            order: Order from strategy
        """
        # Get current price
        current_price = self.current_prices.get(order.symbol)
        if current_price is None:
            print(f"No price data for {order.symbol}, skipping order")
            return

        # Validate with risk manager
        is_valid, reason = self.risk_manager.validate_order(
            order,
            self.portfolio,
            current_price
        )

        if not is_valid:
            print(f"Order rejected by risk manager: {reason}")
            return

        # Submit order
        try:
            self.order_manager.submit_order(order)
        except Exception as e:
            print(f"Error submitting order: {e}")

    def _on_order_filled(self, order: Order) -> None:
        """
        Callback when an order is filled.

        Args:
            order: Filled order
        """
        # Get fill price (use current price as approximation)
        fill_price = self.current_prices.get(order.symbol, 0)

        # Update portfolio
        from trading_platform.core.order import OrderSide
        quantity = order.quantity if order.side == OrderSide.BUY else -order.quantity

        self.portfolio.update_position(
            symbol=order.symbol,
            quantity=quantity,
            price=fill_price,
            commission=fill_price * order.quantity * 0.001,  # Assume 0.1% commission
            timestamp=datetime.now()
        )

        # Notify strategy
        try:
            self.strategy.on_order_filled(order)
        except Exception as e:
            print(f"Error in strategy on_order_filled: {e}")

    def _on_order_cancelled(self, order: Order) -> None:
        """
        Callback when an order is cancelled.

        Args:
            order: Cancelled order
        """
        # Notify strategy
        try:
            self.strategy.on_order_cancelled(order)
        except Exception as e:
            print(f"Error in strategy on_order_cancelled: {e}")

    def get_status(self) -> Dict:
        """
        Get live trading status.

        Returns:
            Dictionary with status information
        """
        return {
            'running': self.running,
            'strategy': self.strategy.name,
            'symbols': self.symbols,
            'portfolio': self.portfolio.summary() if self.portfolio else {},
            'order_manager': self.order_manager.get_summary(),
            'risk_manager': self.risk_manager.get_summary(),
            'current_prices': self.current_prices
        }

    def __repr__(self) -> str:
        """String representation."""
        status = "running" if self.running else "stopped"
        return f"LiveTradingEngine({self.strategy.name}, {status})"
