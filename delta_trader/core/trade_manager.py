"""
Execute and manage trades.
"""

from typing import Dict, Optional
from datetime import datetime
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from exchange.executor import OrderExecutor
from risk.position_sizing import calculate_position
from learning.trade_logger import TradeRecord


class TradeManager:
    """
    Handles trade execution and management.
    """

    def __init__(self, client, data_fetcher):
        self.executor = OrderExecutor(client)
        self.data_fetcher = data_fetcher

    def enter_trade(self, setup: Dict) -> Optional[Dict]:
        """
        Enter a trade based on setup.

        Returns:
            Order response or None if failed
        """
        try:
            # Calculate position size
            position_info = calculate_position(setup)

            # Determine order side
            side = "buy" if setup["direction"] == "LONG" else "sell"

            # Execute market order
            order = self.executor.execute_market_order(
                setup["symbol"],
                side,
                position_info["size_units"]
            )

            if order:
                return {
                    "order": order,
                    "position_info": position_info
                }

            return None

        except Exception as e:
            print(f"Error entering trade: {e}")
            return None

    def exit_trade(self, position_data: Dict, current_price: float = None) -> Optional[Dict]:
        """
        Exit a trade.

        Returns:
            Order response or None if failed
        """
        try:
            setup = position_data["setup"]
            position_info = position_data["position"]

            # Determine order side (opposite of entry)
            side = "sell" if setup["direction"] == "LONG" else "buy"

            # Execute market order to close
            order = self.executor.execute_market_order(
                setup["symbol"],
                side,
                position_info["size_units"]
            )

            return order

        except Exception as e:
            print(f"Error exiting trade: {e}")
            return None

    def should_exit(
        self,
        position_data: Dict,
        current_price: float
    ) -> tuple:
        """
        Check if position should be exited.

        Returns:
            (should_exit: bool, reason: str or None)
        """
        setup = position_data["setup"]
        entry_time = position_data["entry_time"]

        # Check TP/SL
        if setup["direction"] == "LONG":
            if current_price >= setup["target"]:
                return True, "TP"
            elif current_price <= setup["stop"]:
                return True, "STOP"
        else:  # SHORT
            if current_price <= setup["target"]:
                return True, "TP"
            elif current_price >= setup["stop"]:
                return True, "STOP"

        # Check time limit (2 hours = 120 minutes)
        duration = (datetime.utcnow() - entry_time).total_seconds() / 60
        if duration > 120:
            return True, "TIME"

        return False, None

    def create_trade_record(
        self,
        position_data: Dict,
        exit_price: float,
        exit_reason: str,
        btc_price: float,
        btc_trend: str
    ) -> TradeRecord:
        """Create a trade record for logging."""
        setup = position_data["setup"]
        position_info = position_data["position"]
        entry_price = position_data["entry_price"]
        entry_time = position_data["entry_time"]

        # Calculate P&L
        if setup["direction"] == "LONG":
            pnl_pct = (exit_price - entry_price) / entry_price
        else:
            pnl_pct = (entry_price - exit_price) / entry_price

        pnl_inr = position_info["size_inr"] * pnl_pct

        duration = int((datetime.utcnow() - entry_time).total_seconds() / 60)

        return TradeRecord(
            id=position_data["id"],
            symbol=setup["symbol"],
            setup_type=setup["type"],
            direction=setup["direction"],
            score=setup["score"],
            entry_price=entry_price,
            entry_time=entry_time.isoformat(),
            position_size_inr=position_info["size_inr"],
            btc_price=btc_price,
            btc_trend=btc_trend,
            hour_utc=entry_time.hour,
            day_of_week=entry_time.weekday(),
            exit_price=exit_price,
            exit_time=datetime.utcnow().isoformat(),
            exit_reason=exit_reason,
            pnl_inr=pnl_inr,
            pnl_pct=pnl_pct,
            duration_minutes=duration,
        )
