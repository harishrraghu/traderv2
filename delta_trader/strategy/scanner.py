"""
Scans all coins for setups.
"""

from typing import List, Dict
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from strategy.setups import SetupDetector
from config.coins import TRADING_COINS


class Scanner:
    """
    Scans trading universe for setups.
    """

    def __init__(self, data_fetcher):
        self.data_fetcher = data_fetcher
        self.setup_detector = SetupDetector()

    def scan_all(self, timeframe: str = "15m") -> List[Dict]:
        """
        Scan all coins and return sorted setups.
        """
        all_setups = []

        for symbol in TRADING_COINS:
            try:
                df = self.data_fetcher.get_ohlcv(symbol, timeframe, limit=100)
                if df is not None and len(df) >= 55:  # Need enough data for indicators
                    setups = self.setup_detector.detect_all_setups(df, symbol)
                    all_setups.extend(setups)
            except Exception as e:
                print(f"Error scanning {symbol}: {e}")

        # Sort by score descending
        all_setups.sort(key=lambda x: x["score"], reverse=True)

        return all_setups

    def get_best_setup(self, timeframe: str = "15m") -> Dict:
        """Get single best setup."""
        setups = self.scan_all(timeframe)
        return setups[0] if setups else None

    def scan_symbol(self, symbol: str, timeframe: str = "15m") -> List[Dict]:
        """Scan a single symbol for setups."""
        try:
            df = self.data_fetcher.get_ohlcv(symbol, timeframe, limit=100)
            if df is not None and len(df) >= 55:
                return self.setup_detector.detect_all_setups(df, symbol)
        except Exception as e:
            print(f"Error scanning {symbol}: {e}")

        return []
