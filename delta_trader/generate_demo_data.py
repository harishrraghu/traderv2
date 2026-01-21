"""
Demo script to generate sample historical data and run backtest.
This simulates what would happen with real Delta Exchange data.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os

def generate_sample_ohlcv(symbol: str, start_date: str, end_date: str, base_price: float):
    """Generate realistic-looking OHLCV data for demonstration."""

    start = pd.to_datetime(start_date)
    end = pd.to_datetime(end_date)

    # Create 15-minute intervals
    timestamps = pd.date_range(start, end, freq='15min')

    data = []
    price = base_price

    for ts in timestamps:
        # Simulate price movement with some randomness
        change = np.random.normal(0, 0.003)  # 0.3% std deviation
        price = price * (1 + change)

        # Generate OHLCV
        high = price * (1 + abs(np.random.normal(0, 0.002)))
        low = price * (1 - abs(np.random.normal(0, 0.002)))
        open_price = price * (1 + np.random.normal(0, 0.001))
        volume = np.random.uniform(1000000, 5000000)

        data.append({
            'timestamp': ts,
            'open': open_price,
            'high': max(high, open_price, price),
            'low': min(low, open_price, price),
            'close': price,
            'volume': volume
        })

    df = pd.DataFrame(data)
    df.set_index('timestamp', inplace=True)

    return df

def save_sample_data():
    """Generate and save sample data for all symbols."""

    # Create directory
    os.makedirs('data/historical', exist_ok=True)

    symbols_config = {
        'BTCUSDT': 45000,
        'ETHUSDT': 2500,
        'SOLUSDT': 100,
        'BNBUSDT': 300,
        'XRPUSDT': 0.50
    }

    start_date = "2025-01-01"
    end_date = "2025-01-21"  # Recent data

    print(f"\n🔧 Generating sample historical data...")
    print(f"Period: {start_date} to {end_date}\n")

    for symbol, base_price in symbols_config.items():
        print(f"Generating {symbol}... ", end='')
        df = generate_sample_ohlcv(symbol, start_date, end_date, base_price)

        # Save to CSV
        filepath = f'data/historical/{symbol}_15m.csv'
        df.to_csv(filepath)

        print(f"✅ {len(df)} candles saved")

    print(f"\n✅ Sample data generated successfully!\n")

if __name__ == "__main__":
    save_sample_data()
