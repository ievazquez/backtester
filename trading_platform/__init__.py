"""
Trading Platform - A comprehensive Python-based trading platform
for backtesting and live trading.
"""

__version__ = "0.1.0"
__author__ = "Trading Platform Contributors"

from trading_platform.core.strategy import Strategy
from trading_platform.core.portfolio import Portfolio
from trading_platform.core.order import Order, OrderType, OrderSide
from trading_platform.core.position import Position

__all__ = [
    "Strategy",
    "Portfolio",
    "Order",
    "OrderType",
    "OrderSide",
    "Position",
]
