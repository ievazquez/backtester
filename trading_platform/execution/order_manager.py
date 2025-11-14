"""Order management for live trading."""

from typing import Dict, List, Optional, Callable
from datetime import datetime
import threading
import time

from trading_platform.core.order import Order, OrderStatus
from trading_platform.brokers.base import BrokerAdapter


class OrderManager:
    """
    Manages order execution and tracking for live trading.

    Handles order submission, monitoring, and callbacks.
    """

    def __init__(self, broker: BrokerAdapter):
        """
        Initialize order manager.

        Args:
            broker: Broker adapter to use for order execution
        """
        self.broker = broker
        self.orders: Dict[str, Order] = {}  # order_id -> Order
        self.broker_order_ids: Dict[str, str] = {}  # our_id -> broker_id
        self.pending_orders: List[Order] = []
        self.filled_orders: List[Order] = []
        self.cancelled_orders: List[Order] = []

        self._callbacks: Dict[str, List[Callable]] = {
            'on_fill': [],
            'on_cancel': [],
            'on_reject': []
        }

        self._monitoring_thread: Optional[threading.Thread] = None
        self._stop_monitoring = threading.Event()

    def submit_order(self, order: Order) -> str:
        """
        Submit an order to the broker.

        Args:
            order: Order to submit

        Returns:
            Order ID
        """
        try:
            # Submit to broker
            broker_order_id = self.broker.submit_order(order)

            # Track order
            self.orders[order.order_id] = order
            self.broker_order_ids[order.order_id] = broker_order_id
            self.pending_orders.append(order)

            order.status = OrderStatus.SUBMITTED

            print(f"Order submitted: {order.symbol} {order.side.value} {order.quantity} @ {order.order_type.value}")

            return order.order_id

        except Exception as e:
            print(f"Error submitting order: {e}")
            order.status = OrderStatus.REJECTED
            self._trigger_callbacks('on_reject', order)
            raise

    def cancel_order(self, order_id: str) -> bool:
        """
        Cancel an order.

        Args:
            order_id: Order ID to cancel

        Returns:
            True if cancellation successful
        """
        if order_id not in self.orders:
            print(f"Order {order_id} not found")
            return False

        order = self.orders[order_id]
        broker_order_id = self.broker_order_ids.get(order_id)

        if broker_order_id is None:
            print(f"Broker order ID not found for {order_id}")
            return False

        try:
            success = self.broker.cancel_order(broker_order_id)

            if success:
                order.cancel()
                self.pending_orders.remove(order)
                self.cancelled_orders.append(order)

                self._trigger_callbacks('on_cancel', order)

                print(f"Order cancelled: {order_id}")

            return success

        except Exception as e:
            print(f"Error cancelling order: {e}")
            return False

    def get_order(self, order_id: str) -> Optional[Order]:
        """
        Get an order by ID.

        Args:
            order_id: Order ID

        Returns:
            Order if found, None otherwise
        """
        return self.orders.get(order_id)

    def get_pending_orders(self) -> List[Order]:
        """
        Get all pending orders.

        Returns:
            List of pending orders
        """
        return self.pending_orders.copy()

    def get_filled_orders(self) -> List[Order]:
        """
        Get all filled orders.

        Returns:
            List of filled orders
        """
        return self.filled_orders.copy()

    def start_monitoring(self, interval: float = 1.0) -> None:
        """
        Start monitoring order status.

        Args:
            interval: Check interval in seconds
        """
        if self._monitoring_thread is not None and self._monitoring_thread.is_alive():
            print("Monitoring already started")
            return

        self._stop_monitoring.clear()

        def monitor_loop():
            while not self._stop_monitoring.is_set():
                self._update_order_statuses()
                time.sleep(interval)

        self._monitoring_thread = threading.Thread(target=monitor_loop, daemon=True)
        self._monitoring_thread.start()

        print("Order monitoring started")

    def stop_monitoring(self) -> None:
        """Stop monitoring order status."""
        if self._monitoring_thread is None:
            return

        self._stop_monitoring.set()
        self._monitoring_thread.join(timeout=5)
        self._monitoring_thread = None

        print("Order monitoring stopped")

    def register_callback(self, event: str, callback: Callable[[Order], None]) -> None:
        """
        Register a callback for order events.

        Args:
            event: Event type ('on_fill', 'on_cancel', 'on_reject')
            callback: Callback function
        """
        if event in self._callbacks:
            self._callbacks[event].append(callback)

    def _update_order_statuses(self) -> None:
        """Update status of all pending orders."""
        for order in self.pending_orders.copy():
            try:
                broker_order_id = self.broker_order_ids.get(order.order_id)
                if broker_order_id is None:
                    continue

                # Get status from broker
                status = self.broker.get_order_status(broker_order_id)

                # Update order status
                if status == OrderStatus.FILLED and order.status != OrderStatus.FILLED:
                    order.status = OrderStatus.FILLED
                    order.filled_at = datetime.now()

                    # Move to filled orders
                    self.pending_orders.remove(order)
                    self.filled_orders.append(order)

                    self._trigger_callbacks('on_fill', order)

                    print(f"Order filled: {order.symbol} {order.side.value} {order.quantity}")

                elif status == OrderStatus.CANCELLED and order.status != OrderStatus.CANCELLED:
                    order.status = OrderStatus.CANCELLED

                    # Move to cancelled orders
                    self.pending_orders.remove(order)
                    self.cancelled_orders.append(order)

                    self._trigger_callbacks('on_cancel', order)

            except Exception as e:
                print(f"Error updating order status: {e}")

    def _trigger_callbacks(self, event: str, order: Order) -> None:
        """Trigger callbacks for an event."""
        for callback in self._callbacks.get(event, []):
            try:
                callback(order)
            except Exception as e:
                print(f"Error in callback: {e}")

    def get_summary(self) -> Dict:
        """
        Get order manager summary.

        Returns:
            Dictionary with order statistics
        """
        return {
            'total_orders': len(self.orders),
            'pending_orders': len(self.pending_orders),
            'filled_orders': len(self.filled_orders),
            'cancelled_orders': len(self.cancelled_orders),
            'monitoring_active': self._monitoring_thread is not None and self._monitoring_thread.is_alive()
        }

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"OrderManager(total={len(self.orders)}, "
            f"pending={len(self.pending_orders)}, "
            f"filled={len(self.filled_orders)})"
        )
