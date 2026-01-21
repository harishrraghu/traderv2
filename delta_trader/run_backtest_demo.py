"""
Demo backtest using pre-generated sample data.
"""

import pandas as pd
import sys
import os

from backtest.engine import BacktestEngine
from backtest.reporter import BacktestReporter
from config.coins import TRADING_COINS

def load_sample_data():
    """Load pre-generated sample data from CSV files."""
    data = {}

    print("\n" + "="*60)
    print("📊 DELTA TRADER - BACKTEST DEMO")
    print("="*60)
    print("\n📥 Loading sample historical data...\n")

    for symbol in TRADING_COINS:
        filepath = f'data/historical/{symbol}_15m.csv'

        if os.path.exists(filepath):
            df = pd.read_csv(filepath, parse_dates=['timestamp'], index_col='timestamp')
            data[symbol] = df
            print(f"✅ {symbol}: {len(df)} candles loaded")
        else:
            print(f"❌ {symbol}: No data file found")

    return data

def main():
    # Load data
    data = load_sample_data()

    if not data:
        print("\n❌ No data available. Run generate_demo_data.py first.")
        return

    # Run backtest
    print("\n" + "="*60)
    print("🚀 Running backtest simulation...")
    print("="*60)

    engine = BacktestEngine()
    results = engine.run(data, "2025-01-01", "2025-01-21")

    # Generate report
    reporter = BacktestReporter(results)
    reporter.print_summary()

    # Show insights
    insights = reporter.get_insights()
    if insights:
        print("\n💡 Insights:")
        for insight in insights:
            print(f"  {insight}")

    # Save report
    reporter.save_to_file()

    print("\n" + "="*60)
    print("✅ BACKTEST COMPLETE!")
    print("="*60)

    # Show some sample trades
    if results.get("trades"):
        print(f"\n📋 Sample Trades (showing first 5):")
        print("="*60)
        for trade in results["trades"][:5]:
            symbol = trade.symbol
            pnl = trade.pnl_pct
            emoji = "✅" if pnl > 0 else "❌"
            print(f"{emoji} {symbol} {trade.setup_type} {trade.direction}")
            print(f"   Entry: ${trade.entry_price:.2f} @ {trade.entry_time}")
            print(f"   Exit:  ${trade.exit_price:.2f} @ {trade.exit_time}")
            print(f"   P&L: {pnl:+.2%} | Reason: {trade.exit_reason}")
            print()

    print("📁 Full report saved to data/reports/")
    print("\n")

if __name__ == "__main__":
    main()
