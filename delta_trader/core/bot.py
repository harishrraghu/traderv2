"""
Main trading bot.
"""

import asyncio
from datetime import datetime
from typing import Dict, List
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from exchange.client import DeltaExchangeClient
from exchange.data_fetcher import DataFetcher
from strategy.scanner import Scanner
from risk.safety_gate import SafetyGate
from learning.trade_logger import TradeLogger
from learning.analyzer import PerformanceAnalyzer
from core.position_manager import PositionManager
from core.trade_manager import TradeManager

from config.settings import (
    DELTA_API_KEY, DELTA_API_SECRET, USE_TESTNET,
    SCAN_INTERVAL_SECONDS, MAX_POSITIONS, MAX_DAILY_TRADES, MAX_DAILY_LOSS_PCT,
    CAPITAL_INR
)


class TradingBot:
    """
    Main trading bot orchestrator.
    """

    def __init__(self):
        # Initialize exchange client
        self.client = DeltaExchangeClient(DELTA_API_KEY, DELTA_API_SECRET, USE_TESTNET)

        # Initialize components
        self.data_fetcher = DataFetcher(self.client)
        self.scanner = Scanner(self.data_fetcher)
        self.safety_gate = SafetyGate(self.data_fetcher)
        self.trade_logger = TradeLogger()
        self.position_manager = PositionManager()
        self.trade_manager = TradeManager(self.client, self.data_fetcher)

        # State
        self.daily_trades = 0
        self.running = False
        self.current_date = None

    async def start(self):
        """Start the trading bot."""
        self.running = True

        self._print_startup_banner()

        while self.running:
            try:
                await self._run_cycle()
                await asyncio.sleep(SCAN_INTERVAL_SECONDS)
            except KeyboardInterrupt:
                print("\n⚠️ Shutting down...")
                self.running = False
                break
            except Exception as e:
                print(f"❌ Error in main loop: {e}")
                await asyncio.sleep(60)

        self._print_shutdown()

    def _print_startup_banner(self):
        """Print startup banner."""
        print("\n" + "="*60)
        print("🚀 DELTA TRADER BOT STARTED")
        print("="*60)
        print(f"Capital: ₹{CAPITAL_INR}")
        print(f"Mode: {'TESTNET' if USE_TESTNET else 'LIVE'}")
        print(f"Max Positions: {MAX_POSITIONS}")
        print(f"Max Daily Trades: {MAX_DAILY_TRADES}")
        print(f"Scan Interval: {SCAN_INTERVAL_SECONDS}s")

        # Show previous performance
        if len(self.trade_logger.trades) > 0:
            total_pnl = self.trade_logger.get_total_pnl()
            print(f"\n📊 Previous Performance:")
            print(f"  Total Trades: {len(self.trade_logger.trades)}")
            print(f"  Total P&L: ₹{total_pnl:.2f}")

        print("="*60 + "\n")

    def _print_shutdown(self):
        """Print shutdown message."""
        print("\n" + "="*60)
        print("🛑 BOT STOPPED")
        print("="*60)

        # Show session summary
        daily_pnl = self.trade_logger.get_daily_pnl()
        print(f"\n📊 Today's Performance:")
        print(f"  Trades: {self.daily_trades}")
        print(f"  P&L: ₹{daily_pnl:.2f}")

        print("\n" + "="*60)

    async def _run_cycle(self):
        """Single trading cycle."""

        # Reset daily counter at midnight
        today = datetime.utcnow().date()
        if self.current_date != today:
            self.current_date = today
            self.daily_trades = 0
            print(f"\n📅 New trading day: {today}")

        # 1. Safety check
        safety = self.safety_gate.check()
        if not safety["allowed"]:
            print(f"⚠️ Safety gate: {safety['reason']}")
            return

        # 2. Check daily limits
        if self.daily_trades >= MAX_DAILY_TRADES:
            return

        daily_pnl = self.trade_logger.get_daily_pnl()
        if daily_pnl <= -CAPITAL_INR * MAX_DAILY_LOSS_PCT:
            print(f"⚠️ Daily loss limit reached: ₹{daily_pnl:.2f}")
            return

        # 3. Manage existing positions
        await self._manage_positions()

        # 4. Look for new setups if we have capacity
        if self.position_manager.count() < MAX_POSITIONS:
            await self._scan_and_trade()

    async def _manage_positions(self):
        """Check and manage open positions."""
        for symbol in list(self.position_manager.get_position_symbols()):
            pos_data = self.position_manager.get_position(symbol)

            try:
                # Get current price
                current_price = self.data_fetcher.get_current_price(symbol)

                if current_price == 0:
                    continue

                # Check if should exit
                should_exit, exit_reason = self.trade_manager.should_exit(pos_data, current_price)

                if should_exit:
                    await self._close_position(symbol, current_price, exit_reason)

            except Exception as e:
                print(f"❌ Error managing {symbol}: {e}")

    async def _close_position(self, symbol: str, exit_price: float, exit_reason: str):
        """Close a position."""
        pos_data = self.position_manager.get_position(symbol)

        if not pos_data:
            return

        try:
            # Execute exit order
            exit_order = self.trade_manager.exit_trade(pos_data, exit_price)

            if exit_order:
                # Get BTC context
                btc_price = self.data_fetcher.get_current_price("BTCUSDT")
                btc_trend = self._get_btc_trend()

                # Create trade record
                trade_record = self.trade_manager.create_trade_record(
                    pos_data,
                    exit_price,
                    exit_reason,
                    btc_price,
                    btc_trend
                )

                # Log trade
                self.trade_logger.log_trade(trade_record)

                # Remove position
                self.position_manager.remove_position(symbol)

                # Show insights periodically
                if len(self.trade_logger.trades) % 5 == 0:
                    self._show_insights()

        except Exception as e:
            print(f"❌ Error closing position {symbol}: {e}")

    async def _scan_and_trade(self):
        """Scan for setups and take trades."""
        try:
            # Scan all coins
            setups = self.scanner.scan_all()

            if not setups:
                return

            # Take the best setup that we don't already have
            for setup in setups:
                symbol = setup["symbol"]

                if self.position_manager.has_position(symbol):
                    continue

                # Check capacity again
                if self.position_manager.count() >= MAX_POSITIONS:
                    break

                # Take the trade
                await self._take_trade(setup)
                break  # One trade per cycle

        except Exception as e:
            print(f"❌ Error scanning: {e}")

    async def _take_trade(self, setup: Dict):
        """Execute a trade."""
        print(f"\n📊 NEW TRADE: {setup['symbol']} {setup['type']}")
        print(f"   Direction: {setup['direction']}")
        print(f"   Entry: {setup['entry']:.4f}")
        print(f"   Stop: {setup['stop']:.4f}")
        print(f"   Target: {setup['target']:.4f}")
        print(f"   Score: {setup['score']:.2f}")

        try:
            # Enter trade
            result = self.trade_manager.enter_trade(setup)

            if result:
                order = result["order"]
                position_info = result["position_info"]

                # Get actual entry price from order
                entry_price = order.get("average_fill_price") or order.get("price") or setup["entry"]

                # Add to position manager
                self.position_manager.add_position(
                    setup["symbol"],
                    setup,
                    position_info,
                    entry_price,
                    order.get("id")
                )

                self.daily_trades += 1

                print(f"   ✅ Position opened")
                print(f"   Risk: ₹{position_info['risk_inr']:.2f}")

            else:
                print(f"   ❌ Order failed")

        except Exception as e:
            print(f"   ❌ Error: {e}")

    def _get_btc_trend(self) -> str:
        """Get current BTC trend."""
        try:
            df = self.data_fetcher.get_ohlcv("BTCUSDT", "1h", limit=55)

            if df is None or len(df) < 55:
                return "UNKNOWN"

            from utils.indicators import ema

            close = df["close"]
            ema_21 = ema(close, 21).iloc[-1]
            ema_55 = ema(close, 55).iloc[-1]

            if ema_21 > ema_55 * 1.005:
                return "UP"
            elif ema_21 < ema_55 * 0.995:
                return "DOWN"
            else:
                return "RANGE"
        except:
            return "UNKNOWN"

    def _show_insights(self):
        """Show performance insights."""
        analyzer = PerformanceAnalyzer(self.trade_logger.trades)
        insights = analyzer.get_insights()

        print("\n" + "="*60)
        print("📊 PERFORMANCE INSIGHTS")
        print("="*60)
        for insight in insights:
            print(f"  {insight}")
        print("="*60 + "\n")
