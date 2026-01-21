"""
DELTA TRADER - Configuration Settings
Optimized based on backtest analysis
"""

# =============================================================================
# API CONFIGURATION
# =============================================================================
DELTA_API_KEY = "6CNdBGWFPkzozqSYBkaonGLBUmISOQ"
DELTA_API_SECRET = "zmfUKvVqH5OdGFdrtdH0LuhVyHrkg2hBzBm0pcEXzAQUQrhu7HhBoFMMwyks"
DELTA_BASE_URL = "https://api.delta.exchange"
DELTA_TESTNET_URL = "https://testnet-api.delta.exchange"
USE_TESTNET = True  # Always start with testnet

# =============================================================================
# CAPITAL & LEVERAGE
# =============================================================================
CAPITAL_INR = 1000
LEVERAGE = 5
EFFECTIVE_CAPITAL = CAPITAL_INR * LEVERAGE  # ₹5000

# =============================================================================
# POSITION SIZING (Dynamic based on setup quality)
# =============================================================================
POSITION_SIZE_BASE_PCT = 0.4  # Base: 40% of effective capital

# Score-based multipliers
POSITION_MULTIPLIERS = {
    "high_confidence": 1.0,    # Score >= 0.7
    "medium_confidence": 0.7,  # Score 0.5-0.7
    "low_confidence": 0.5,     # Score 0.4-0.5
}

# Trend alignment multipliers
TREND_MULTIPLIERS = {
    "strong_trend": 1.0,       # Trading with clear trend
    "weak_trend": 0.8,         # Trend exists but weak
    "ranging": 0.6,            # No clear trend
    "counter_trend": 0.0,      # BLOCKED - Don't trade against trend
}

# Legacy setting (for backward compatibility)
POSITION_SIZE_PCT = POSITION_SIZE_BASE_PCT

MAX_POSITIONS = 2
MAX_DAILY_TRADES = 8  # Reduced from 12 (quality over quantity)

# =============================================================================
# RISK MANAGEMENT
# =============================================================================
# Per-trade risk
MAX_RISK_PER_TRADE_PCT = 0.02  # 2% of capital max risk per trade

# Daily limits
MAX_DAILY_LOSS_PCT = 0.05     # Stop trading if down 5% (was 30% - too loose)
MAX_DAILY_LOSS_INR = CAPITAL_INR * MAX_DAILY_LOSS_PCT  # ₹50

# Consecutive loss handling
MAX_CONSECUTIVE_LOSSES = 3     # Pause after 3 losses in a row
COOLDOWN_AFTER_LOSSES_MIN = 60 # Wait 1 hour after hitting loss limit

# =============================================================================
# STOP LOSS & TAKE PROFIT (ATR-Based, not fixed)
# =============================================================================
# Old fixed values (for backward compatibility)
STOP_LOSS_PCT = 0.01
TAKE_PROFIT_PCT = 0.015

# New ATR-based values
USE_ATR_BASED_EXITS = True
ATR_PERIOD = 14
ATR_TIMEFRAME = "15m"

STOP_LOSS_ATR_MULTIPLE = 1.5    # Stop = 1.5 × ATR below entry
TAKE_PROFIT_1_ATR_MULTIPLE = 1.0  # TP1 = 1.0 × ATR (close 50%)
TAKE_PROFIT_2_ATR_MULTIPLE = 2.0  # TP2 = 2.0 × ATR (close 30%)
TAKE_PROFIT_3_ATR_MULTIPLE = 3.0  # TP3 = 3.0 × ATR (close 20%)

# Partial profit taking
PARTIAL_PROFITS = {
    "tp1_pct": 0.50,  # Close 50% at TP1
    "tp2_pct": 0.30,  # Close 30% at TP2
    "tp3_pct": 0.20,  # Let 20% run
}

# Breakeven stop
MOVE_STOP_TO_BREAKEVEN_AFTER_TP1 = True
BREAKEVEN_BUFFER_PCT = 0.001  # Add 0.1% buffer above entry

# =============================================================================
# TIMEFRAMES
# =============================================================================
PRIMARY_TIMEFRAME = "15m"       # Entry timeframe
CONFIRMATION_TIMEFRAME = "1h"   # Trend determination
CONTEXT_TIMEFRAME = "4h"        # Higher timeframe context (optional)

# =============================================================================
# TREND FILTER SETTINGS (NEW - Critical Addition)
# =============================================================================
TREND_FILTER_ENABLED = True     # Must be True for profitability

TREND_EMA_FAST = 21
TREND_EMA_SLOW = 55
TREND_TIMEFRAME = "1h"          # Determine trend on 1H

# Trend determination thresholds
TREND_THRESHOLD_PCT = 0.003     # EMAs must be 0.3% apart for clear trend
RANGING_ZONE_PCT = 0.003        # If EMAs within 0.3%, market is ranging

# What to do in each trend state
TREND_TRADING_RULES = {
    "uptrend": ["LONG"],           # Only longs in uptrend
    "downtrend": ["SHORT"],        # Only shorts in downtrend
    "ranging": [],                 # No trades in ranging (conservative)
    # "ranging": ["LONG", "SHORT"], # Uncomment for range trading
}

# =============================================================================
# SETUP DETECTION SETTINGS
# =============================================================================
MIN_SETUP_SCORE = 0.5           # Increased from 0.4 (higher quality bar)

# Setup-specific enable/disable
ENABLED_SETUPS = {
    "EMA_PULLBACK_LONG": True,   # ✅ Keep - 33% win rate
    "EMA_PULLBACK_SHORT": False, # ❌ Disabled - 7.7% win rate (disaster)
    "BREAKOUT_LONG": False,      # ❌ Disabled - 20% win rate
    "BREAKOUT_SHORT": True,      # ⚠️ Keep for now - needs more data
    "RSI_OVERSOLD_LONG": True,   # ✅ Keep
    "RSI_OVERBOUGHT_SHORT": False, # ❌ Disable until trend filter working
    "RANGE_BOUNCE_LONG": False,  # ❌ Disable for now
    "RANGE_BOUNCE_SHORT": False, # ❌ Disable for now
    "MOMENTUM_LONG": False,      # ❌ Disable - chasing
    "MOMENTUM_SHORT": False,     # ❌ Disable - chasing
}

# Setup quality scores (base scores before adjustments)
SETUP_BASE_SCORES = {
    "EMA_PULLBACK_LONG": 0.65,
    "EMA_PULLBACK_SHORT": 0.50,   # Lower score since it's risky
    "BREAKOUT_LONG": 0.45,
    "BREAKOUT_SHORT": 0.55,
    "RSI_OVERSOLD_LONG": 0.55,
    "RSI_OVERBOUGHT_SHORT": 0.50,
    "RANGE_BOUNCE_LONG": 0.45,
    "RANGE_BOUNCE_SHORT": 0.45,
    "MOMENTUM_LONG": 0.40,
    "MOMENTUM_SHORT": 0.40,
}

# =============================================================================
# ENTRY CONFIRMATION REQUIREMENTS (NEW)
# =============================================================================
REQUIRE_ENTRY_CONFIRMATION = True

# EMA Pullback specific
EMA_PULLBACK_CONFIG = {
    "ema_distance_max_pct": 0.005,    # Must be within 0.5% of EMA (was 1%)
    "ema_distance_min_pct": 0.001,    # Must be at least 0.1% (avoid sitting on EMA)
    "require_bounce_candle": True,     # Candle must show rejection
    "bounce_wick_ratio_min": 1.5,      # Wick must be 1.5x body size
    "rsi_min": 35,                     # RSI must be > 35 (not too oversold)
    "rsi_max": 50,                     # RSI must be < 50 (still has room)
    "lookback_for_pullback": 8,        # Must have been away from EMA in last 8 candles
    "away_distance_min_pct": 0.005,    # Was at least 0.5% away before pulling back
}

# Breakout specific
BREAKOUT_CONFIG = {
    "lookback_period": 20,             # 20-period high/low
    "min_break_pct": 0.002,            # Must break by at least 0.2%
    "require_volume_spike": False,     # Volume must confirm (disabled for backtest - no volume data)
    "volume_spike_multiple": 1.5,      # 150% of average volume
    "max_extension_pct": 0.01,         # Don't chase if already 1% extended
}

# =============================================================================
# TRADE COOLDOWN SETTINGS (NEW - Prevents Duplicate Trades)
# =============================================================================
COOLDOWN_ENABLED = True

# After entering a trade
COOLDOWN_AFTER_ENTRY_CANDLES = 8      # No new trade on same symbol for 8 candles (2 hours)

# After exiting a trade
COOLDOWN_AFTER_EXIT_CANDLES = 4       # No new trade on same symbol for 4 candles (1 hour)

# After a losing trade
COOLDOWN_AFTER_LOSS_CANDLES = 6       # Extra cooldown after a loss

# Global cooldown between any trades
MIN_CANDLES_BETWEEN_ANY_TRADE = 2     # At least 2 candles between any trades

# =============================================================================
# MARKET CONDITION FILTERS (NEW)
# =============================================================================
# Skip dead/low volatility markets
VOLATILITY_FILTER_ENABLED = True
MIN_ATR_PERCENTILE = 20               # Skip if ATR in bottom 20%
MIN_CANDLE_RANGE_PCT = 0.003          # Skip if last 4 candles combined range < 0.3%
MIN_RECENT_MOVEMENT_CANDLES = 4       # Check last 4 candles

# Volume filter
VOLUME_FILTER_ENABLED = False          # Disabled for backtest (no volume data)
MIN_VOLUME_PCT_OF_AVERAGE = 0.7       # Current volume must be > 70% of 20-period avg

# =============================================================================
# TIME-BASED EXIT RULES (Refined)
# =============================================================================
MAX_HOLD_TIME_MINUTES = 240           # 4 hours max (was effectively 2 hours)

# Early exit conditions
TIME_BASED_EXIT_RULES = {
    "exit_if_flat_after_minutes": 120,     # Exit if no movement after 2 hours
    "flat_threshold_pct": 0.003,           # "Flat" = less than 0.3% move
    "exit_if_profit_after_minutes": 90,    # Take profit if up after 1.5 hours
    "min_profit_for_early_exit_pct": 0.005, # Must be up at least 0.5% for early exit
}

# =============================================================================
# SCANNING SETTINGS
# =============================================================================
SCAN_INTERVAL_SECONDS = 30            # Increased from 15 (less noise)

# Minimum data requirements
MIN_CANDLES_FOR_ANALYSIS = 55         # Need 55 candles for EMA55

# =============================================================================
# SAFETY GATE THRESHOLDS
# =============================================================================
SAFETY_GATE_ENABLED = True

# BTC-based safety
BTC_FLASH_MOVE_PCT = 0.015            # 1.5% move in 15 min = danger (was 2%)
BTC_FLASH_LOOKBACK_CANDLES = 1        # Check last 1 candle

# Funding rate
EXTREME_FUNDING_RATE = 0.10           # 0.1% funding = extreme (was 0.15%)

# Liquidation cascade detection (if available)
LIQUIDATION_THRESHOLD_USD = 10000000  # $10M liquidations in 1 hour = danger

# =============================================================================
# SYMBOL CONFIGURATION
# =============================================================================
# Only trade these symbols (reduced list for focus)
TRADING_SYMBOLS = [
    "BTCUSDT",
    "ETHUSDT",
    # "SOLUSDT",  # Disabled - not enough data
    # "BNBUSDT",  # Disabled - no data on Delta
    # "XRPUSDT",  # Disabled - too few trades in backtest
]

# Symbol-specific settings (optional)
SYMBOL_CONFIGS = {
    "BTCUSDT": {
        "enabled": True,
        "max_position_pct": 0.5,      # Can use up to 50% of capital
        "min_volume_usd": 1000000,    # Minimum 24h volume
    },
    "ETHUSDT": {
        "enabled": True,
        "max_position_pct": 0.4,
        "min_volume_usd": 500000,
    },
}

# =============================================================================
# BACKTEST SETTINGS
# =============================================================================
BACKTEST_START_DATE = "2025-01-01"
BACKTEST_END_DATE = "2025-12-31"
BACKTEST_INITIAL_CAPITAL = 1000

# Backtest-specific
BACKTEST_INCLUDE_FEES = True
BACKTEST_FEE_PCT = 0.001              # 0.1% per trade (round trip = 0.2%)
BACKTEST_INCLUDE_SLIPPAGE = True
BACKTEST_SLIPPAGE_PCT = 0.0005        # 0.05% slippage estimate

# =============================================================================
# LOGGING & DEBUGGING
# =============================================================================
LOG_LEVEL = "INFO"                    # DEBUG, INFO, WARNING, ERROR
LOG_TRADES = True
LOG_SKIPPED_SETUPS = True             # Log why setups were skipped
LOG_TREND_CHANGES = True
SAVE_TRADE_HISTORY = True

# =============================================================================
# FEATURE FLAGS (Easy enable/disable for testing)
# =============================================================================
FEATURES = {
    "trend_filter": True,              # ✅ Critical - must be on
    "cooldown_system": True,           # ✅ Critical - prevents duplicates
    "volatility_filter": True,         # ✅ Important - skip dead markets
    "volume_filter": False,            # ⚠️ Disabled - no volume data in backtest
    "atr_based_exits": True,           # ✅ Important - dynamic stops
    "partial_profit_taking": False,    # ⚠️ Disabled for now (simplify)
    "breakeven_stop": False,           # ⚠️ Disabled for now (simplify)
    "entry_confirmation": True,        # ✅ Critical - quality entries
    "time_based_exits": True,          # ⚠️ Keep time exits
}
