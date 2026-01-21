"""
Signal generation and confirmation.
"""

from typing import Dict, Optional
import pandas as pd


class SignalGenerator:
    """
    Generates and confirms trading signals.
    Can add multi-timeframe confirmation here.
    """

    def __init__(self, data_fetcher):
        self.data_fetcher = data_fetcher

    def confirm_setup(self, setup: Dict) -> bool:
        """
        Confirm setup with additional checks.
        Returns True if setup is confirmed.
        """
        # For now, simple confirmation
        # Can add multi-timeframe checks, volume confirmation, etc.

        try:
            symbol = setup["symbol"]

            # Check if price is still valid
            current_price = self.data_fetcher.get_current_price(symbol)

            if current_price == 0:
                return False

            # Price shouldn't have moved too much from entry
            price_diff = abs(current_price - setup["entry"]) / setup["entry"]

            if price_diff > 0.005:  # More than 0.5% difference
                return False

            return True

        except Exception as e:
            print(f"Error confirming setup: {e}")
            return False

    def get_exit_signals(self, position: Dict, current_data: pd.DataFrame) -> Optional[str]:
        """
        Check for exit signals.
        Returns: "TP", "STOP", "SIGNAL_EXIT", or None
        """
        # This can be extended with dynamic exit logic
        # For now, we rely on TP/SL in the bot
        return None
