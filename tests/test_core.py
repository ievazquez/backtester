"""Tests for core components."""

import pytest
from datetime import datetime

from trading_platform.core.order import Order, OrderType, OrderSide, OrderStatus
from trading_platform.core.position import Position
from trading_platform.core.portfolio import Portfolio


class TestOrder:
    """Test Order class."""

    def test_create_market_order(self):
        """Test creating a market order."""
        order = Order(
            symbol='AAPL',
            side=OrderSide.BUY,
            quantity=100,
            order_type=OrderType.MARKET
        )

        assert order.symbol == 'AAPL'
        assert order.side == OrderSide.BUY
        assert order.quantity == 100
        assert order.status == OrderStatus.PENDING

    def test_create_limit_order(self):
        """Test creating a limit order."""
        order = Order(
            symbol='AAPL',
            side=OrderSide.BUY,
            quantity=100,
            order_type=OrderType.LIMIT,
            limit_price=150.00
        )

        assert order.limit_price == 150.00

    def test_fill_order(self):
        """Test filling an order."""
        order = Order(
            symbol='AAPL',
            side=OrderSide.BUY,
            quantity=100,
            order_type=OrderType.MARKET
        )

        order.fill(100, 150.50)

        assert order.is_filled()
        assert order.filled_quantity == 100
        assert order.average_fill_price == 150.50

    def test_partial_fill(self):
        """Test partial order fill."""
        order = Order(
            symbol='AAPL',
            side=OrderSide.BUY,
            quantity=100,
            order_type=OrderType.MARKET
        )

        order.fill(50, 150.50)

        assert not order.is_filled()
        assert order.status == OrderStatus.PARTIALLY_FILLED
        assert order.filled_quantity == 50

    def test_cancel_order(self):
        """Test cancelling an order."""
        order = Order(
            symbol='AAPL',
            side=OrderSide.BUY,
            quantity=100
        )

        order.cancel()

        assert order.status == OrderStatus.CANCELLED


class TestPosition:
    """Test Position class."""

    def test_create_position(self):
        """Test creating a position."""
        pos = Position(symbol='AAPL')

        assert pos.symbol == 'AAPL'
        assert pos.quantity == 0
        assert pos.is_closed()

    def test_open_long_position(self):
        """Test opening a long position."""
        pos = Position(symbol='AAPL')
        pos.update(100, 150.00)

        assert pos.quantity == 100
        assert pos.average_price == 150.00
        assert pos.is_long()
        assert not pos.is_closed()

    def test_open_short_position(self):
        """Test opening a short position."""
        pos = Position(symbol='AAPL')
        pos.update(-100, 150.00)

        assert pos.quantity == -100
        assert pos.is_short()

    def test_close_position(self):
        """Test closing a position."""
        pos = Position(symbol='AAPL')

        # Open long
        pos.update(100, 150.00)

        # Close
        pos.update(-100, 155.00)

        assert pos.is_closed()
        assert pos.quantity == 0

        # Should have profit
        assert pos.realized_pnl > 0

    def test_unrealized_pnl(self):
        """Test unrealized P&L calculation."""
        pos = Position(symbol='AAPL')
        pos.update(100, 150.00)

        # Update current price
        pos.current_price = 155.00

        upnl = pos.unrealized_pnl()
        assert upnl == 500.00  # (155 - 150) * 100


class TestPortfolio:
    """Test Portfolio class."""

    def test_create_portfolio(self):
        """Test creating a portfolio."""
        portfolio = Portfolio(initial_capital=100000)

        assert portfolio.initial_capital == 100000
        assert portfolio.cash == 100000
        assert portfolio.total_equity() == 100000

    def test_update_position(self):
        """Test updating a position."""
        portfolio = Portfolio(initial_capital=100000)

        # Buy 100 shares at $150
        portfolio.update_position('AAPL', 100, 150.00, commission=1.50)

        assert portfolio.has_position('AAPL')

        position = portfolio.get_position('AAPL')
        assert position.quantity == 100
        assert position.average_price == 150.00

        # Cash should decrease
        assert portfolio.cash < 100000

    def test_close_position(self):
        """Test closing a position."""
        portfolio = Portfolio(initial_capital=100000)

        # Open position
        portfolio.update_position('AAPL', 100, 150.00, commission=1.50)

        # Close position
        portfolio.update_position('AAPL', -100, 155.00, commission=1.50)

        # Position should be closed
        assert not portfolio.has_position('AAPL')

        # Should have profit (minus commissions)
        assert portfolio.total_pnl() > 0

    def test_multiple_positions(self):
        """Test managing multiple positions."""
        portfolio = Portfolio(initial_capital=100000)

        portfolio.update_position('AAPL', 100, 150.00)
        portfolio.update_position('GOOGL', 50, 2000.00)

        assert len(portfolio.positions) == 2
        assert portfolio.has_position('AAPL')
        assert portfolio.has_position('GOOGL')

    def test_portfolio_return(self):
        """Test portfolio return calculation."""
        portfolio = Portfolio(initial_capital=100000)

        # Buy and sell for profit
        portfolio.update_position('AAPL', 100, 150.00)

        # Update prices
        portfolio.update_prices({'AAPL': 155.00})

        # Should show positive return
        assert portfolio.total_return() > 0


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
