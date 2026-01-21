"""
Generate trading insights and recommendations.
"""

from typing import List, Dict
from learning.analyzer import PerformanceAnalyzer
from learning.trade_logger import TradeRecord


class InsightGenerator:
    """
    Generates actionable insights from trading data.
    """

    def __init__(self, trades: List[TradeRecord]):
        self.analyzer = PerformanceAnalyzer(trades)

    def get_all_insights(self) -> Dict:
        """Get all insights categorized."""
        return {
            "general": self.analyzer.get_insights(),
            "recommendations": self._get_recommendations(),
            "warnings": self._get_warnings(),
        }

    def _get_recommendations(self) -> List[str]:
        """Get actionable recommendations."""
        recommendations = []
        summary = self.analyzer.get_summary()

        if "message" in summary:
            return ["Keep trading to gather more data"]

        # Based on win rate
        if summary["win_rate"] < 0.45:
            recommendations.append("Consider tightening entry criteria")
            recommendations.append("Focus on higher-score setups only")

        # Based on profit factor
        if summary["profit_factor"] < 1:
            recommendations.append("System is losing money - review all setups")
            recommendations.append("Consider reducing position size")

        # Based on setup performance
        by_setup = self.analyzer.get_by_setup_type()
        if by_setup:
            # Find losing setups
            losing_setups = [s for s, stats in by_setup.items() if stats["avg_pnl_pct"] < 0]
            if losing_setups:
                recommendations.append(f"Disable losing setups: {', '.join(losing_setups)}")

        return recommendations

    def _get_warnings(self) -> List[str]:
        """Get warning messages."""
        warnings = []
        summary = self.analyzer.get_summary()

        if "message" in summary:
            return []

        # High loss warning
        if summary["total_pnl_inr"] < -500:
            warnings.append("⚠️ Total loss exceeds ₹500 - consider stopping")

        # Poor win rate
        if summary["win_rate"] < 0.3:
            warnings.append("⚠️ Win rate below 30% - system not working")

        return warnings

    def should_stop_trading(self) -> tuple:
        """
        Determine if trading should stop.
        Returns: (should_stop: bool, reason: str)
        """
        summary = self.analyzer.get_summary()

        if "message" in summary:
            return False, None

        # Stop if massive losses
        if summary["total_pnl_inr"] < -700:
            return True, "Total loss exceeds ₹700"

        # Stop if consistently losing
        if len(self.analyzer.trades) >= 20 and summary["profit_factor"] < 0.5:
            return True, "Profit factor too low after 20+ trades"

        return False, None
