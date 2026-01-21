"""
Entry point for backtesting.
"""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from exchange.client import DeltaExchangeClient
from exchange.data_fetcher import DataFetcher
from backtest.engine import BacktestEngine
from backtest.data_loader import BacktestDataLoader
from backtest.reporter import BacktestReporter
from config.coins import TRADING_COINS
from config.settings import BACKTEST_START_DATE, BACKTEST_END_DATE


def main():
    """
    Main entry point for backtesting.
    """
    print("\n" + "="*60)
    print("📊 DELTA TRADER - BACKTEST MODE")
    print("="*60)

    # Initialize (no auth needed for historical data if using cached files)
    client = DeltaExchangeClient("", "", testnet=True)
    data_fetcher = DataFetcher(client)

    # Load data
    data_loader = BacktestDataLoader(data_fetcher)
    data = data_loader.load_data(
        TRADING_COINS,
        "15m",
        BACKTEST_START_DATE,
        BACKTEST_END_DATE
    )

    # Validate data
    if not data_loader.validate_data(data):
        print("❌ Data validation failed")
        return

    # Run backtest
    print("\n" + "="*60)
    print("Running backtest...")
    print("="*60)

    engine = BacktestEngine()
    results = engine.run(data, BACKTEST_START_DATE, BACKTEST_END_DATE)

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

    print("\n✅ Backtest complete!\n")


if __name__ == "__main__":
    main()
