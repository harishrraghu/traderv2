"""
Analyze the historical data that was actually downloaded.
"""

import pandas as pd
import os
from datetime import datetime

def analyze_data():
    """Check what data we actually have."""

    print("\n" + "="*60)
    print("📊 ANALYZING DOWNLOADED HISTORICAL DATA")
    print("="*60 + "\n")

    symbols = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "XRPUSDT", "BNBUSDT"]

    for symbol in symbols:
        filepath = f"data/historical/{symbol}_15m.csv"

        if not os.path.exists(filepath):
            print(f"❌ {symbol}: No file found")
            continue

        try:
            df = pd.read_csv(filepath, parse_dates=['timestamp'])

            if len(df) == 0:
                print(f"❌ {symbol}: File is empty")
                continue

            # Get date range
            first_date = df['timestamp'].min()
            last_date = df['timestamp'].max()
            total_candles = len(df)

            # Calculate expected vs actual
            duration_hours = (last_date - first_date).total_seconds() / 3600
            expected_candles = int(duration_hours * 4)  # 4 candles per hour for 15m

            # Show statistics
            print(f"\n📈 {symbol}:")
            print(f"  {'─'*50}")
            print(f"  📅 First candle: {first_date}")
            print(f"  📅 Last candle:  {last_date}")
            print(f"  ⏱️  Duration:     {duration_hours:.1f} hours ({duration_hours/24:.1f} days)")
            print(f"  📊 Candles:      {total_candles}")
            print(f"  📊 Expected:     {expected_candles} (if complete)")
            print(f"  📊 Coverage:     {(total_candles/expected_candles)*100:.1f}% complete")

            # Check for gaps
            df_sorted = df.sort_values('timestamp')
            time_diffs = df_sorted['timestamp'].diff()
            gaps = time_diffs[time_diffs > pd.Timedelta(minutes=20)]  # More than 20 min = gap

            if len(gaps) > 0:
                print(f"  ⚠️  Data gaps:    {len(gaps)} gaps found")
            else:
                print(f"  ✅ Data gaps:    No gaps (continuous)")

            # Show price range
            print(f"  💵 Price range:  ${df['close'].min():.2f} - ${df['close'].max():.2f}")

        except Exception as e:
            print(f"❌ {symbol}: Error analyzing - {e}")

    print("\n" + "="*60)
    print("📋 SUMMARY")
    print("="*60)

    print("""
The data you have is MUCH LESS than a full year because:

1. ⏱️  LIMITED TIME RANGE
   You only got about 8-20 days of data, not a full year

2. 🔍 LIKELY REASONS:

   a) Delta Exchange API Pagination Issue
      - The API might have stopped returning data after first batch
      - Max candles per request might be limited

   b) Testnet Limitations
      - Testnet might only have recent data (last few days/weeks)
      - Not full historical archives like production

   c) Symbol Availability
      - Some symbols might not be available for the full period
      - BNBUSDT returned no data at all

   d) API Rate Limiting
      - Requests might have been throttled/blocked

3. 💡 SOLUTIONS:

   Option A: Use Production API (not testnet)
      - Change USE_TESTNET = False in config/settings.py
      - Production usually has more historical data

   Option B: Adjust Date Range
      - Change dates to recent period (last 30 days)
      - In config/settings.py:
        BACKTEST_START_DATE = "2025-01-01"
        BACKTEST_END_DATE = "2025-01-21"

   Option C: Verify Symbol Names
      - Check Delta Exchange docs for correct symbol format
      - Might be "BTCUSD" not "BTCUSDT"
      - Might need different contract identifiers

   Option D: Fix Pagination Logic
      - The data fetcher might have a bug
      - API might need different parameters
""")

    print("="*60 + "\n")

if __name__ == "__main__":
    analyze_data()
