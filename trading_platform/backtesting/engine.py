"""Backtesting engine implementation."""

from typing import List, Dict, Optional
from datetime import datetime
import pandas as pd
from tqdm import tqdm

from trading_platform.core.strategy import Strategy
from trading_platform.core.portfolio import Portfolio
from trading_platform.core.order import Order, OrderType, OrderSide, OrderStatus
from trading_platform.data.providers import DataProvider
from trading_platform.data.historical import HistoricalDataManager
from trading_platform.backtesting.metrics import PerformanceMetrics


class BacktestEngine:
    """
    Event-driven backtesting engine.

    Simulates historical trading with realistic order execution and
    portfolio management.
    """

    def __init__(
        self,
        strategy: Strategy,
        symbols: List[str],
        start_date: datetime,
        end_date: datetime,
        initial_capital: float = 100000.0,
        data_provider: Optional[DataProvider] = None,
        commission: float = 0.001,  # 0.1% per trade
        slippage: float = 0.0005,   # 0.05% slippage
        use_cache: bool = True,
        interval: str = "1d",
    ):
        """
        Initialize backtesting engine.

        Args:
            strategy: Trading strategy to backtest
            symbols: List of symbols to trade
            start_date: Backtest start date
            end_date: Backtest end date
            initial_capital: Initial capital
            data_provider: Data provider (defaults to Yahoo Finance)
            commission: Commission rate (as decimal)
            slippage: Slippage rate (as decimal)
            use_cache: Whether to cache historical data
            interval: Data interval (e.g., '1d', '1h', '5m')
        """
        self.strategy = strategy
        self.symbols = symbols
        self.start_date = start_date
        self.end_date = end_date
        self.initial_capital = initial_capital
        self.commission = commission
        self.slippage = slippage
        self.interval = interval

        # Initialize portfolio
        self.portfolio = Portfolio(initial_capital=initial_capital)

        # Initialize data manager
        self.data_manager = HistoricalDataManager(
            provider=data_provider,
            use_cache=use_cache
        )

        # Tracking
        self.pending_orders: List[Order] = []
        self.filled_orders: List[Order] = []
        self.cancelled_orders: List[Order] = []
        self.current_data: Dict[str, pd.DataFrame] = {}
        self.current_prices: Dict[str, float] = {}
        self.current_time: Optional[datetime] = None

    def run(self, show_progress: bool = True) -> PerformanceMetrics:
        """
        Run the backtest.

        Args:
            show_progress: Whether to show progress bar

        Returns:
            Performance metrics
        """
        print(f"Loading historical data for {len(self.symbols)} symbols...")

        # Load all historical data
        historical_data = self.data_manager.load_data(
            symbols=self.symbols,
            start_date=self.start_date,
            end_date=self.end_date,
            interval=self.interval
        )

        if not historical_data:
            raise ValueError("No historical data loaded")

        # Initialize strategy
        self.strategy.initialize(self.portfolio)

        # Get all unique timestamps across all symbols
        all_timestamps = set()
        for df in historical_data.values():
            all_timestamps.update(df.index)

        timestamps = sorted(all_timestamps)

        print(f"Running backtest from {self.start_date} to {self.end_date}")
        print(f"Total periods: {len(timestamps)}")

        # Event loop
        iterator = tqdm(timestamps) if show_progress else timestamps

        for timestamp in iterator:
            self.current_time = timestamp

            # Update current data and prices
            for symbol, df in historical_data.items():
                if timestamp in df.index:
                    # Get data up to current timestamp
                    self.current_data[symbol] = df.loc[:timestamp]
                    self.current_prices[symbol] = df.loc[timestamp, 'close']

            # Update portfolio prices
            self.portfolio.update_prices(self.current_prices, timestamp)

            # Process pending orders
            self._process_orders(timestamp)

            # Call strategy
            try:
                new_orders = []

                # Update strategy state
                self.strategy.current_time = timestamp
                self.strategy.current_data = self.current_data

                # Call strategy's on_data method
                result = self.strategy.on_data(self.current_data)

                # Handle returned orders
                if result is not None:
                    if isinstance(result, Order):
                        new_orders.append(result)
                    elif isinstance(result, list):
                        new_orders.extend(result)

                # Add new orders to pending
                for order in new_orders:
                    order.created_at = timestamp
                    self.pending_orders.append(order)

            except Exception as e:
                print(f"\nError in strategy at {timestamp}: {e}")
                raise

        # Close strategy
        self.strategy.on_stop()

        # Calculate performance metrics
        print("\nBacktest complete!")
        metrics = PerformanceMetrics(
            portfolio=self.portfolio,
            start_date=self.start_date,
            end_date=self.end_date,
            initial_capital=self.initial_capital
        )

        return metrics

    def _process_orders(self, timestamp: datetime) -> None:
        """
        Process pending orders.

        Args:
            timestamp: Current timestamp
        """
        remaining_orders = []

        for order in self.pending_orders:
            try:
                # Check if order can be filled
                if self._can_fill_order(order):
                    fill_price = self._get_fill_price(order)
                    commission = self._calculate_commission(order, fill_price)

                    # Fill the order
                    order.fill(order.quantity, fill_price, timestamp)

                    # Update portfolio
                    quantity_signed = (
                        order.quantity if order.side == OrderSide.BUY else -order.quantity
                    )

                    self.portfolio.update_position(
                        symbol=order.symbol,
                        quantity=quantity_signed,
                        price=fill_price,
                        commission=commission,
                        timestamp=timestamp
                    )

                    # Track filled order
                    self.filled_orders.append(order)

                    # Notify strategy
                    try:
                        self.strategy.on_order_filled(order)
                    except Exception as e:
                        print(f"Error in on_order_filled: {e}")

                else:
                    # Keep order pending
                    remaining_orders.append(order)

            except Exception as e:
                print(f"Error processing order {order.order_id}: {e}")
                order.status = OrderStatus.REJECTED
                remaining_orders.append(order)

        self.pending_orders = remaining_orders

    def _can_fill_order(self, order: Order) -> bool:
        """
        Check if an order can be filled at current price.

        Args:
            order: Order to check

        Returns:
            True if order can be filled
        """
        if order.symbol not in self.current_prices:
            return False

        current_price = self.current_prices[order.symbol]

        # Market orders can always be filled
        if order.order_type == OrderType.MARKET:
            return True

        # Limit orders
        if order.order_type == OrderType.LIMIT:
            if order.side == OrderSide.BUY:
                return current_price <= order.limit_price
            else:
                return current_price >= order.limit_price

        # Stop orders
        if order.order_type == OrderType.STOP:
            if order.side == OrderSide.BUY:
                return current_price >= order.stop_price
            else:
                return current_price <= order.stop_price

        return False

    def _get_fill_price(self, order: Order) -> float:
        """
        Get fill price for an order including slippage.

        Args:
            order: Order to fill

        Returns:
            Fill price
        """
        current_price = self.current_prices[order.symbol]

        # Apply slippage
        if order.side == OrderSide.BUY:
            fill_price = current_price * (1 + self.slippage)
        else:
            fill_price = current_price * (1 - self.slippage)

        # For limit orders, use limit price if better
        if order.order_type == OrderType.LIMIT:
            if order.side == OrderSide.BUY:
                fill_price = min(fill_price, order.limit_price)
            else:
                fill_price = max(fill_price, order.limit_price)

        return fill_price

    def _calculate_commission(self, order: Order, fill_price: float) -> float:
        """
        Calculate commission for an order.

        Args:
            order: Order
            fill_price: Fill price

        Returns:
            Commission amount
        """
        trade_value = order.quantity * fill_price
        return trade_value * self.commission

    def get_orders_df(self) -> pd.DataFrame:
        """
        Get all orders as a DataFrame.

        Returns:
            DataFrame with order history
        """
        if not self.filled_orders:
            return pd.DataFrame()

        orders_data = []
        for order in self.filled_orders:
            orders_data.append({
                'timestamp': order.filled_at,
                'symbol': order.symbol,
                'side': order.side.value,
                'quantity': order.quantity,
                'price': order.average_fill_price,
                'order_type': order.order_type.value,
                'status': order.status.value
            })

        df = pd.DataFrame(orders_data)
        if not df.empty and 'timestamp' in df.columns:
            df.set_index('timestamp', inplace=True)

        return df

    def summary(self) -> str:
        """
        Get backtest summary.

        Returns:
            Summary string
        """
        summary_lines = [
            "=" * 60,
            "BACKTEST SUMMARY",
            "=" * 60,
            f"Strategy: {self.strategy.name}",
            f"Period: {self.start_date.date()} to {self.end_date.date()}",
            f"Symbols: {', '.join(self.symbols)}",
            f"Initial Capital: ${self.initial_capital:,.2f}",
            "-" * 60,
            f"Final Equity: ${self.portfolio.total_equity():,.2f}",
            f"Total Return: {self.portfolio.total_return():.2f}%",
            f"Total P&L: ${self.portfolio.total_pnl():,.2f}",
            f"Realized P&L: ${self.portfolio.realized_pnl():,.2f}",
            f"Unrealized P&L: ${self.portfolio.unrealized_pnl():,.2f}",
            "-" * 60,
            f"Total Trades: {len(self.filled_orders)}",
            f"Open Positions: {len(self.portfolio.positions)}",
            f"Closed Positions: {len(self.portfolio.closed_positions)}",
            "=" * 60,
        ]

        return "\n".join(summary_lines)
