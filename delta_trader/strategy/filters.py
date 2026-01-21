"""
Market condition filters for trade validation.
Includes trend detection, volatility checks, and other quality filters.
"""

import pandas as pd
import numpy as np
from typing import Optional, Dict, Tuple
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.indicators import ema, atr
from config.settings import (
    TREND_FILTER_ENABLED, TREND_EMA_FAST, TREND_EMA_SLOW,
    TREND_THRESHOLD_PCT, RANGING_ZONE_PCT, TREND_TRADING_RULES,
    VOLATILITY_FILTER_ENABLED, MIN_ATR_PERCENTILE,
    MIN_CANDLE_RANGE_PCT, MIN_RECENT_MOVEMENT_CANDLES,
    FEATURES
)


class MarketFilters:
    """
    Validates market conditions before allowing trades.

    - Trend filter: Only trade in direction of higher timeframe trend
    - Volatility filter: Skip dead/ranging markets
    - Quality filters: Ensure setup conditions are met
    """

    def __init__(self):
        self.trend_filter_enabled = FEATURES.get("trend_filter", TREND_FILTER_ENABLED)
        self.volatility_filter_enabled = FEATURES.get("volatility_filter", VOLATILITY_FILTER_ENABLED)

    def get_trend_state(self, df: pd.DataFrame) -> str:
        """
        Determine market trend state.

        Args:
            df: OHLCV DataFrame (should be 1H timeframe)

        Returns:
            "uptrend", "downtrend", or "ranging"
        """
        if len(df) < TREND_EMA_SLOW:
            return "ranging"  # Not enough data

        close = df["close"]
        ema_fast = ema(close, TREND_EMA_FAST).iloc[-1]
        ema_slow = ema(close, TREND_EMA_SLOW).iloc[-1]

        # Calculate difference
        diff_pct = (ema_fast - ema_slow) / ema_slow

        # Determine trend
        if abs(diff_pct) < RANGING_ZONE_PCT:
            return "ranging"
        elif diff_pct > TREND_THRESHOLD_PCT:
            return "uptrend"
        elif diff_pct < -TREND_THRESHOLD_PCT:
            return "downtrend"
        else:
            return "ranging"

    def is_direction_allowed(self, direction: str, trend_state: str) -> bool:
        """
        Check if trade direction is allowed in current trend.

        Args:
            direction: "LONG" or "SHORT"
            trend_state: "uptrend", "downtrend", or "ranging"

        Returns:
            True if direction is allowed
        """
        if not self.trend_filter_enabled:
            return True

        allowed_directions = TREND_TRADING_RULES.get(trend_state, [])
        return direction in allowed_directions

    def check_volatility(self, df: pd.DataFrame) -> Tuple[bool, str]:
        """
        Check if market has sufficient volatility.

        Args:
            df: OHLCV DataFrame (15m timeframe)

        Returns:
            (passed: bool, reason: str)
        """
        if not self.volatility_filter_enabled:
            return True, "Volatility filter disabled"

        if len(df) < 50:
            return False, "Insufficient data for volatility check"

        # Check 1: ATR percentile
        close = df["close"]
        atr_values = atr(df, 14)

        if len(atr_values) < 50:
            return False, "Insufficient ATR data"

        current_atr = atr_values.iloc[-1]
        atr_percentile = (atr_values.iloc[-50:] < current_atr).sum() / 50 * 100

        if atr_percentile < MIN_ATR_PERCENTILE:
            return False, f"ATR too low (percentile: {atr_percentile:.1f}%, need {MIN_ATR_PERCENTILE}%)"

        # Check 2: Recent price movement
        recent_candles = df.iloc[-MIN_RECENT_MOVEMENT_CANDLES:]
        total_range = (recent_candles["high"].max() - recent_candles["low"].min())
        range_pct = total_range / recent_candles["close"].iloc[-1]

        if range_pct < MIN_CANDLE_RANGE_PCT:
            return False, f"Dead market: last {MIN_RECENT_MOVEMENT_CANDLES} candles moved only {range_pct:.3%}"

        return True, "Volatility check passed"

    def validate_setup(
        self,
        df_15m: pd.DataFrame,
        df_1h: pd.DataFrame,
        direction: str
    ) -> Tuple[bool, str, Optional[Dict]]:
        """
        Complete validation check for a setup.

        Args:
            df_15m: 15-minute OHLCV data
            df_1h: 1-hour OHLCV data for trend
            direction: "LONG" or "SHORT"

        Returns:
            (allowed: bool, reason: str, metadata: dict)
        """
        metadata = {}

        # 1. Check trend
        trend_state = self.get_trend_state(df_1h)
        metadata["trend_state"] = trend_state

        if not self.is_direction_allowed(direction, trend_state):
            return False, f"Direction {direction} not allowed in {trend_state}", metadata

        # 2. Check volatility
        vol_passed, vol_reason = self.check_volatility(df_15m)
        metadata["volatility_check"] = vol_reason

        if not vol_passed:
            return False, vol_reason, metadata

        # All checks passed
        return True, "All filters passed", metadata

    def get_trend_multiplier(self, trend_state: str) -> float:
        """
        Get position size multiplier based on trend strength.

        Args:
            trend_state: "uptrend", "downtrend", or "ranging"

        Returns:
            Multiplier (0.0 to 1.0)
        """
        from config.settings import TREND_MULTIPLIERS

        if trend_state in ["uptrend", "downtrend"]:
            return TREND_MULTIPLIERS.get("strong_trend", 1.0)
        elif trend_state == "ranging":
            return TREND_MULTIPLIERS.get("ranging", 0.6)
        else:
            return TREND_MULTIPLIERS.get("weak_trend", 0.8)


def determine_trend_from_15m(df_15m: pd.DataFrame) -> str:
    """
    Fallback: Determine trend from 15m data when 1H not available.
    Uses same logic but on 15m timeframe.

    Args:
        df_15m: 15-minute OHLCV DataFrame

    Returns:
        "uptrend", "downtrend", or "ranging"
    """
    if len(df_15m) < TREND_EMA_SLOW:
        return "ranging"

    close = df_15m["close"]
    ema_fast = ema(close, TREND_EMA_FAST).iloc[-1]
    ema_slow = ema(close, TREND_EMA_SLOW).iloc[-1]

    diff_pct = (ema_fast - ema_slow) / ema_slow

    if abs(diff_pct) < RANGING_ZONE_PCT:
        return "ranging"
    elif diff_pct > TREND_THRESHOLD_PCT:
        return "uptrend"
    elif diff_pct < -TREND_THRESHOLD_PCT:
        return "downtrend"
    else:
        return "ranging"
