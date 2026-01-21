"""
Analyze trading performance.
"""

import pandas as pd
from typing import Dict, List
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from learning.trade_logger import TradeRecord


class PerformanceAnalyzer:
    """
    Analyzes trade history to find what works.
    """

    def __init__(self, trades: List[TradeRecord]):
        self.trades = trades
        self.df = self._to_dataframe() if trades else pd.DataFrame()

    def _to_dataframe(self) -> pd.DataFrame:
        """Convert trades to DataFrame."""
        if not self.trades:
            return pd.DataFrame()
        return pd.DataFrame([t.__dict__ for t in self.trades])

    def get_summary(self) -> Dict:
        """Get overall performance summary."""
        if len(self.df) == 0:
            return {"message": "No trades yet"}

        winners = self.df[self.df["pnl_pct"] > 0]
        losers = self.df[self.df["pnl_pct"] <= 0]

        return {
            "total_trades": len(self.df),
            "total_pnl_inr": self.df["pnl_inr"].sum(),
            "total_pnl_pct": self.df["pnl_pct"].sum(),
            "win_rate": len(winners) / len(self.df) if len(self.df) > 0 else 0,
            "avg_winner_pct": winners["pnl_pct"].mean() if len(winners) > 0 else 0,
            "avg_loser_pct": losers["pnl_pct"].mean() if len(losers) > 0 else 0,
            "profit_factor": abs(winners["pnl_inr"].sum() / losers["pnl_inr"].sum()) if len(losers) > 0 and losers["pnl_inr"].sum() != 0 else float('inf'),
            "avg_duration_min": self.df["duration_minutes"].mean(),
            "best_trade_pct": self.df["pnl_pct"].max(),
            "worst_trade_pct": self.df["pnl_pct"].min(),
        }

    def get_by_setup_type(self) -> Dict:
        """Performance breakdown by setup type."""
        if len(self.df) == 0:
            return {}

        result = {}
        for setup_type in self.df["setup_type"].unique():
            subset = self.df[self.df["setup_type"] == setup_type]
            winners = subset[subset["pnl_pct"] > 0]

            result[setup_type] = {
                "trades": len(subset),
                "win_rate": len(winners) / len(subset) if len(subset) > 0 else 0,
                "total_pnl_pct": subset["pnl_pct"].sum(),
                "avg_pnl_pct": subset["pnl_pct"].mean(),
            }

        return result

    def get_by_symbol(self) -> Dict:
        """Performance breakdown by symbol."""
        if len(self.df) == 0:
            return {}

        result = {}
        for symbol in self.df["symbol"].unique():
            subset = self.df[self.df["symbol"] == symbol]
            winners = subset[subset["pnl_pct"] > 0]

            result[symbol] = {
                "trades": len(subset),
                "win_rate": len(winners) / len(subset) if len(subset) > 0 else 0,
                "total_pnl_inr": subset["pnl_inr"].sum(),
                "avg_pnl_pct": subset["pnl_pct"].mean(),
            }

        return result

    def get_by_hour(self) -> Dict:
        """Performance breakdown by hour."""
        if len(self.df) == 0:
            return {}

        result = {}
        for hour in sorted(self.df["hour_utc"].unique()):
            subset = self.df[self.df["hour_utc"] == hour]
            winners = subset[subset["pnl_pct"] > 0]

            result[hour] = {
                "trades": len(subset),
                "win_rate": len(winners) / len(subset) if len(subset) > 0 else 0,
                "avg_pnl_pct": subset["pnl_pct"].mean(),
            }

        return result

    def get_by_btc_trend(self) -> Dict:
        """Performance breakdown by BTC trend."""
        if len(self.df) == 0 or "btc_trend" not in self.df.columns:
            return {}

        result = {}
        for trend in self.df["btc_trend"].unique():
            subset = self.df[self.df["btc_trend"] == trend]
            winners = subset[subset["pnl_pct"] > 0]

            result[trend] = {
                "trades": len(subset),
                "win_rate": len(winners) / len(subset) if len(subset) > 0 else 0,
                "avg_pnl_pct": subset["pnl_pct"].mean(),
            }

        return result

    def get_by_direction(self) -> Dict:
        """Performance breakdown by direction (LONG/SHORT)."""
        if len(self.df) == 0:
            return {}

        result = {}
        for direction in self.df["direction"].unique():
            subset = self.df[self.df["direction"] == direction]
            winners = subset[subset["pnl_pct"] > 0]

            result[direction] = {
                "trades": len(subset),
                "win_rate": len(winners) / len(subset) if len(subset) > 0 else 0,
                "total_pnl_inr": subset["pnl_inr"].sum(),
                "avg_pnl_pct": subset["pnl_pct"].mean(),
            }

        return result

    def get_insights(self) -> List[str]:
        """Generate actionable insights."""
        insights = []

        if len(self.df) < 10:
            return ["📊 Need at least 10 trades for insights. Keep trading!"]

        summary = self.get_summary()
        by_setup = self.get_by_setup_type()
        by_hour = self.get_by_hour()

        # Win rate insight
        wr = summary["win_rate"]
        if wr < 0.4:
            insights.append(f"⚠️ Win rate is {wr:.1%} - review entry criteria")
        elif wr > 0.55:
            insights.append(f"✅ Win rate is {wr:.1%} - entries are working")

        # Best/worst setup
        if by_setup:
            best_setup = max(by_setup.items(), key=lambda x: x[1]["avg_pnl_pct"])
            worst_setup = min(by_setup.items(), key=lambda x: x[1]["avg_pnl_pct"])
            insights.append(f"📈 Best setup: {best_setup[0]} ({best_setup[1]['avg_pnl_pct']:.2%} avg)")
            insights.append(f"📉 Worst setup: {worst_setup[0]} ({worst_setup[1]['avg_pnl_pct']:.2%} avg) - consider removing")

        # Best/worst hour
        if by_hour and len(by_hour) >= 3:
            best_hour = max(by_hour.items(), key=lambda x: x[1]["avg_pnl_pct"])
            worst_hour = min(by_hour.items(), key=lambda x: x[1]["avg_pnl_pct"])
            insights.append(f"🕐 Best hour (UTC): {best_hour[0]}:00")
            insights.append(f"🕐 Worst hour (UTC): {worst_hour[0]}:00 - avoid trading")

        # Profit factor
        if summary["profit_factor"] < 1:
            insights.append(f"⚠️ Profit factor {summary['profit_factor']:.2f} - losing money overall")
        elif summary["profit_factor"] > 1.5:
            insights.append(f"✅ Profit factor {summary['profit_factor']:.2f} - system has edge")

        return insights

    def print_report(self):
        """Print comprehensive performance report."""
        print("\n" + "="*60)
        print("📊 PERFORMANCE REPORT")
        print("="*60)

        summary = self.get_summary()

        if "message" in summary:
            print(summary["message"])
            return

        print(f"\n📈 Overall Performance:")
        print(f"  Total Trades: {summary['total_trades']}")
        print(f"  Total P&L: ₹{summary['total_pnl_inr']:.2f}")
        print(f"  Win Rate: {summary['win_rate']:.1%}")
        print(f"  Profit Factor: {summary['profit_factor']:.2f}")
        print(f"  Avg Winner: {summary['avg_winner_pct']:.2%}")
        print(f"  Avg Loser: {summary['avg_loser_pct']:.2%}")

        by_setup = self.get_by_setup_type()
        if by_setup:
            print(f"\n📊 By Setup Type:")
            for setup, stats in sorted(by_setup.items(), key=lambda x: x[1]["avg_pnl_pct"], reverse=True):
                print(f"  {setup}: {stats['trades']} trades, {stats['win_rate']:.1%} WR, {stats['avg_pnl_pct']:.2%} avg")

        print("\n" + "="*60)
