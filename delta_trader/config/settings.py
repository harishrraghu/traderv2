"""
All system configuration in one place.
User will add API keys later - use placeholders.
"""

# Delta Exchange API
DELTA_API_KEY = ""  # User will fill
DELTA_API_SECRET = ""  # User will fill
DELTA_BASE_URL = "https://api.delta.exchange"
DELTA_TESTNET_URL = "https://testnet-api.delta.exchange"
USE_TESTNET = True  # Start with testnet

# Capital Settings
CAPITAL_INR = 1000
LEVERAGE = 5
EFFECTIVE_CAPITAL = CAPITAL_INR * LEVERAGE

# Position Settings
POSITION_SIZE_PCT = 0.4  # 40% of effective capital per trade
MAX_POSITIONS = 2
MAX_DAILY_TRADES = 12

# Risk Settings
STOP_LOSS_PCT = 0.01  # 1%
TAKE_PROFIT_PCT = 0.015  # 1.5%
MAX_DAILY_LOSS_PCT = 0.30  # Stop trading if down 30% of capital

# Scanning Settings
SCAN_INTERVAL_SECONDS = 15
MIN_SETUP_SCORE = 0.4
PRIMARY_TIMEFRAME = "15m"
CONFIRMATION_TIMEFRAME = "1h"

# Safety Gate Thresholds
BTC_FLASH_MOVE_PCT = 0.02  # 2% move in 15 min = danger
EXTREME_FUNDING_RATE = 0.15

# Backtest Settings
BACKTEST_START_DATE = "2024-12-01"  # More realistic: last 2 months
BACKTEST_END_DATE = "2025-01-21"    # Or use shorter range based on API limits
BACKTEST_INITIAL_CAPITAL = 1000
