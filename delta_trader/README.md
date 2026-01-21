# Delta Trader - Crypto Trading Bot

A modular intraday crypto trading system for Delta Exchange designed for learning and small capital trading.

## Features

- **Multiple Trading Setups**: EMA Pullback, Breakout, RSI Extreme, Range Bounce, Momentum
- **Risk Management**: Position sizing, stop loss, take profit, daily loss limits
- **Safety Gate**: Prevents trading during extreme market conditions
- **Performance Tracking**: Detailed trade logging and analysis
- **Backtesting Engine**: Test strategies on historical data
- **Learning System**: Generates insights from trading performance

## Project Structure

```
delta_trader/
├── config/          # Configuration files
├── exchange/        # Delta Exchange API integration
├── strategy/        # Trading setups and scanning
├── risk/           # Risk management
├── core/           # Main bot logic
├── learning/       # Performance analysis
├── backtest/       # Backtesting engine
├── utils/          # Utilities and indicators
└── data/           # Trade logs and historical data
```

## Setup

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure API keys**:
   Edit `config/settings.py` and add your Delta Exchange API credentials:
   ```python
   DELTA_API_KEY = "your_api_key"
   DELTA_API_SECRET = "your_api_secret"
   ```

3. **Configure trading parameters**:
   Review and adjust settings in `config/settings.py`:
   - Capital amount
   - Position sizes
   - Risk parameters
   - Safety thresholds

## Usage

### Live Trading

**IMPORTANT**: Start with testnet mode first!

```bash
cd delta_trader
python main.py
```

The bot will:
- Scan for trading setups every 15 seconds
- Execute trades when conditions are met
- Manage positions with TP/SL
- Log all trades for analysis
- Show performance insights

### Backtesting

Test your strategy on historical data:

```bash
cd delta_trader
python run_backtest.py
```

This will:
- Fetch historical data for configured symbols
- Run the strategy on past data
- Generate performance report
- Save detailed results to `data/reports/`

## Configuration

### Capital Settings (`config/settings.py`)

- `CAPITAL_INR`: Base capital (default: ₹1000)
- `LEVERAGE`: Trading leverage (default: 5x)
- `POSITION_SIZE_PCT`: % of capital per trade (default: 40%)
- `MAX_POSITIONS`: Maximum concurrent positions (default: 2)
- `MAX_DAILY_TRADES`: Daily trade limit (default: 12)

### Risk Settings

- `STOP_LOSS_PCT`: Stop loss % (default: 1%)
- `TAKE_PROFIT_PCT`: Take profit % (default: 1.5%)
- `MAX_DAILY_LOSS_PCT`: Daily loss limit (default: 30%)

### Trading Universe (`config/coins.py`)

Default coins:
- BTCUSDT
- ETHUSDT
- SOLUSDT
- BNBUSDT
- XRPUSDT

## Trading Setups

### 1. EMA Pullback
Price pulls back to 21 EMA in a trending market (21 EMA > 55 EMA for uptrend)

### 2. Breakout
Price breaks above 20-period high (long) or below 20-period low (short)

### 3. RSI Extreme
RSI < 30 (oversold bounce) or RSI > 70 (overbought fade)

### 4. Range Bounce
Price bounces from Bollinger Band edges in ranging market

### 5. Momentum
Continuation trades on strong 3-candle moves (>2%)

## Performance Monitoring

The bot generates insights every 5 trades:
- Win rate analysis
- Best/worst setups
- Best/worst trading hours
- Profit factor

View trade history in `data/trades.json`

## Safety Features

### Safety Gate
Stops trading when:
- BTC moves >2% in 15 minutes (flash crash/pump)
- Funding rate is extreme (>15%)

### Daily Limits
- Maximum trades per day
- Maximum daily loss threshold
- Position limits

## File Structure

### Data Files
- `data/trades.json` - All trade history
- `data/historical/` - Cached historical price data
- `data/reports/` - Backtest reports

### Key Modules
- `exchange/client.py` - Delta Exchange API wrapper
- `exchange/data_fetcher.py` - Price data fetching
- `strategy/setups.py` - Setup detection logic
- `strategy/scanner.py` - Multi-symbol scanning
- `core/bot.py` - Main trading bot
- `backtest/engine.py` - Backtesting engine

## Development Workflow

1. **Start with backtesting**:
   ```bash
   python run_backtest.py
   ```

2. **Analyze results**:
   - Review backtest report
   - Check which setups work best
   - Adjust parameters if needed

3. **Test on testnet**:
   - Set `USE_TESTNET = True` in settings
   - Run live bot to test execution
   - Verify order placement works

4. **Go live (when ready)**:
   - Set `USE_TESTNET = False`
   - Start with small capital
   - Monitor closely

## Customization

### Adding New Setups

Edit `strategy/setups.py` and add your detector:

```python
def detect_my_setup(self, df: pd.DataFrame) -> Optional[Dict]:
    # Your logic here
    return {
        "type": "MY_SETUP",
        "direction": "LONG",
        "score": 0.6,
        "entry": current_price,
        "stop": stop_price,
        "target": target_price,
        "reason": "Description"
    }
```

Then add it to `detect_all_setups()`.

### Modifying Indicators

All indicators are in `utils/indicators.py`. They're simple implementations without external dependencies for transparency.

## Troubleshooting

### API Connection Issues
- Check API keys are correct
- Verify network connection
- Check Delta Exchange status

### No Trades Being Taken
- Review safety gate status
- Check if setups are being detected
- Verify position limits aren't reached

### Backtest Shows No Data
- Check date ranges in settings
- Ensure symbols are available on Delta
- Try fetching data manually first

## Disclaimer

This is a learning/educational trading system. Use at your own risk:

- Start with testnet mode
- Use only capital you can afford to lose
- Past performance doesn't guarantee future results
- Crypto trading involves substantial risk
- Always monitor your bot

## Support

For issues with:
- **Delta Exchange API**: Check their documentation at https://docs.delta.exchange
- **Python/Code**: Review error messages and check configurations
- **Strategy**: Backtest thoroughly and adjust parameters

## Next Steps

1. Run backtests on different time periods
2. Analyze which setups perform best
3. Disable underperforming setups
4. Adjust position sizing based on results
5. Test on testnet extensively
6. Keep detailed logs of all trades

## License

This project is for educational purposes. Use responsibly.
