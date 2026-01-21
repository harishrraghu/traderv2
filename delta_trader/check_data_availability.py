"""
Check what historical data is actually available from Delta Exchange.
"""

import sys
sys.path.insert(0, '.')

from exchange.client import DeltaExchangeClient
from config.settings import DELTA_API_KEY, DELTA_API_SECRET, USE_TESTNET
from datetime import datetime, timedelta
import time

def check_available_data():
    """Check what data is available for each symbol."""

    client = DeltaExchangeClient(DELTA_API_KEY, DELTA_API_SECRET, USE_TESTNET)

    print("\n" + "="*60)
    print("🔍 CHECKING AVAILABLE HISTORICAL DATA")
    print("="*60)
    print(f"Mode: {'TESTNET' if USE_TESTNET else 'PRODUCTION'}")
    print("="*60 + "\n")

    # First, let's see what products are available
    print("📋 Fetching available products...\n")
    try:
        products = client.get_products()

        if products:
            print(f"✅ Found {len(products)} products\n")
            print("Available perpetual contracts:")
            print("-" * 60)

            perp_count = 0
            for product in products[:50]:  # Show first 50
                symbol = product.get('symbol', 'N/A')
                contract_type = product.get('contract_type', 'N/A')

                if 'perpetual' in contract_type.lower():
                    perp_count += 1
                    print(f"  {symbol} ({contract_type})")

                    if perp_count >= 20:  # Just show first 20 perpetuals
                        print(f"  ... and more")
                        break

            print(f"\n📊 Total perpetual contracts found: {perp_count}+")
        else:
            print("❌ No products found")

    except Exception as e:
        print(f"❌ Error fetching products: {e}")

    # Try different time ranges to see what's available
    symbols_to_test = ["BTCUSDT", "BTCUSD", "ETHUSD", "ETHUSDT"]

    print("\n" + "="*60)
    print("📅 Testing data availability for different time ranges")
    print("="*60 + "\n")

    for symbol in symbols_to_test:
        print(f"\n🔍 Testing {symbol}:")
        print("-" * 40)

        # Test different time ranges
        time_ranges = [
            ("Last 7 days", 7),
            ("Last 30 days", 30),
            ("Last 90 days", 90),
            ("Last 365 days", 365),
        ]

        for range_name, days in time_ranges:
            try:
                end_time = int(time.time())
                start_time = end_time - (days * 24 * 60 * 60)

                candles = client.get_candles(symbol, "15m", start_time, end_time)

                if candles:
                    print(f"  ✅ {range_name}: {len(candles)} candles")
                else:
                    print(f"  ❌ {range_name}: No data")

            except Exception as e:
                print(f"  ❌ {range_name}: Error - {str(e)[:50]}")

            time.sleep(0.5)  # Rate limiting

    # Check current ticker to verify symbols work
    print("\n" + "="*60)
    print("💹 Checking current prices (to verify symbols)")
    print("="*60 + "\n")

    for symbol in symbols_to_test:
        try:
            ticker = client.get_ticker(symbol)

            if ticker:
                price = ticker.get('close') or ticker.get('mark_price') or ticker.get('last_price')
                print(f"  ✅ {symbol}: ${price}")
            else:
                print(f"  ❌ {symbol}: No ticker data")

        except Exception as e:
            print(f"  ❌ {symbol}: {str(e)[:60]}")

        time.sleep(0.3)

    print("\n" + "="*60)
    print("✅ Data availability check complete")
    print("="*60 + "\n")

if __name__ == "__main__":
    check_available_data()
