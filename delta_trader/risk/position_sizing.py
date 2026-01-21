"""
Simple position sizing.
"""

import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.settings import (
    CAPITAL_INR, LEVERAGE, EFFECTIVE_CAPITAL,
    POSITION_SIZE_PCT, STOP_LOSS_PCT, TAKE_PROFIT_PCT
)


def calculate_position(setup: dict) -> dict:
    """
    Calculate position size and risk.

    Returns:
    {
        "size_inr": float,        # Position size in INR
        "size_units": float,      # Size in coin units
        "risk_inr": float,        # Max loss if stopped
        "risk_pct": float,        # Risk as % of capital
        "reward_inr": float,      # Expected profit if target hit
        "rr_ratio": float,        # Risk:Reward ratio
    }
    """
    position_size_inr = EFFECTIVE_CAPITAL * POSITION_SIZE_PCT
    position_size_units = position_size_inr / setup["entry"]

    # Calculate risk
    if setup["direction"] == "LONG":
        risk_pct = (setup["entry"] - setup["stop"]) / setup["entry"]
        reward_pct = (setup["target"] - setup["entry"]) / setup["entry"]
    else:
        risk_pct = (setup["stop"] - setup["entry"]) / setup["entry"]
        reward_pct = (setup["entry"] - setup["target"]) / setup["entry"]

    risk_inr = position_size_inr * risk_pct
    reward_inr = position_size_inr * reward_pct

    return {
        "size_inr": position_size_inr,
        "size_units": position_size_units,
        "risk_inr": risk_inr,
        "risk_pct": risk_inr / CAPITAL_INR,
        "reward_inr": reward_inr,
        "rr_ratio": reward_pct / risk_pct if risk_pct > 0 else 0,
    }


def validate_position_size(size_units: float, symbol: str) -> bool:
    """
    Validate if position size meets exchange requirements.
    """
    # Add minimum size checks based on exchange requirements
    # This is exchange-specific
    return size_units > 0
