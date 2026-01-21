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

    def detect_all_setups(self, df: pd.DataFrame, symbol: str) -> List[Dict]:
        """
        Run all setup detectors on the data.
        Returns list of valid setups.
        """
        setups = []

        # Run each detector
        detectors = [
            self.detect_ema_pullback,
            self.detect_breakout,
            self.detect_rsi_extreme,
            self.detect_range_bounce,
            self.detect_momentum,
        ]

        for detector in detectors:
            try:
                setup = detector(df)
                if setup and setup["score"] >= self.min_score:
                    setup["symbol"] = symbol
                    setups.append(setup)
            except Exception as e:
                # Silent fail for individual detectors
                pass

        return setups

    def detect_ema_pullback(self, df: pd.DataFrame) -> Optional[Dict]:
        """
        EMA Pullback Setup:
        - Price pulls back to 21 EMA in a trend
        - 21 EMA > 55 EMA for uptrend (or < for downtrend)
        """
        if len(df) < 55:
            return None

        close = df["close"]
        current_price = close.iloc[-1]

        ema_21 = ema(close, 21).iloc[-1]
        ema_55 = ema(close, 55).iloc[-1]

        distance_to_ema = (current_price - ema_21) / ema_21

        # Uptrend pullback
        if ema_21 > ema_55:
            if -0.01 < distance_to_ema < 0.005:
                return {
                    "type": "EMA_PULLBACK_LONG",
                    "direction": "LONG",
                    "score": 0.6,
                    "entry": current_price,
                    "stop": ema_55 * 0.995,
                    "target": current_price * 1.015,
                    "reason": f"Price near 21 EMA in uptrend, distance: {distance_to_ema:.2%}"
                }

        # Downtrend pullback
        if ema_21 < ema_55:
            if -0.005 < distance_to_ema < 0.01:
                return {
                    "type": "EMA_PULLBACK_SHORT",
                    "direction": "SHORT",
                    "score": 0.6,
                    "entry": current_price,
                    "stop": ema_55 * 1.005,
                    "target": current_price * 0.985,
                    "reason": f"Price near 21 EMA in downtrend, distance: {distance_to_ema:.2%}"
                }

        return None

    def detect_breakout(self, df: pd.DataFrame) -> Optional[Dict]:
        """
        Breakout Setup:
        - Price breaks above 20-period high (long)
        - Price breaks below 20-period low (short)
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

        if current_price > high_20:
            return {
                "type": "BREAKOUT_LONG",
                "direction": "LONG",
                "score": 0.55,
                "entry": current_price,
                "stop": high_20 * 0.99,
                "target": current_price * 1.02,
                "reason": f"Broke above 20-period high at {high_20:.4f}"
            }

        if current_price < low_20:
            return {
                "type": "BREAKOUT_SHORT",
                "direction": "SHORT",
                "score": 0.55,
                "entry": current_price,
                "stop": low_20 * 1.01,
                "target": current_price * 0.98,
                "reason": f"Broke below 20-period low at {low_20:.4f}"
            }

        return None

    def detect_rsi_extreme(self, df: pd.DataFrame) -> Optional[Dict]:
        """
        RSI Extreme Setup:
        - RSI < 30 and price holding above recent low (oversold bounce)
        - RSI > 70 and price holding below recent high (overbought fade)
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

        if rsi_value < 30 and current_price > recent_low:
            return {
                "type": "RSI_OVERSOLD_LONG",
                "direction": "LONG",
                "score": 0.5,
                "entry": current_price,
                "stop": recent_low * 0.995,
                "target": current_price * 1.012,
                "reason": f"RSI oversold at {rsi_value:.1f}, holding above {recent_low:.4f}"
            }

        if rsi_value > 70 and current_price < recent_high:
            return {
                "type": "RSI_OVERBOUGHT_SHORT",
                "direction": "SHORT",
                "score": 0.5,
                "entry": current_price,
                "stop": recent_high * 1.005,
                "target": current_price * 0.988,
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
