"""
Minimal safety checks.
Only blocks obvious dangers, not suboptimal conditions.
"""

import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.settings import BTC_FLASH_MOVE_PCT, EXTREME_FUNDING_RATE


class SafetyGate:
    """
    Simple safety gate. Only blocks extreme conditions.
    """

    def __init__(self, data_fetcher):
        self.data_fetcher = data_fetcher

    def check(self) -> dict:
        """
        Returns:
        {
            "allowed": bool,
            "reason": str or None
        }
        """
        try:
            # Check BTC flash move
            btc_df = self.data_fetcher.get_ohlcv("BTCUSDT", "15m", limit=2)
            if btc_df is not None and len(btc_df) >= 2:
                btc_change = (btc_df["close"].iloc[-1] - btc_df["close"].iloc[-2]) / btc_df["close"].iloc[-2]

                if abs(btc_change) > BTC_FLASH_MOVE_PCT:
                    return {
                        "allowed": False,
                        "reason": f"BTC flash move: {btc_change:.2%} in 15 min"
                    }

            # Check funding rate (if available)
            try:
                funding = self.data_fetcher.get_funding_rate("BTCUSDT")
                if funding and abs(funding) > EXTREME_FUNDING_RATE:
                    return {
                        "allowed": False,
                        "reason": f"Extreme funding rate: {funding:.4%}"
                    }
            except:
                pass  # Funding check is optional

            return {"allowed": True, "reason": None}

        except Exception as e:
            # If we can't check, allow but log
            print(f"Safety gate error: {e}")
            return {"allowed": True, "reason": None}
