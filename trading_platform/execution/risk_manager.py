"""Risk management for live trading."""

from typing import Dict, Optional
from datetime import datetime, timedelta
import pandas as pd

from trading_platform.core.order import Order
from trading_platform.core.portfolio import Portfolio


class RiskManager:
    """
    Risk management system for live trading.

    Enforces position sizing, exposure limits, and stop-loss rules.
    """

    def __init__(
        self,
        max_position_size: float = 0.1,  # Max 10% per position
        max_portfolio_risk: float = 0.02,  # Max 2% portfolio risk per trade
        max_daily_loss: float = 0.05,  # Max 5% daily loss
        max_total_exposure: float = 1.0,  # Max 100% exposure
        enable_stops: bool = True,
    ):
        """
        Initialize risk manager.

        Args:
            max_position_size: Maximum position size as fraction of portfolio
            max_portfolio_risk: Maximum risk per trade as fraction of portfolio
            max_daily_loss: Maximum daily loss as fraction of portfolio
            max_total_exposure: Maximum total exposure as fraction of portfolio
            enable_stops: Whether to enable automatic stop-loss
        """
        self.max_position_size = max_position_size
        self.max_portfolio_risk = max_portfolio_risk
        self.max_daily_loss = max_daily_loss
        self.max_total_exposure = max_total_exposure
        self.enable_stops = enable_stops

        self._daily_pnl: Dict[str, float] = {}  # date -> pnl
        self._trade_count: Dict[str, int] = {}  # date -> count
        self._violations: list = []

    def validate_order(
        self,
        order: Order,
        portfolio: Portfolio,
        current_price: float
    ) -> tuple[bool, Optional[str]]:
        """
        Validate an order against risk rules.

        Args:
            order: Order to validate
            portfolio: Current portfolio
            current_price: Current market price

        Returns:
            Tuple of (is_valid, reason_if_invalid)
        """
        # Check daily loss limit
        if not self._check_daily_loss_limit(portfolio):
            reason = f"Daily loss limit exceeded ({self.max_daily_loss * 100}%)"
            self._record_violation(order, reason)
            return False, reason

        # Check position size
        if not self._check_position_size(order, portfolio, current_price):
            reason = f"Position size exceeds limit ({self.max_position_size * 100}%)"
            self._record_violation(order, reason)
            return False, reason

        # Check total exposure
        if not self._check_total_exposure(order, portfolio, current_price):
            reason = f"Total exposure exceeds limit ({self.max_total_exposure * 100}%)"
            self._record_violation(order, reason)
            return False, reason

        # Check account balance
        if not self._check_sufficient_capital(order, portfolio, current_price):
            reason = "Insufficient capital"
            self._record_violation(order, reason)
            return False, reason

        return True, None

    def calculate_position_size(
        self,
        symbol: str,
        portfolio: Portfolio,
        current_price: float,
        stop_loss_price: Optional[float] = None,
    ) -> float:
        """
        Calculate appropriate position size based on risk parameters.

        Args:
            symbol: Trading symbol
            portfolio: Current portfolio
            current_price: Current market price
            stop_loss_price: Stop loss price (if using)

        Returns:
            Recommended position size (quantity)
        """
        equity = portfolio.total_equity()

        # Method 1: Fixed percentage of portfolio
        max_value = equity * self.max_position_size
        quantity_by_size = max_value / current_price

        # Method 2: Risk-based sizing (if stop loss provided)
        if stop_loss_price is not None and self.enable_stops:
            risk_per_share = abs(current_price - stop_loss_price)
            if risk_per_share > 0:
                max_risk_amount = equity * self.max_portfolio_risk
                quantity_by_risk = max_risk_amount / risk_per_share

                # Use the more conservative size
                quantity = min(quantity_by_size, quantity_by_risk)
            else:
                quantity = quantity_by_size
        else:
            quantity = quantity_by_size

        return max(0, quantity)

    def update_daily_pnl(self, date: datetime, pnl: float) -> None:
        """
        Update daily P&L tracking.

        Args:
            date: Date
            pnl: P&L for the date
        """
        date_key = date.strftime("%Y-%m-%d")
        self._daily_pnl[date_key] = pnl

    def get_daily_pnl(self, date: datetime) -> float:
        """
        Get P&L for a specific date.

        Args:
            date: Date

        Returns:
            P&L for the date
        """
        date_key = date.strftime("%Y-%m-%d")
        return self._daily_pnl.get(date_key, 0.0)

    def reset_daily_tracking(self) -> None:
        """Reset daily tracking (call at start of each day)."""
        today = datetime.now().strftime("%Y-%m-%d")
        self._daily_pnl[today] = 0.0
        self._trade_count[today] = 0

    def get_violations(self) -> pd.DataFrame:
        """
        Get all risk violations.

        Returns:
            DataFrame with violation history
        """
        if not self._violations:
            return pd.DataFrame()

        return pd.DataFrame(self._violations)

    def _check_daily_loss_limit(self, portfolio: Portfolio) -> bool:
        """Check if daily loss limit has been exceeded."""
        today = datetime.now().strftime("%Y-%m-%d")
        daily_pnl = self._daily_pnl.get(today, 0.0)

        max_loss = portfolio.initial_capital * self.max_daily_loss

        return abs(daily_pnl) < max_loss if daily_pnl < 0 else True

    def _check_position_size(
        self,
        order: Order,
        portfolio: Portfolio,
        current_price: float
    ) -> bool:
        """Check if position size is within limits."""
        position_value = order.quantity * current_price
        max_position_value = portfolio.total_equity() * self.max_position_size

        return position_value <= max_position_value

    def _check_total_exposure(
        self,
        order: Order,
        portfolio: Portfolio,
        current_price: float
    ) -> bool:
        """Check if total exposure is within limits."""
        current_exposure = portfolio.positions_value()
        new_position_value = order.quantity * current_price
        total_exposure = current_exposure + new_position_value

        max_exposure = portfolio.total_equity() * self.max_total_exposure

        return total_exposure <= max_exposure

    def _check_sufficient_capital(
        self,
        order: Order,
        portfolio: Portfolio,
        current_price: float
    ) -> bool:
        """Check if there's sufficient capital for the order."""
        order_cost = order.quantity * current_price

        # Add some buffer for commissions
        required_capital = order_cost * 1.01

        return portfolio.cash >= required_capital

    def _record_violation(self, order: Order, reason: str) -> None:
        """Record a risk violation."""
        self._violations.append({
            'timestamp': datetime.now(),
            'order_id': order.order_id,
            'symbol': order.symbol,
            'side': order.side.value,
            'quantity': order.quantity,
            'reason': reason
        })

    def get_summary(self) -> Dict:
        """
        Get risk manager summary.

        Returns:
            Dictionary with risk statistics
        """
        return {
            'max_position_size_pct': self.max_position_size * 100,
            'max_portfolio_risk_pct': self.max_portfolio_risk * 100,
            'max_daily_loss_pct': self.max_daily_loss * 100,
            'max_total_exposure_pct': self.max_total_exposure * 100,
            'total_violations': len(self._violations),
            'daily_pnl': dict(self._daily_pnl),
            'trade_counts': dict(self._trade_count)
        }

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"RiskManager(max_pos={self.max_position_size*100}%, "
            f"max_risk={self.max_portfolio_risk*100}%, "
            f"violations={len(self._violations)})"
        )
