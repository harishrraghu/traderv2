"""
Backtest engine using real historical data.
"""

import pandas as pd
from datetime import datetime
from typing import List, Dict
from dataclasses import dataclass
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from strategy.setups import SetupDetector
from risk.position_sizing import calculate_position
from config.settings import (
    CAPITAL_INR, MAX_POSITIONS, MAX_DAILY_TRADES,
    COOLDOWN_ENABLED, COOLDOWN_AFTER_ENTRY_CANDLES, COOLDOWN_AFTER_EXIT_CANDLES,
    COOLDOWN_AFTER_LOSS_CANDLES, MIN_CANDLES_BETWEEN_ANY_TRADE
)


@dataclass
class BacktestTrade:
    """Single backtest trade."""
    symbol: str
    setup_type: str
    direction: str
    entry_time: datetime
    entry_price: float
    exit_time: datetime
    exit_price: float
    exit_reason: str
    position_size_inr: float
    pnl_inr: float
    pnl_pct: float


class BacktestEngine:
    """
    Backtests strategy on historical data.

    Uses same SetupDetector as live trading for consistency.
    """

    def __init__(self, initial_capital: float = CAPITAL_INR):
        self.initial_capital = initial_capital
        self.capital = initial_capital
        self.setup_detector = SetupDetector()
        self.trades: List[BacktestTrade] = []
        self.equity_curve: List[Dict] = []

        # Cooldown tracking: {symbol: candle_count_when_available}
        self.symbol_cooldowns: Dict[str, int] = {}
        self.last_trade_candle: int = 0

    def run(
        self,
        data: Dict[str, pd.DataFrame],  # {symbol: DataFrame}
        start_date: str = None,
        end_date: str = None,
    ) -> Dict:
        """
        Run backtest.

        Args:
            data: Dict of symbol -> OHLCV DataFrame
            start_date: Optional start date filter
            end_date: Optional end date filter

        Returns:
            Backtest results dict
        """
        self.capital = self.initial_capital
        self.trades = []
        self.equity_curve = []
        self.symbol_cooldowns = {}
        self.last_trade_candle = 0

        # Get all timestamps across all symbols
        all_timestamps = set()
        for symbol, df in data.items():
            all_timestamps.update(df.index.tolist())

        all_timestamps = sorted(all_timestamps)

        # Filter by date range
        if start_date:
            start_dt = pd.to_datetime(start_date)
            all_timestamps = [t for t in all_timestamps if t >= start_dt]
        if end_date:
            end_dt = pd.to_datetime(end_date)
            all_timestamps = [t for t in all_timestamps if t <= end_dt]

        open_positions = {}  # {symbol: position_data}
        daily_trades = 0
        current_date = None

        print(f"\nRunning backtest on {len(all_timestamps)} timestamps...")

        # Iterate through each timestamp
        for i, timestamp in enumerate(all_timestamps):
            # Progress update
            if i % 1000 == 0:
                print(f"  Progress: {i}/{len(all_timestamps)} ({i/len(all_timestamps)*100:.1f}%)")

            # Reset daily counter
            if current_date != timestamp.date():
                current_date = timestamp.date()
                daily_trades = 0

            # Check and close existing positions
            for symbol in list(open_positions.keys()):
                if symbol in data and timestamp in data[symbol].index:
                    pos = open_positions[symbol]
                    current_bar = data[symbol].loc[timestamp]

                    closed, trade = self._check_exit(pos, current_bar, timestamp)
                    if closed:
                        self.trades.append(trade)
                        self.capital += trade.pnl_inr
                        del open_positions[symbol]

                        # Set cooldown after exit
                        if COOLDOWN_ENABLED:
                            cooldown_candles = COOLDOWN_AFTER_EXIT_CANDLES
                            if trade.pnl_pct < 0:  # Extra cooldown for losses
                                cooldown_candles = COOLDOWN_AFTER_LOSS_CANDLES
                            self.symbol_cooldowns[symbol] = i + cooldown_candles

            # Look for new setups if we have capacity
            if len(open_positions) < MAX_POSITIONS and daily_trades < MAX_DAILY_TRADES:
                for symbol, df in data.items():
                    if symbol in open_positions:
                        continue

                    if timestamp not in df.index:
                        continue

                    # Check cooldown
                    if COOLDOWN_ENABLED:
                        # Global cooldown between any trades
                        if i < self.last_trade_candle + MIN_CANDLES_BETWEEN_ANY_TRADE:
                            continue

                        # Symbol-specific cooldown
                        if symbol in self.symbol_cooldowns and i < self.symbol_cooldowns[symbol]:
                            continue

                    # Get data up to current timestamp
                    idx = df.index.get_loc(timestamp)
                    if idx < 55:  # Need enough history
                        continue

                    historical = df.iloc[:idx+1].copy()

                    # Detect setups
                    setups = self.setup_detector.detect_all_setups(historical, symbol)

                    if setups:
                        best_setup = max(setups, key=lambda x: x["score"])

                        # Take the trade
                        position_info = calculate_position(best_setup)

                        open_positions[symbol] = {
                            "setup": best_setup,
                            "position": position_info,
                            "entry_time": timestamp,
                            "entry_price": best_setup["entry"],
                        }

                        daily_trades += 1

                        # Set cooldown after entry
                        if COOLDOWN_ENABLED:
                            self.symbol_cooldowns[symbol] = i + COOLDOWN_AFTER_ENTRY_CANDLES
                            self.last_trade_candle = i

                        if len(open_positions) >= MAX_POSITIONS:
                            break

            # Record equity
            self.equity_curve.append({
                "timestamp": timestamp,
                "capital": self.capital,
                "open_positions": len(open_positions),
            })

        # Close any remaining positions at end
        for symbol, pos in open_positions.items():
            if symbol in data:
                last_bar = data[symbol].iloc[-1]
                _, trade = self._check_exit(pos, last_bar, all_timestamps[-1], force_close=True)
                self.trades.append(trade)
                self.capital += trade.pnl_inr

        print(f"  ✅ Backtest complete: {len(self.trades)} trades executed\n")

        return self._generate_report()

    def _check_exit(
        self,
        position: Dict,
        current_bar: pd.Series,
        timestamp: datetime,
        force_close: bool = False
    ) -> tuple:
        """
        Check if position should be closed.

        Returns: (closed: bool, trade: BacktestTrade or None)
        """
        setup = position["setup"]
        entry_price = position["entry_price"]
        current_price = current_bar["close"]
        high = current_bar["high"]
        low = current_bar["low"]

        exit_reason = None
        exit_price = current_price

        if setup["direction"] == "LONG":
            # Check stop
            if low <= setup["stop"]:
                exit_reason = "STOP"
                exit_price = setup["stop"]
            # Check target
            elif high >= setup["target"]:
                exit_reason = "TP"
                exit_price = setup["target"]
        else:  # SHORT
            # Check stop
            if high >= setup["stop"]:
                exit_reason = "STOP"
                exit_price = setup["stop"]
            # Check target
            elif low <= setup["target"]:
                exit_reason = "TP"
                exit_price = setup["target"]

        # Time-based exit (2 hours = 8 candles on 15m)
        entry_time = position["entry_time"]
        duration = (timestamp - entry_time).total_seconds() / 60
        if duration > 120 and exit_reason is None:
            exit_reason = "TIME"
            exit_price = current_price

        if force_close and exit_reason is None:
            exit_reason = "END"
            exit_price = current_price

        if exit_reason:
            # Calculate P&L
            pos_info = position["position"]
            if setup["direction"] == "LONG":
                pnl_pct = (exit_price - entry_price) / entry_price
            else:
                pnl_pct = (entry_price - exit_price) / entry_price

            pnl_inr = pos_info["size_inr"] * pnl_pct

            trade = BacktestTrade(
                symbol=setup["symbol"],
                setup_type=setup["type"],
                direction=setup["direction"],
                entry_time=position["entry_time"],
                entry_price=entry_price,
                exit_time=timestamp,
                exit_price=exit_price,
                exit_reason=exit_reason,
                position_size_inr=pos_info["size_inr"],
                pnl_inr=pnl_inr,
                pnl_pct=pnl_pct,
            )

            return True, trade

        return False, None

    def _generate_report(self) -> Dict:
        """Generate backtest report."""
        if not self.trades:
            return {"message": "No trades executed"}

        df = pd.DataFrame([t.__dict__ for t in self.trades])

        winners = df[df["pnl_pct"] > 0]
        losers = df[df["pnl_pct"] <= 0]

        # Calculate drawdown
        equity_df = pd.DataFrame(self.equity_curve)
        equity_df["peak"] = equity_df["capital"].cummax()
        equity_df["drawdown"] = (equity_df["capital"] - equity_df["peak"]) / equity_df["peak"]
        max_drawdown = equity_df["drawdown"].min()

        return {
            "summary": {
                "initial_capital": self.initial_capital,
                "final_capital": self.capital,
                "total_return_pct": (self.capital - self.initial_capital) / self.initial_capital,
                "total_pnl_inr": self.capital - self.initial_capital,
                "total_trades": len(df),
                "winning_trades": len(winners),
                "losing_trades": len(losers),
                "win_rate": len(winners) / len(df) if len(df) > 0 else 0,
                "profit_factor": abs(winners["pnl_inr"].sum() / losers["pnl_inr"].sum()) if len(losers) > 0 and losers["pnl_inr"].sum() != 0 else float('inf'),
                "avg_winner_pct": winners["pnl_pct"].mean() if len(winners) > 0 else 0,
                "avg_loser_pct": losers["pnl_pct"].mean() if len(losers) > 0 else 0,
                "max_drawdown_pct": max_drawdown,
                "avg_trade_duration_min": (df["exit_time"] - df["entry_time"]).mean().total_seconds() / 60,
                "best_trade_pct": df["pnl_pct"].max(),
                "worst_trade_pct": df["pnl_pct"].min(),
            },
            "by_setup_type": self._breakdown_by(df, "setup_type"),
            "by_symbol": self._breakdown_by(df, "symbol"),
            "by_direction": self._breakdown_by(df, "direction"),
            "trades": self.trades,
            "equity_curve": self.equity_curve,
        }

    def _breakdown_by(self, df: pd.DataFrame, column: str) -> Dict:
        """Generate breakdown statistics by a column."""
        result = {}
        for value in df[column].unique():
            subset = df[df[column] == value]
            winners = subset[subset["pnl_pct"] > 0]

            result[value] = {
                "trades": len(subset),
                "win_rate": len(winners) / len(subset) if len(subset) > 0 else 0,
                "total_pnl_inr": subset["pnl_inr"].sum(),
                "avg_pnl_pct": subset["pnl_pct"].mean(),
            }

        return result
