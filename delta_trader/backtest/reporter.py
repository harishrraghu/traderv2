"""
Generate backtest reports.
"""

import json
import os
from typing import Dict
from datetime import datetime


class BacktestReporter:
    """
    Generates reports from backtest results.
    """

    def __init__(self, results: Dict):
        self.results = results

    def print_summary(self):
        """Print summary to console."""
        print("\n" + "="*60)
        print("📈 BACKTEST RESULTS")
        print("="*60)

        if "message" in self.results:
            print(f"\n{self.results['message']}")
            return

        summary = self.results["summary"]

        print(f"\n💰 Capital & Returns:")
        print(f"  Initial Capital: ₹{summary['initial_capital']:.0f}")
        print(f"  Final Capital: ₹{summary['final_capital']:.0f}")
        print(f"  P&L: ₹{summary['total_pnl_inr']:.2f}")
        print(f"  Return: {summary['total_return_pct']:.2%}")

        print(f"\n📊 Trade Statistics:")
        print(f"  Total Trades: {summary['total_trades']}")
        print(f"  Winning Trades: {summary['winning_trades']}")
        print(f"  Losing Trades: {summary['losing_trades']}")
        print(f"  Win Rate: {summary['win_rate']:.1%}")

        print(f"\n📈 Performance Metrics:")
        print(f"  Profit Factor: {summary['profit_factor']:.2f}")
        print(f"  Avg Winner: {summary['avg_winner_pct']:.2%}")
        print(f"  Avg Loser: {summary['avg_loser_pct']:.2%}")
        print(f"  Max Drawdown: {summary['max_drawdown_pct']:.2%}")
        print(f"  Avg Duration: {summary['avg_trade_duration_min']:.1f} minutes")

        # Setup breakdown
        print(f"\n📊 By Setup Type:")
        by_setup = self.results.get("by_setup_type", {})
        for setup, stats in sorted(by_setup.items(), key=lambda x: x[1]["avg_pnl_pct"], reverse=True):
            print(f"  {setup}:")
            print(f"    Trades: {stats['trades']}, WR: {stats['win_rate']:.1%}, Avg P&L: {stats['avg_pnl_pct']:.2%}")

        # Symbol breakdown
        print(f"\n📊 By Symbol:")
        by_symbol = self.results.get("by_symbol", {})
        for symbol, stats in sorted(by_symbol.items(), key=lambda x: x[1]["total_pnl_inr"], reverse=True):
            print(f"  {symbol}: {stats['trades']} trades, ₹{stats['total_pnl_inr']:.2f}")

        print("\n" + "="*60)

    def save_to_file(self, filepath: str = None):
        """Save full results to JSON file."""
        if filepath is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filepath = f"data/reports/backtest_{timestamp}.json"

        os.makedirs(os.path.dirname(filepath), exist_ok=True)

        # Convert datetime objects to strings for JSON serialization
        serializable_results = self._make_serializable(self.results)

        with open(filepath, 'w') as f:
            json.dump(serializable_results, f, indent=2)

        print(f"\n📁 Full report saved to: {filepath}")

    def _make_serializable(self, obj):
        """Convert non-serializable objects to serializable format."""
        if isinstance(obj, dict):
            return {k: self._make_serializable(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._make_serializable(item) for item in obj]
        elif hasattr(obj, '__dict__'):
            return self._make_serializable(obj.__dict__)
        elif isinstance(obj, (datetime,)):
            return obj.isoformat()
        elif isinstance(obj, float):
            if obj == float('inf'):
                return "Infinity"
            elif obj == float('-inf'):
                return "-Infinity"
            return obj
        else:
            return obj

    def get_insights(self) -> list:
        """Generate insights from backtest."""
        insights = []

        if "message" in self.results:
            return insights

        summary = self.results["summary"]

        # Return insights
        if summary["total_return_pct"] > 0.5:
            insights.append("✅ Strong positive returns - strategy is profitable")
        elif summary["total_return_pct"] < -0.2:
            insights.append("❌ Significant losses - strategy needs major revision")

        # Win rate insights
        if summary["win_rate"] > 0.55:
            insights.append("✅ High win rate - entries are working well")
        elif summary["win_rate"] < 0.4:
            insights.append("⚠️ Low win rate - review entry criteria")

        # Profit factor insights
        if summary["profit_factor"] > 1.5:
            insights.append("✅ Strong profit factor - winners outweigh losers")
        elif summary["profit_factor"] < 1:
            insights.append("❌ Profit factor below 1 - losing money overall")

        # Drawdown insights
        if abs(summary["max_drawdown_pct"]) > 0.3:
            insights.append("⚠️ High drawdown - consider reducing position sizes")

        return insights
