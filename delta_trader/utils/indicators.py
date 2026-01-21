"""
Simple technical indicators.
No external TA libraries - implement from scratch for transparency.
"""

import pandas as pd
import numpy as np


def ema(series: pd.Series, period: int) -> pd.Series:
    """Exponential Moving Average."""
    return series.ewm(span=period, adjust=False).mean()


def sma(series: pd.Series, period: int) -> pd.Series:
    """Simple Moving Average."""
    return series.rolling(window=period).mean()


def rsi(series: pd.Series, period: int = 14) -> pd.Series:
    """Relative Strength Index."""
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))


def atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
    """Average True Range."""
    tr1 = high - low
    tr2 = abs(high - close.shift())
    tr3 = abs(low - close.shift())
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
    return tr.rolling(window=period).mean()


def bollinger_bands(series: pd.Series, period: int = 20, std_dev: int = 2) -> tuple:
    """Bollinger Bands. Returns (upper, middle, lower, width)."""
    middle = sma(series, period)
    std = series.rolling(window=period).std()
    upper = middle + (std * std_dev)
    lower = middle - (std * std_dev)
    width = (upper - lower) / middle
    return upper, middle, lower, width


def rolling_high(series: pd.Series, period: int) -> pd.Series:
    """Rolling highest high."""
    return series.rolling(window=period).max()


def rolling_low(series: pd.Series, period: int) -> pd.Series:
    """Rolling lowest low."""
    return series.rolling(window=period).min()


def returns(series: pd.Series, period: int = 1) -> pd.Series:
    """Calculate returns over period."""
    return series.pct_change(periods=period)


def percentile_rank(series: pd.Series, period: int) -> pd.Series:
    """Current value's percentile rank over lookback period."""
    def calc_percentile(window):
        if len(window) < period:
            return np.nan
        return (window.iloc[-1] > window.iloc[:-1]).sum() / (len(window) - 1) * 100
    return series.rolling(window=period).apply(calc_percentile, raw=False)
