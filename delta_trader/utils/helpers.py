"""
Utility helper functions.
"""

from datetime import datetime, timedelta
import time
from typing import Optional


def timestamp_to_datetime(ts: int) -> datetime:
    """Convert Unix timestamp to datetime."""
    return datetime.fromtimestamp(ts)


def datetime_to_timestamp(dt: datetime) -> int:
    """Convert datetime to Unix timestamp."""
    return int(dt.timestamp())


def format_price(price: float, decimals: int = 4) -> str:
    """Format price for display."""
    return f"{price:.{decimals}f}"


def format_pnl(pnl: float, pct: float) -> str:
    """Format P&L for display."""
    sign = "+" if pnl >= 0 else ""
    return f"{sign}₹{pnl:.2f} ({sign}{pct:.2%})"


def retry_with_backoff(func, max_retries: int = 4, initial_delay: float = 2.0):
    """
    Retry a function with exponential backoff.
    Used for network operations that may fail transiently.
    """
    for attempt in range(max_retries):
        try:
            return func()
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            delay = initial_delay * (2 ** attempt)
            print(f"Attempt {attempt + 1} failed: {e}. Retrying in {delay}s...")
            time.sleep(delay)


def validate_timeframe(timeframe: str) -> bool:
    """Validate if timeframe is supported."""
    valid_timeframes = ["1m", "5m", "15m", "30m", "1h", "2h", "4h", "1d", "1w"]
    return timeframe in valid_timeframes


def calculate_duration_minutes(start: datetime, end: datetime) -> int:
    """Calculate duration in minutes between two datetimes."""
    return int((end - start).total_seconds() / 60)


def round_to_precision(value: float, precision: int = 8) -> float:
    """Round value to specified precision."""
    return round(value, precision)


def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """Safely divide two numbers, returning default if denominator is zero."""
    if denominator == 0:
        return default
    return numerator / denominator
