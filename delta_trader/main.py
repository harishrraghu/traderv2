"""
Entry point for live trading.
"""

import asyncio
import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.bot import TradingBot


def main():
    """
    Main entry point for the trading bot.
    """
    print("\n🤖 Delta Trader - Crypto Trading Bot")
    print("Starting in live mode...\n")

    bot = TradingBot()

    try:
        asyncio.run(bot.start())
    except KeyboardInterrupt:
        print("\n\nBot stopped by user.")
    except Exception as e:
        print(f"\n\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
