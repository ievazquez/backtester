"""Tests for technical indicators."""

import pytest
import pandas as pd
import numpy as np

from trading_platform.utils.indicators import (
    sma, ema, rsi, macd, bollinger_bands, atr
)


@pytest.fixture
def sample_price_data():
    """Create sample price data for testing."""
    np.random.seed(42)

    # Generate random walk price data
    returns = np.random.randn(100) * 0.02
    prices = 100 * (1 + returns).cumprod()

    return pd.Series(prices)


@pytest.fixture
def sample_ohlc_data():
    """Create sample OHLC data for testing."""
    np.random.seed(42)

    size = 100
    close = 100 * (1 + np.random.randn(size) * 0.02).cumprod()

    # High is close + random positive
    high = close + np.random.rand(size) * 2

    # Low is close - random positive
    low = close - np.random.rand(size) * 2

    # Open is somewhere between high and low
    open_price = low + (high - low) * np.random.rand(size)

    return pd.DataFrame({
        'open': open_price,
        'high': high,
        'low': low,
        'close': close
    })


class TestIndicators:
    """Test technical indicators."""

    def test_sma(self, sample_price_data):
        """Test Simple Moving Average."""
        result = sma(sample_price_data, 10)

        # Result should be a Series
        assert isinstance(result, pd.Series)

        # Should have same length as input
        assert len(result) == len(sample_price_data)

        # First 9 values should be NaN
        assert result.iloc[:9].isna().all()

        # Remaining values should not be NaN
        assert not result.iloc[9:].isna().any()

    def test_ema(self, sample_price_data):
        """Test Exponential Moving Average."""
        result = ema(sample_price_data, 10)

        assert isinstance(result, pd.Series)
        assert len(result) == len(sample_price_data)

        # EMA should react faster than SMA
        sma_result = sma(sample_price_data, 10)

        # Check that EMA differs from SMA
        assert not result.equals(sma_result)

    def test_rsi(self, sample_price_data):
        """Test Relative Strength Index."""
        result = rsi(sample_price_data, 14)

        assert isinstance(result, pd.Series)

        # RSI should be between 0 and 100
        valid_values = result.dropna()
        assert (valid_values >= 0).all()
        assert (valid_values <= 100).all()

    def test_macd(self, sample_price_data):
        """Test MACD indicator."""
        macd_line, signal_line, histogram = macd(sample_price_data)

        # All should be Series
        assert isinstance(macd_line, pd.Series)
        assert isinstance(signal_line, pd.Series)
        assert isinstance(histogram, pd.Series)

        # Histogram should be macd_line - signal_line
        diff = macd_line - signal_line
        assert diff.equals(histogram)

    def test_bollinger_bands(self, sample_price_data):
        """Test Bollinger Bands."""
        upper, middle, lower = bollinger_bands(sample_price_data, 20, 2.0)

        # All should be Series
        assert isinstance(upper, pd.Series)
        assert isinstance(middle, pd.Series)
        assert isinstance(lower, pd.Series)

        # Upper should be greater than middle
        valid_idx = ~middle.isna()
        assert (upper[valid_idx] >= middle[valid_idx]).all()

        # Middle should be greater than lower
        assert (middle[valid_idx] >= lower[valid_idx]).all()

    def test_atr(self, sample_ohlc_data):
        """Test Average True Range."""
        result = atr(
            sample_ohlc_data['high'],
            sample_ohlc_data['low'],
            sample_ohlc_data['close'],
            14
        )

        assert isinstance(result, pd.Series)

        # ATR should be positive
        valid_values = result.dropna()
        assert (valid_values >= 0).all()


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
