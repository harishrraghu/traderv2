"""
Log all trades for analysis.
"""

import json
import os
from datetime import datetime
from typing import List, Dict, Optional
from dataclasses import dataclass, asdict


@dataclass
class TradeRecord:
    """Complete trade record."""
    id: str
    symbol: str
    setup_type: str
    direction: str
    score: float

    # Entry
    entry_price: float
    entry_time: str
    position_size_inr: float

    # Context
    btc_price: float
    btc_trend: str
    hour_utc: int
    day_of_week: int

    # Exit
    exit_price: float
    exit_time: str
    exit_reason: str  # "TP", "STOP", "MANUAL", "TIME"

    # Results
    pnl_inr: float
    pnl_pct: float
    duration_minutes: int


class TradeLogger:
    """
    Logs trades to JSON file.
    """

    def __init__(self, filepath: str = "data/trades.json"):
        self.filepath = filepath
        self.trades: List[TradeRecord] = []
        self._load()

    def _load(self):
        """Load existing trades from file."""
        if os.path.exists(self.filepath):
            try:
                with open(self.filepath, 'r') as f:
                    data = json.load(f)
                    self.trades = [TradeRecord(**t) for t in data]
            except:
                self.trades = []

    def _save(self):
        """Save trades to file."""
        os.makedirs(os.path.dirname(self.filepath), exist_ok=True)
        with open(self.filepath, 'w') as f:
            json.dump([asdict(t) for t in self.trades], f, indent=2)

    def log_trade(self, trade: TradeRecord):
        """Log a completed trade."""
        self.trades.append(trade)
        self._save()
        self._print_trade(trade)

    def _print_trade(self, trade: TradeRecord):
        """Print trade summary."""
        emoji = "✅" if trade.pnl_inr > 0 else "❌"
        print(f"\n{emoji} {trade.symbol} | {trade.setup_type}")
        print(f"   P&L: ₹{trade.pnl_inr:.2f} ({trade.pnl_pct:.2%})")
        print(f"   Exit: {trade.exit_reason} after {trade.duration_minutes} min")

    def get_all_trades(self) -> List[TradeRecord]:
        """Get all logged trades."""
        return self.trades

    def get_recent_trades(self, n: int = 10) -> List[TradeRecord]:
        """Get last n trades."""
        return self.trades[-n:]

    def get_today_trades(self) -> List[TradeRecord]:
        """Get trades from today."""
        today = datetime.utcnow().date()
        return [t for t in self.trades if datetime.fromisoformat(t.entry_time).date() == today]

    def get_daily_pnl(self) -> float:
        """Get today's P&L."""
        today_trades = self.get_today_trades()
        return sum(t.pnl_inr for t in today_trades)

    def get_total_pnl(self) -> float:
        """Get total P&L across all trades."""
        return sum(t.pnl_inr for t in self.trades)
