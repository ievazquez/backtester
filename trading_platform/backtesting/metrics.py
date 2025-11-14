"""Performance metrics calculation for backtesting."""

import numpy as np
import pandas as pd
from typing import Dict, Optional
from datetime import datetime

from trading_platform.core.portfolio import Portfolio


class PerformanceMetrics:
    """
    Calculate and store performance metrics for a backtest.

    Provides comprehensive analytics including returns, risk metrics,
    and drawdown analysis.
    """

    def __init__(
        self,
        portfolio: Portfolio,
        start_date: datetime,
        end_date: datetime,
        initial_capital: float,
        risk_free_rate: float = 0.02,  # 2% annual risk-free rate
    ):
        """
        Initialize performance metrics.

        Args:
            portfolio: Portfolio to analyze
            start_date: Backtest start date
            end_date: Backtest end date
            initial_capital: Initial capital
            risk_free_rate: Annual risk-free rate for Sharpe ratio
        """
        self.portfolio = portfolio
        self.start_date = start_date
        self.end_date = end_date
        self.initial_capital = initial_capital
        self.risk_free_rate = risk_free_rate

        # Get equity curve
        self.equity_curve = portfolio.get_equity_curve_df()

        # Calculate metrics
        self._calculate_metrics()

    def _calculate_metrics(self) -> None:
        """Calculate all performance metrics."""
        if self.equity_curve.empty:
            self.metrics = {}
            return

        equity = self.equity_curve['equity']

        # Returns
        self.total_return = ((equity.iloc[-1] - self.initial_capital) / self.initial_capital) * 100
        self.daily_returns = equity.pct_change().dropna()

        # Annualized metrics
        trading_days = len(equity)
        years = (self.end_date - self.start_date).days / 365.25

        if years > 0:
            self.annualized_return = ((equity.iloc[-1] / self.initial_capital) ** (1 / years) - 1) * 100
        else:
            self.annualized_return = 0.0

        # Volatility
        if len(self.daily_returns) > 1:
            self.volatility = self.daily_returns.std() * np.sqrt(252) * 100  # Annualized
        else:
            self.volatility = 0.0

        # Sharpe ratio
        if self.volatility > 0:
            excess_return = self.annualized_return - (self.risk_free_rate * 100)
            self.sharpe_ratio = excess_return / self.volatility
        else:
            self.sharpe_ratio = 0.0

        # Sortino ratio (uses downside deviation)
        downside_returns = self.daily_returns[self.daily_returns < 0]
        if len(downside_returns) > 1:
            downside_std = downside_returns.std() * np.sqrt(252) * 100
            if downside_std > 0:
                self.sortino_ratio = (self.annualized_return - (self.risk_free_rate * 100)) / downside_std
            else:
                self.sortino_ratio = 0.0
        else:
            self.sortino_ratio = 0.0

        # Drawdown analysis
        self._calculate_drawdown()

        # Win/Loss statistics
        self._calculate_win_loss_stats()

    def _calculate_drawdown(self) -> None:
        """Calculate drawdown metrics."""
        if self.equity_curve.empty:
            self.max_drawdown = 0.0
            self.max_drawdown_duration = 0
            self.current_drawdown = 0.0
            return

        equity = self.equity_curve['equity']

        # Calculate running maximum
        running_max = equity.expanding().max()

        # Calculate drawdown
        drawdown = (equity - running_max) / running_max * 100
        self.drawdown_series = drawdown

        # Maximum drawdown
        self.max_drawdown = abs(drawdown.min())

        # Maximum drawdown duration
        is_drawdown = drawdown < 0
        drawdown_periods = (is_drawdown != is_drawdown.shift()).cumsum()
        drawdown_durations = is_drawdown.groupby(drawdown_periods).sum()
        self.max_drawdown_duration = int(drawdown_durations.max()) if len(drawdown_durations) > 0 else 0

        # Current drawdown
        self.current_drawdown = abs(drawdown.iloc[-1]) if len(drawdown) > 0 else 0.0

    def _calculate_win_loss_stats(self) -> None:
        """Calculate win/loss statistics from closed positions."""
        closed_positions = self.portfolio.closed_positions

        if not closed_positions:
            self.win_rate = 0.0
            self.avg_win = 0.0
            self.avg_loss = 0.0
            self.profit_factor = 0.0
            self.num_winners = 0
            self.num_losers = 0
            return

        pnls = [pos.realized_pnl for pos in closed_positions]
        winners = [pnl for pnl in pnls if pnl > 0]
        losers = [pnl for pnl in pnls if pnl < 0]

        self.num_winners = len(winners)
        self.num_losers = len(losers)
        total_trades = len(pnls)

        # Win rate
        self.win_rate = (self.num_winners / total_trades * 100) if total_trades > 0 else 0.0

        # Average win/loss
        self.avg_win = np.mean(winners) if winners else 0.0
        self.avg_loss = abs(np.mean(losers)) if losers else 0.0

        # Profit factor
        total_wins = sum(winners) if winners else 0.0
        total_losses = abs(sum(losers)) if losers else 0.0
        self.profit_factor = (total_wins / total_losses) if total_losses > 0 else 0.0

    def get_metrics(self) -> Dict:
        """
        Get all metrics as a dictionary.

        Returns:
            Dictionary of performance metrics
        """
        return {
            'initial_capital': self.initial_capital,
            'final_equity': self.portfolio.total_equity(),
            'total_return_pct': self.total_return,
            'annualized_return_pct': self.annualized_return,
            'volatility_pct': self.volatility,
            'sharpe_ratio': self.sharpe_ratio,
            'sortino_ratio': self.sortino_ratio,
            'max_drawdown_pct': self.max_drawdown,
            'max_drawdown_duration': self.max_drawdown_duration,
            'current_drawdown_pct': self.current_drawdown,
            'total_pnl': self.portfolio.total_pnl(),
            'realized_pnl': self.portfolio.realized_pnl(),
            'unrealized_pnl': self.portfolio.unrealized_pnl(),
            'win_rate_pct': self.win_rate,
            'num_winners': self.num_winners,
            'num_losers': self.num_losers,
            'avg_win': self.avg_win,
            'avg_loss': self.avg_loss,
            'profit_factor': self.profit_factor,
            'total_trades': len(self.portfolio.closed_positions),
            'open_positions': len(self.portfolio.positions),
        }

    def summary(self) -> str:
        """
        Get formatted summary of metrics.

        Returns:
            Formatted summary string
        """
        metrics = self.get_metrics()

        summary_lines = [
            "=" * 70,
            "PERFORMANCE METRICS",
            "=" * 70,
            "",
            "RETURNS",
            "-" * 70,
            f"  Initial Capital:        ${metrics['initial_capital']:>15,.2f}",
            f"  Final Equity:           ${metrics['final_equity']:>15,.2f}",
            f"  Total Return:           {metrics['total_return_pct']:>15.2f}%",
            f"  Annualized Return:      {metrics['annualized_return_pct']:>15.2f}%",
            f"  Total P&L:              ${metrics['total_pnl']:>15,.2f}",
            "",
            "RISK METRICS",
            "-" * 70,
            f"  Volatility (Ann.):      {metrics['volatility_pct']:>15.2f}%",
            f"  Sharpe Ratio:           {metrics['sharpe_ratio']:>15.2f}",
            f"  Sortino Ratio:          {metrics['sortino_ratio']:>15.2f}",
            f"  Max Drawdown:           {metrics['max_drawdown_pct']:>15.2f}%",
            f"  Max DD Duration:        {metrics['max_drawdown_duration']:>15} days",
            f"  Current Drawdown:       {metrics['current_drawdown_pct']:>15.2f}%",
            "",
            "TRADING STATISTICS",
            "-" * 70,
            f"  Total Trades:           {metrics['total_trades']:>15}",
            f"  Winners:                {metrics['num_winners']:>15}",
            f"  Losers:                 {metrics['num_losers']:>15}",
            f"  Win Rate:               {metrics['win_rate_pct']:>15.2f}%",
            f"  Average Win:            ${metrics['avg_win']:>15,.2f}",
            f"  Average Loss:           ${metrics['avg_loss']:>15,.2f}",
            f"  Profit Factor:          {metrics['profit_factor']:>15.2f}",
            f"  Open Positions:         {metrics['open_positions']:>15}",
            "=" * 70,
        ]

        return "\n".join(summary_lines)

    def plot_equity_curve(self, save_path: Optional[str] = None) -> None:
        """
        Plot equity curve.

        Args:
            save_path: Path to save plot (optional)
        """
        try:
            import matplotlib.pyplot as plt

            fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), sharex=True)

            # Equity curve
            self.equity_curve['equity'].plot(ax=ax1, label='Portfolio Equity')
            ax1.axhline(y=self.initial_capital, color='r', linestyle='--', label='Initial Capital')
            ax1.set_ylabel('Equity ($)')
            ax1.set_title('Portfolio Equity Curve')
            ax1.legend()
            ax1.grid(True)

            # Drawdown
            self.drawdown_series.plot(ax=ax2, color='red', label='Drawdown')
            ax2.fill_between(self.drawdown_series.index, self.drawdown_series, 0, alpha=0.3, color='red')
            ax2.set_ylabel('Drawdown (%)')
            ax2.set_xlabel('Date')
            ax2.set_title('Drawdown')
            ax2.legend()
            ax2.grid(True)

            plt.tight_layout()

            if save_path:
                plt.savefig(save_path)
                print(f"Plot saved to {save_path}")
            else:
                plt.show()

        except ImportError:
            print("matplotlib is required for plotting. Install with: pip install matplotlib")

    def plot_returns_distribution(self, save_path: Optional[str] = None) -> None:
        """
        Plot returns distribution.

        Args:
            save_path: Path to save plot (optional)
        """
        try:
            import matplotlib.pyplot as plt

            fig, ax = plt.subplots(figsize=(10, 6))

            self.daily_returns.hist(bins=50, ax=ax, alpha=0.7, edgecolor='black')
            ax.axvline(x=self.daily_returns.mean(), color='r', linestyle='--', label='Mean')
            ax.axvline(x=0, color='black', linestyle='-', linewidth=0.5)
            ax.set_xlabel('Daily Return')
            ax.set_ylabel('Frequency')
            ax.set_title('Distribution of Daily Returns')
            ax.legend()
            ax.grid(True, alpha=0.3)

            plt.tight_layout()

            if save_path:
                plt.savefig(save_path)
                print(f"Plot saved to {save_path}")
            else:
                plt.show()

        except ImportError:
            print("matplotlib is required for plotting. Install with: pip install matplotlib")

    def __repr__(self) -> str:
        """String representation."""
        return f"PerformanceMetrics(return={self.total_return:.2f}%, sharpe={self.sharpe_ratio:.2f})"
