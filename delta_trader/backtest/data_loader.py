"""
Load and prepare data for backtesting.
"""

import pandas as pd
from typing import Dict, List
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class BacktestDataLoader:
    """
    Loads historical data for backtesting.
    """

    def __init__(self, data_fetcher):
        self.data_fetcher = data_fetcher

    def load_data(
        self,
        symbols: List[str],
        timeframe: str,
        start_date: str,
        end_date: str
    ) -> Dict[str, pd.DataFrame]:
        """
        Load historical data for multiple symbols.

        Returns:
            Dict of symbol -> DataFrame
        """
        data = {}

        print(f"\nLoading data for backtesting...")
        print(f"Symbols: {', '.join(symbols)}")
        print(f"Timeframe: {timeframe}")
        print(f"Period: {start_date} to {end_date}\n")

        for symbol in symbols:
            print(f"Loading {symbol}...")

            df = self.data_fetcher.fetch_historical_data(
                symbol,
                timeframe,
                start_date,
                end_date,
                save_to_file=True
            )

            if df is not None and len(df) > 0:
                data[symbol] = df
                print(f"  ✅ Loaded {len(df)} candles\n")
            else:
                print(f"  ❌ No data available\n")

        return data

    def validate_data(self, data: Dict[str, pd.DataFrame]) -> bool:
        """Validate loaded data."""
        if not data:
            print("❌ No data loaded")
            return False

        for symbol, df in data.items():
            if len(df) < 100:
                print(f"⚠️ Warning: {symbol} has only {len(df)} candles")

            # Check for missing values
            if df.isnull().any().any():
                print(f"⚠️ Warning: {symbol} has missing values")

        return True
