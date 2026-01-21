"""
Manage open positions.
"""

from typing import Dict, List, Optional
from datetime import datetime
import uuid


class PositionManager:
    """
    Tracks and manages open positions.
    """

    def __init__(self):
        self.positions: Dict[str, Dict] = {}

    def add_position(
        self,
        symbol: str,
        setup: Dict,
        position_info: Dict,
        entry_price: float,
        order_id: str = None
    ) -> str:
        """
        Add a new position.

        Returns:
            position_id
        """
        position_id = str(uuid.uuid4())

        self.positions[symbol] = {
            "id": position_id,
            "symbol": symbol,
            "setup": setup,
            "position": position_info,
            "entry_time": datetime.utcnow(),
            "entry_price": entry_price,
            "order_id": order_id,
        }

        return position_id

    def remove_position(self, symbol: str) -> Optional[Dict]:
        """Remove and return a position."""
        return self.positions.pop(symbol, None)

    def get_position(self, symbol: str) -> Optional[Dict]:
        """Get position for a symbol."""
        return self.positions.get(symbol)

    def has_position(self, symbol: str) -> bool:
        """Check if there's an open position for a symbol."""
        return symbol in self.positions

    def get_all_positions(self) -> Dict[str, Dict]:
        """Get all open positions."""
        return self.positions

    def count(self) -> int:
        """Get number of open positions."""
        return len(self.positions)

    def get_position_symbols(self) -> List[str]:
        """Get list of symbols with open positions."""
        return list(self.positions.keys())

    def clear_all(self):
        """Clear all positions (use with caution)."""
        self.positions.clear()
