"""
Core setup detection logic.
Each setup type is a function that returns a dict or None.
"""

import pandas as pd
from typing import Optional, Dict, List
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.indicators import ema, rsi, atr, rolling_high, rolling_low, bollinger_bands
from strategy.filters import MarketFilters, determine_trend_from_15m
from config.settings import (
    ENABLED_SETUPS, SETUP_BASE_SCORES, USE_ATR_BASED_EXITS, ATR_PERIOD,
    STOP_LOSS_ATR_MULTIPLE, TAKE_PROFIT_1_ATR_MULTIPLE,
    REQUIRE_ENTRY_CONFIRMATION, EMA_PULLBACK_CONFIG, FEATURES
)


class SetupDetector:
    """
    Detects trade setups on price data.

    Each setup returns:
    {
        "type": str,          # Setup name
        "direction": str,     # "LONG" or "SHORT"
        "score": float,       # 0.0 to 1.0
        "entry": float,       # Entry price
        "stop": float,        # Stop loss price
        "target": float,      # Take profit price
        "reason": str,        # Why this setup triggered
    }
    """

    def __init__(self):
        self.min_score = 0.4
        self.market_filters = MarketFilters()

    def detect_all_setups(self, df: pd.DataFrame, symbol: str, df_1h: pd.DataFrame = None) -> List[Dict]:
        """
        Run all setup detectors on the data.
        Returns list of valid setups.

        Args:
            df: 15-minute OHLCV data
            symbol: Trading symbol
            df_1h: Optional 1-hour data for trend filter (if None, uses 15m)
        """
        setups = []

        # Determine trend
        if df_1h is not None and len(df_1h) >= 55:
            trend_state = self.market_filters.get_trend_state(df_1h)
        else:
            # Fallback to 15m data
            trend_state = determine_trend_from_15m(df)

        # Check volatility
        if FEATURES.get("volatility_filter", False):
            vol_passed, vol_reason = self.market_filters.check_volatility(df)
            if not vol_passed:
                # Skip this symbol - no volatility
                return []

        # Run each detector
        detectors = [
            ("EMA_PULLBACK", self.detect_ema_pullback),
            ("BREAKOUT", self.detect_breakout),
            ("RSI_EXTREME", self.detect_rsi_extreme),
            ("RANGE_BOUNCE", self.detect_range_bounce),
            ("MOMENTUM", self.detect_momentum),
        ]

        for detector_name, detector in detectors:
            try:
                setup = detector(df)
                if setup and setup["score"] >= self.min_score:
                    # Check if this setup type is enabled
                    setup_type = setup["type"]
                    if not ENABLED_SETUPS.get(setup_type, False):
                        continue  # Skip disabled setups

                    # Check trend filter
                    if FEATURES.get("trend_filter", False):
                        direction = setup["direction"]
                        if not self.market_filters.is_direction_allowed(direction, trend_state):
                            continue  # Wrong direction for current trend

                    setup["symbol"] = symbol
                    setup["trend_state"] = trend_state
                    setups.append(setup)
            except Exception as e:
                # Silent fail for individual detectors
                pass

        return setups

    def detect_ema_pullback(self, df: pd.DataFrame) -> Optional[Dict]:
        """
        EMA Pullback Setup (Improved):
        - Price pulls back to 21 EMA in a trend
        - 21 EMA > 55 EMA for uptrend (or < for downtrend)
        - Now with entry confirmation requirements
        """
        if len(df) < 55:
            return None

        close = df["close"]
        high = df["high"]
        low = df["low"]
        current_price = close.iloc[-1]

        ema_21 = ema(close, 21).iloc[-1]
        ema_55 = ema(close, 55).iloc[-1]

        distance_to_ema = (current_price - ema_21) / ema_21

        # Calculate ATR for stops/targets
        atr_value = atr(df["high"], df["low"], df["close"], ATR_PERIOD).iloc[-1] if USE_ATR_BASED_EXITS else None

        # Entry confirmation check (if enabled)
        if REQUIRE_ENTRY_CONFIRMATION and FEATURES.get("entry_confirmation", False):
            config = EMA_PULLBACK_CONFIG

            # Check RSI if available
            try:
                rsi_value = rsi(close, 14).iloc[-1]
            except:
                rsi_value = 50  # Default if can't calculate

        # Uptrend pullback
        if ema_21 > ema_55:
            # Tighter distance requirement
            max_dist = EMA_PULLBACK_CONFIG.get("ema_distance_max_pct", 0.005) if REQUIRE_ENTRY_CONFIRMATION else 0.01
            min_dist = -EMA_PULLBACK_CONFIG.get("ema_distance_min_pct", 0.001) if REQUIRE_ENTRY_CONFIRMATION else -0.01

            if min_dist < distance_to_ema < max_dist:
                # Additional confirmation checks
                if REQUIRE_ENTRY_CONFIRMATION and FEATURES.get("entry_confirmation", False):
                    # RSI check
                    rsi_min = EMA_PULLBACK_CONFIG.get("rsi_min", 35)
                    rsi_max = EMA_PULLBACK_CONFIG.get("rsi_max", 50)
                    if not (rsi_min < rsi_value < rsi_max):
                        return None  # RSI out of range

                # Calculate stop and target
                if USE_ATR_BASED_EXITS and atr_value:
                    stop = current_price - (STOP_LOSS_ATR_MULTIPLE * atr_value)
                    target = current_price + (TAKE_PROFIT_1_ATR_MULTIPLE * atr_value)
                else:
                    stop = ema_55 * 0.995
                    target = current_price * 1.015

                score = SETUP_BASE_SCORES.get("EMA_PULLBACK_LONG", 0.65)

                return {
                    "type": "EMA_PULLBACK_LONG",
                    "direction": "LONG",
                    "score": score,
                    "entry": current_price,
                    "stop": stop,
                    "target": target,
                    "reason": f"Price near 21 EMA in uptrend, distance: {distance_to_ema:.2%}"
                }

        # Downtrend pullback
        if ema_21 < ema_55:
            # Tighter distance requirement
            max_dist = EMA_PULLBACK_CONFIG.get("ema_distance_max_pct", 0.005) if REQUIRE_ENTRY_CONFIRMATION else 0.01
            min_dist = -EMA_PULLBACK_CONFIG.get("ema_distance_min_pct", 0.001) if REQUIRE_ENTRY_CONFIRMATION else -0.005

            if min_dist < distance_to_ema < max_dist:
                # Additional confirmation checks
                if REQUIRE_ENTRY_CONFIRMATION and FEATURES.get("entry_confirmation", False):
                    # RSI check (inverted for shorts)
                    rsi_min = 50
                    rsi_max = 65
                    if not (rsi_min < rsi_value < rsi_max):
                        return None  # RSI out of range

                # Calculate stop and target
                if USE_ATR_BASED_EXITS and atr_value:
                    stop = current_price + (STOP_LOSS_ATR_MULTIPLE * atr_value)
                    target = current_price - (TAKE_PROFIT_1_ATR_MULTIPLE * atr_value)
                else:
                    stop = ema_55 * 1.005
                    target = current_price * 0.985

                score = SETUP_BASE_SCORES.get("EMA_PULLBACK_SHORT", 0.50)

                return {
                    "type": "EMA_PULLBACK_SHORT",
                    "direction": "SHORT",
                    "score": score,
                    "entry": current_price,
                    "stop": stop,
                    "target": target,
                    "reason": f"Price near 21 EMA in downtrend, distance: {distance_to_ema:.2%}"
                }

        return None

    def detect_breakout(self, df: pd.DataFrame) -> Optional[Dict]:
        """
        Breakout Setup (Improved):
        - Price breaks above 20-period high (long)
        - Price breaks below 20-period low (short)
        - Now with ATR-based stops
        """
        if len(df) < 21:
            return None

        close = df["close"]
        high = df["high"]
        low = df["low"]
        current_price = close.iloc[-1]

        # Use second-to-last bar for reference (avoid including current bar)
        high_20 = rolling_high(high, 20).iloc[-2]
        low_20 = rolling_low(low, 20).iloc[-2]

        # Calculate ATR for stops/targets
        atr_value = atr(df["high"], df["low"], df["close"], ATR_PERIOD).iloc[-1] if USE_ATR_BASED_EXITS else None

        if current_price > high_20:
            # Calculate stop and target
            if USE_ATR_BASED_EXITS and atr_value:
                stop = current_price - (STOP_LOSS_ATR_MULTIPLE * atr_value)
                target = current_price + (TAKE_PROFIT_1_ATR_MULTIPLE * atr_value)
            else:
                stop = high_20 * 0.99
                target = current_price * 1.02

            score = SETUP_BASE_SCORES.get("BREAKOUT_LONG", 0.45)

            return {
                "type": "BREAKOUT_LONG",
                "direction": "LONG",
                "score": score,
                "entry": current_price,
                "stop": stop,
                "target": target,
                "reason": f"Broke above 20-period high at {high_20:.4f}"
            }

        if current_price < low_20:
            # Calculate stop and target
            if USE_ATR_BASED_EXITS and atr_value:
                stop = current_price + (STOP_LOSS_ATR_MULTIPLE * atr_value)
                target = current_price - (TAKE_PROFIT_1_ATR_MULTIPLE * atr_value)
            else:
                stop = low_20 * 1.01
                target = current_price * 0.98

            score = SETUP_BASE_SCORES.get("BREAKOUT_SHORT", 0.55)

            return {
                "type": "BREAKOUT_SHORT",
                "direction": "SHORT",
                "score": score,
                "entry": current_price,
                "stop": stop,
                "target": target,
                "reason": f"Broke below 20-period low at {low_20:.4f}"
            }

        return None

    def detect_rsi_extreme(self, df: pd.DataFrame) -> Optional[Dict]:
        """
        RSI Extreme Setup (Improved):
        - RSI < 30 and price holding above recent low (oversold bounce)
        - RSI > 70 and price holding below recent high (overbought fade)
        - Now with ATR-based stops
        """
        if len(df) < 20:
            return None

        close = df["close"]
        low = df["low"]
        high = df["high"]
        current_price = close.iloc[-1]

        rsi_value = rsi(close, 14).iloc[-1]
        recent_low = rolling_low(low, 5).iloc[-1]
        recent_high = rolling_high(high, 5).iloc[-1]

        # Calculate ATR for stops/targets
        atr_value = atr(df["high"], df["low"], df["close"], ATR_PERIOD).iloc[-1] if USE_ATR_BASED_EXITS else None

        if rsi_value < 30 and current_price > recent_low:
            # Calculate stop and target
            if USE_ATR_BASED_EXITS and atr_value:
                stop = current_price - (STOP_LOSS_ATR_MULTIPLE * atr_value)
                target = current_price + (TAKE_PROFIT_1_ATR_MULTIPLE * atr_value)
            else:
                stop = recent_low * 0.995
                target = current_price * 1.012

            score = SETUP_BASE_SCORES.get("RSI_OVERSOLD_LONG", 0.55)

            return {
                "type": "RSI_OVERSOLD_LONG",
                "direction": "LONG",
                "score": score,
                "entry": current_price,
                "stop": stop,
                "target": target,
                "reason": f"RSI oversold at {rsi_value:.1f}, holding above {recent_low:.4f}"
            }

        if rsi_value > 70 and current_price < recent_high:
            # Calculate stop and target
            if USE_ATR_BASED_EXITS and atr_value:
                stop = current_price + (STOP_LOSS_ATR_MULTIPLE * atr_value)
                target = current_price - (TAKE_PROFIT_1_ATR_MULTIPLE * atr_value)
            else:
                stop = recent_high * 1.005
                target = current_price * 0.988

            score = SETUP_BASE_SCORES.get("RSI_OVERBOUGHT_SHORT", 0.50)

            return {
                "type": "RSI_OVERBOUGHT_SHORT",
                "direction": "SHORT",
                "score": score,
                "entry": current_price,
                "stop": stop,
                "target": target,
                "reason": f"RSI overbought at {rsi_value:.1f}, holding below {recent_high:.4f}"
            }

        return None

    def detect_range_bounce(self, df: pd.DataFrame) -> Optional[Dict]:
        """
        Range Bounce Setup:
        - Price near Bollinger Band lower band (potential long)
        - Price near Bollinger Band upper band (potential short)
        - Only in ranging market (tight BB width)
        """
        if len(df) < 50:
            return None

        close = df["close"]
        current_price = close.iloc[-1]

        upper, middle, lower, width = bollinger_bands(close, 20, 2)
        current_width = width.iloc[-1]
        avg_width = width.rolling(50).mean().iloc[-1]

        # Only trade if BB is relatively tight (ranging)
        if current_width > avg_width:
            return None

        lower_band = lower.iloc[-1]
        upper_band = upper.iloc[-1]

        # Near lower band
        if (current_price - lower_band) / lower_band < 0.005:
            return {
                "type": "RANGE_BOUNCE_LONG",
                "direction": "LONG",
                "score": 0.45,
                "entry": current_price,
                "stop": lower_band * 0.99,
                "target": middle.iloc[-1],
                "reason": f"Price at lower BB in tight range"
            }

        # Near upper band
        if (upper_band - current_price) / upper_band < 0.005:
            return {
                "type": "RANGE_BOUNCE_SHORT",
                "direction": "SHORT",
                "score": 0.45,
                "entry": current_price,
                "stop": upper_band * 1.01,
                "target": middle.iloc[-1],
                "reason": f"Price at upper BB in tight range"
            }

        return None

    def detect_momentum(self, df: pd.DataFrame) -> Optional[Dict]:
        """
        Momentum Continuation Setup:
        - Strong move in last 3 candles
        - Continuation expected
        """
        if len(df) < 5:
            return None

        close = df["close"]
        current_price = close.iloc[-1]

        returns_3 = (current_price - close.iloc[-4]) / close.iloc[-4]

        if returns_3 > 0.02:  # Up 2%+ in 3 candles
            return {
                "type": "MOMENTUM_LONG",
                "direction": "LONG",
                "score": 0.45,
                "entry": current_price,
                "stop": current_price * 0.985,
                "target": current_price * 1.015,
                "reason": f"Strong momentum, +{returns_3:.2%} in 3 candles"
            }

        if returns_3 < -0.02:  # Down 2%+ in 3 candles
            return {
                "type": "MOMENTUM_SHORT",
                "direction": "SHORT",
                "score": 0.45,
                "entry": current_price,
                "stop": current_price * 1.015,
                "target": current_price * 0.985,
                "reason": f"Strong momentum, {returns_3:.2%} in 3 candles"
            }

        return None
