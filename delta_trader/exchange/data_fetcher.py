"""
Fetch and cache market data.
Uses Delta Exchange API for real data.
"""

import pandas as pd
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import json
import os
import time


class DataFetcher:
    """
    Fetches OHLCV and market data from Delta Exchange.
    Implements caching to avoid excessive API calls.
    """

    def __init__(self, client):
        self.client = client
        self.cache_dir = "data/historical"
        self.cache = {}  # In-memory cache: {symbol_timeframe: (data, timestamp)}
        self.cache_ttl = 60  # Cache TTL in seconds

        # Create cache directory
        os.makedirs(self.cache_dir, exist_ok=True)

    def get_ohlcv(
        self,
        symbol: str,
        timeframe: str = "15m",
        limit: int = 100,
        use_cache: bool = True
    ) -> pd.DataFrame:
        """
        Get OHLCV data as DataFrame.

        Returns DataFrame with columns:
        - timestamp (index)
        - open
        - high
        - low
        - close
        - volume
        """
        cache_key = f"{symbol}_{timeframe}"

        # Check cache
        if use_cache and cache_key in self.cache:
            data, cached_at = self.cache[cache_key]
            if time.time() - cached_at < self.cache_ttl:
                return data.tail(limit).copy()

        try:
            # Calculate time range
            end_time = int(time.time())

            # Convert timeframe to seconds
            timeframe_seconds = self._timeframe_to_seconds(timeframe)
            start_time = end_time - (limit * timeframe_seconds)

            # Fetch from API
            candles = self.client.get_candles(symbol, timeframe, start_time, end_time)

            if not candles:
                return None

            # Convert to DataFrame
            df = pd.DataFrame(candles)

            # Delta API returns: [timestamp, open, high, low, close, volume]
            # Handle different possible formats
            if isinstance(candles[0], list):
                df = pd.DataFrame(candles, columns=["timestamp", "open", "high", "low", "close", "volume"])
            else:
                # If dict format, rename columns as needed
                df = pd.DataFrame(candles)
                if "time" in df.columns:
                    df.rename(columns={"time": "timestamp"}, inplace=True)

            # Convert timestamp to datetime
            df["timestamp"] = pd.to_datetime(df["timestamp"], unit="s")
            df.set_index("timestamp", inplace=True)

            # Convert price columns to float
            for col in ["open", "high", "low", "close", "volume"]:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors="coerce")

            # Sort by timestamp
            df.sort_index(inplace=True)

            # Cache it
            self.cache[cache_key] = (df, time.time())

            return df.tail(limit).copy()

        except Exception as e:
            print(f"Error fetching OHLCV for {symbol}: {e}")
            return None

    def get_current_price(self, symbol: str) -> float:
        """Get current price for symbol."""
        try:
            ticker = self.client.get_ticker(symbol)
            # Delta API returns last price in 'close' or 'last_price' field
            price = ticker.get("close") or ticker.get("last_price") or ticker.get("mark_price")
            return float(price) if price else 0.0
        except Exception as e:
            print(f"Error fetching current price for {symbol}: {e}")
            return 0.0

    def get_btc_data(self, timeframe: str = "15m", limit: int = 100) -> pd.DataFrame:
        """Get BTC data (used for regime detection)."""
        return self.get_ohlcv("BTCUSDT", timeframe, limit)

    def get_funding_rate(self, symbol: str) -> float:
        """Get current funding rate."""
        try:
            funding_data = self.client.get_funding_rate(symbol)
            return float(funding_data.get("funding_rate", 0))
        except Exception as e:
            print(f"Error fetching funding rate for {symbol}: {e}")
            return 0.0

    def get_24h_volume(self, symbol: str) -> float:
        """Get 24h trading volume in USD."""
        try:
            ticker = self.client.get_ticker(symbol)
            volume = ticker.get("volume", 0) or ticker.get("turnover_24h", 0)
            return float(volume) if volume else 0.0
        except Exception as e:
            print(f"Error fetching 24h volume for {symbol}: {e}")
            return 0.0

    def get_multiple_timeframes(
        self,
        symbol: str,
        timeframes: List[str] = ["15m", "1h", "4h"]
    ) -> Dict[str, pd.DataFrame]:
        """Get data for multiple timeframes."""
        result = {}
        for tf in timeframes:
            df = self.get_ohlcv(symbol, tf)
            if df is not None:
                result[tf] = df
        return result

    # === Historical Data for Backtesting ===

    def fetch_historical_data(
        self,
        symbol: str,
        timeframe: str,
        start_date: str,
        end_date: str,
        save_to_file: bool = True
    ) -> pd.DataFrame:
        """
        Fetch historical data for backtesting.
        Handles pagination if needed.
        Saves to CSV for reuse.
        """
        # Check if cached file exists
        filepath = f"{self.cache_dir}/{symbol}_{timeframe}.csv"
        if os.path.exists(filepath):
            print(f"Loading cached data from {filepath}")
            return self.load_historical_data(symbol, timeframe)

        try:
            start_dt = pd.to_datetime(start_date)
            end_dt = pd.to_datetime(end_date)

            start_ts = int(start_dt.timestamp())
            end_ts = int(end_dt.timestamp())

            all_candles = []
            current_start = start_ts
            timeframe_seconds = self._timeframe_to_seconds(timeframe)
            batch_size = 1000  # Fetch in batches

            print(f"Fetching historical data for {symbol} ({timeframe})...")

            while current_start < end_ts:
                current_end = min(current_start + (batch_size * timeframe_seconds), end_ts)

                candles = self.client.get_candles(symbol, timeframe, current_start, current_end)

                if candles:
                    all_candles.extend(candles)
                    print(f"  Fetched {len(candles)} candles")

                current_start = current_end

                # Rate limiting
                time.sleep(0.5)

            if not all_candles:
                print(f"No data available for {symbol}")
                return None

            # Convert to DataFrame
            if isinstance(all_candles[0], list):
                df = pd.DataFrame(all_candles, columns=["timestamp", "open", "high", "low", "close", "volume"])
            else:
                df = pd.DataFrame(all_candles)
                if "time" in df.columns:
                    df.rename(columns={"time": "timestamp"}, inplace=True)

            df["timestamp"] = pd.to_datetime(df["timestamp"], unit="s")
            df.set_index("timestamp", inplace=True)

            for col in ["open", "high", "low", "close", "volume"]:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors="coerce")

            df.sort_index(inplace=True)
            df = df[~df.index.duplicated(keep='first')]

            # Save to file
            if save_to_file:
                df.to_csv(filepath)
                print(f"Saved to {filepath}")

            return df

        except Exception as e:
            print(f"Error fetching historical data: {e}")
            return None

    def load_historical_data(self, symbol: str, timeframe: str) -> Optional[pd.DataFrame]:
        """Load cached historical data from file."""
        filepath = f"{self.cache_dir}/{symbol}_{timeframe}.csv"
        if os.path.exists(filepath):
            df = pd.read_csv(filepath, parse_dates=['timestamp'], index_col='timestamp')
            return df
        return None

    def _timeframe_to_seconds(self, timeframe: str) -> int:
        """Convert timeframe string to seconds."""
        mapping = {
            "1m": 60,
            "5m": 300,
            "15m": 900,
            "30m": 1800,
            "1h": 3600,
            "2h": 7200,
            "4h": 14400,
            "1d": 86400,
            "1w": 604800
        }
        return mapping.get(timeframe, 900)  # Default to 15m
