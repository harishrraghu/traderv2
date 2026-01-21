# Quick Start Guide - Delta Trader

## 🚀 Get Started in 5 Minutes

### Step 1: Install Dependencies

```bash
cd delta_trader
pip install -r requirements.txt
```

### Step 2: Configure API Keys

1. Sign up for Delta Exchange: https://www.delta.exchange
2. Create API keys (enable testnet first!)
3. Edit `config/settings.py`:

```python
# Replace these with your actual keys
DELTA_API_KEY = "your_api_key_here"
DELTA_API_SECRET = "your_api_secret_here"
USE_TESTNET = True  # Keep this True for testing!
```

### Step 3: Run Your First Backtest

This tests the strategy on historical data:

```bash
python run_backtest.py
```

Expected output:
- Fetches historical data for BTC, ETH, SOL, BNB, XRP
- Runs strategy simulation
- Shows performance metrics
- Saves report to `data/reports/`

### Step 4: Start Live Trading (Testnet)

**IMPORTANT**: Make sure `USE_TESTNET = True` in settings!

```bash
python main.py
```

The bot will:
- ✅ Scan for setups every 15 seconds
- ✅ Execute trades on testnet
- ✅ Manage positions automatically
- ✅ Log all trades to `data/trades.json`

Press `Ctrl+C` to stop.

---

## 📊 Understanding the Output

### Backtest Results

```
Capital: ₹1000 → ₹1050
Return: 5.00%
Total Trades: 45
Win Rate: 55.5%
Profit Factor: 1.65
Max Drawdown: -8.2%
```

**What this means**:
- Made ₹50 profit on ₹1000 capital
- 55.5% of trades were winners
- Profit factor >1 means profitable overall
- Worst drawdown was 8.2%

### Live Trading Output

```
📊 NEW TRADE: BTCUSDT EMA_PULLBACK_LONG
   Direction: LONG
   Entry: 45250.00
   Stop: 44800.00
   Target: 45900.00
   Risk: ₹25.00
   ✅ Position opened
```

---

## ⚙️ Configuration Tips

### Adjust Position Size

In `config/settings.py`:

```python
POSITION_SIZE_PCT = 0.4  # 40% of capital per trade

# More conservative: 0.2 (20%)
# More aggressive: 0.5 (50%)
```

### Change Trading Coins

In `config/coins.py`:

```python
TRADING_COINS = [
    "BTCUSDT",
    "ETHUSDT",
    # Add more symbols...
]
```

### Adjust Risk/Reward

In `config/settings.py`:

```python
STOP_LOSS_PCT = 0.01    # 1% stop loss
TAKE_PROFIT_PCT = 0.015  # 1.5% take profit

# Tighter stops: 0.008 / 0.012
# Wider stops: 0.015 / 0.025
```

---

## 🎯 What to Do Next

### 1. Analyze Backtest Results

After running backtest, check:
- Which setups have highest win rate?
- Which symbols perform best?
- What time of day is best?

Look in the backtest report for "By Setup Type" breakdown.

### 2. Disable Poor Setups

If a setup consistently loses, disable it in `strategy/setups.py`:

```python
def detect_all_setups(self, df: pd.DataFrame, symbol: str) -> List[Dict]:
    detectors = [
        self.detect_ema_pullback,
        self.detect_breakout,
        # self.detect_rsi_extreme,  # Commented out = disabled
        self.detect_range_bounce,
        self.detect_momentum,
    ]
```

### 3. Monitor Performance

Check `data/trades.json` regularly:
```bash
cat data/trades.json | grep pnl_inr
```

Or view insights in the bot output (shown every 5 trades).

### 4. Optimize Parameters

Based on backtest results, adjust:
- Setup detection thresholds
- Stop loss / take profit levels
- Position sizes
- Maximum positions

---

## 🛡️ Safety Checklist

Before going live with real money:

- [ ] Run successful backtests on at least 6 months of data
- [ ] Test on testnet for at least 1 week
- [ ] Verify all trades execute correctly
- [ ] Understand all configuration parameters
- [ ] Start with minimum capital
- [ ] Set up monitoring/alerts
- [ ] Have a plan to stop the bot if needed

---

## 🐛 Common Issues

### "No data available"
**Fix**: Check internet connection and Delta Exchange API status

### "API Error 401"
**Fix**: Verify API keys are correct in `config/settings.py`

### "Safety gate: BTC flash move"
**Fix**: This is normal - bot pauses during extreme volatility

### "No trades being taken"
**Fix**:
1. Check if setups are being detected
2. Verify position limits aren't reached
3. Review safety gate status

---

## 📈 Performance Monitoring

### View All Trades
```bash
python -c "import json; print(json.dumps(json.load(open('data/trades.json')), indent=2))"
```

### Calculate Win Rate
```bash
python -c "
import json
trades = json.load(open('data/trades.json'))
winners = [t for t in trades if t['pnl_inr'] > 0]
print(f'Win Rate: {len(winners)/len(trades)*100:.1f}%')
"
```

---

## 🎓 Learning Resources

### Understanding the Strategy

Each setup type has different characteristics:

1. **EMA Pullback**: Best in trending markets
2. **Breakout**: Works in volatile markets
3. **RSI Extreme**: Mean reversion plays
4. **Range Bounce**: Best in sideways markets
5. **Momentum**: Trend continuation

### Reading the Code

Start with these files:
1. `strategy/setups.py` - Setup logic
2. `core/bot.py` - Main bot loop
3. `config/settings.py` - All settings

---

## 💡 Pro Tips

1. **Start Small**: Use minimum capital first
2. **Keep Logs**: All trades are logged automatically
3. **Review Daily**: Check performance every day
4. **Adjust Gradually**: Small changes, test thoroughly
5. **Stay Disciplined**: Let the bot run, don't interfere
6. **Monitor BTC**: Most alts follow Bitcoin

---

## 🆘 Getting Help

1. Check error messages carefully
2. Review configuration files
3. Look at `data/trades.json` for trade history
4. Check Delta Exchange API status
5. Re-run backtests to verify setup

---

## ✅ Success Metrics

**Good signs**:
- Win rate >45%
- Profit factor >1.2
- Consistent small wins
- Drawdown <20%

**Warning signs**:
- Win rate <35%
- Profit factor <0.8
- Large consecutive losses
- Drawdown >30%

If you see warning signs, **STOP** and:
1. Review trade logs
2. Run more backtests
3. Adjust parameters
4. Test on testnet again

---

Happy Trading! 🚀

Remember: This is a learning system. Start small, learn continuously, and only risk what you can afford to lose.
