"""Technical indicators for strategy development."""

import pandas as pd
import numpy as np
from typing import Tuple


def sma(data: pd.Series, period: int) -> pd.Series:
    """
    Simple Moving Average.

    Args:
        data: Price data
        period: Period for moving average

    Returns:
        SMA series
    """
    return data.rolling(window=period).mean()


def ema(data: pd.Series, period: int) -> pd.Series:
    """
    Exponential Moving Average.

    Args:
        data: Price data
        period: Period for moving average

    Returns:
        EMA series
    """
    return data.ewm(span=period, adjust=False).mean()


def rsi(data: pd.Series, period: int = 14) -> pd.Series:
    """
    Relative Strength Index.

    Args:
        data: Price data
        period: RSI period (default 14)

    Returns:
        RSI series (0-100)
    """
    delta = data.diff()

    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()

    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))

    return rsi


def macd(
    data: pd.Series,
    fast_period: int = 12,
    slow_period: int = 26,
    signal_period: int = 9
) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """
    Moving Average Convergence Divergence.

    Args:
        data: Price data
        fast_period: Fast EMA period (default 12)
        slow_period: Slow EMA period (default 26)
        signal_period: Signal line period (default 9)

    Returns:
        Tuple of (macd_line, signal_line, histogram)
    """
    fast_ema = ema(data, fast_period)
    slow_ema = ema(data, slow_period)

    macd_line = fast_ema - slow_ema
    signal_line = ema(macd_line, signal_period)
    histogram = macd_line - signal_line

    return macd_line, signal_line, histogram


def bollinger_bands(
    data: pd.Series,
    period: int = 20,
    num_std: float = 2.0
) -> Tuple[pd.Series, pd.Series, pd.Series]:
    """
    Bollinger Bands.

    Args:
        data: Price data
        period: Period for moving average (default 20)
        num_std: Number of standard deviations (default 2.0)

    Returns:
        Tuple of (upper_band, middle_band, lower_band)
    """
    middle_band = sma(data, period)
    std = data.rolling(window=period).std()

    upper_band = middle_band + (std * num_std)
    lower_band = middle_band - (std * num_std)

    return upper_band, middle_band, lower_band


def atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
    """
    Average True Range.

    Args:
        high: High prices
        low: Low prices
        close: Close prices
        period: ATR period (default 14)

    Returns:
        ATR series
    """
    high_low = high - low
    high_close = abs(high - close.shift())
    low_close = abs(low - close.shift())

    true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    atr = true_range.rolling(window=period).mean()

    return atr


def stochastic(
    high: pd.Series,
    low: pd.Series,
    close: pd.Series,
    k_period: int = 14,
    d_period: int = 3
) -> Tuple[pd.Series, pd.Series]:
    """
    Stochastic Oscillator.

    Args:
        high: High prices
        low: Low prices
        close: Close prices
        k_period: %K period (default 14)
        d_period: %D period (default 3)

    Returns:
        Tuple of (%K, %D)
    """
    lowest_low = low.rolling(window=k_period).min()
    highest_high = high.rolling(window=k_period).max()

    k_percent = 100 * (close - lowest_low) / (highest_high - lowest_low)
    d_percent = k_percent.rolling(window=d_period).mean()

    return k_percent, d_percent


def obv(close: pd.Series, volume: pd.Series) -> pd.Series:
    """
    On-Balance Volume.

    Args:
        close: Close prices
        volume: Volume data

    Returns:
        OBV series
    """
    obv = (np.sign(close.diff()) * volume).fillna(0).cumsum()
    return obv


def adx(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
    """
    Average Directional Index.

    Args:
        high: High prices
        low: Low prices
        close: Close prices
        period: ADX period (default 14)

    Returns:
        ADX series
    """
    # Calculate True Range
    tr = atr(high, low, close, 1)

    # Directional Movement
    up_move = high.diff()
    down_move = -low.diff()

    plus_dm = up_move.where((up_move > down_move) & (up_move > 0), 0)
    minus_dm = down_move.where((down_move > up_move) & (down_move > 0), 0)

    # Smoothed indicators
    atr_smooth = tr.rolling(window=period).mean()
    plus_di = 100 * (plus_dm.rolling(window=period).mean() / atr_smooth)
    minus_di = 100 * (minus_dm.rolling(window=period).mean() / atr_smooth)

    # ADX
    dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
    adx = dx.rolling(window=period).mean()

    return adx
