# 📊 Getting More Historical Data

## Problem: Not Enough Historical Data

If you're seeing fewer candles than expected (e.g., 825 instead of 35,000), here's how to fix it.

## 🔍 Why This Happens

1. **API Pagination Issues** - Data fetching stops after first batch
2. **Testnet Limitations** - Limited historical data available
3. **Network/Proxy Issues** - Connection fails mid-download
4. **Symbol Names Wrong** - Using incorrect symbol format
5. **API Rate Limits** - Too many requests throttled

## ✅ Solutions

### Step 1: Use Production API (Not Testnet)

Testnet often has limited historical data. Production has more.

**Edit `config/settings.py`:**
```python
USE_TESTNET = False  # Change to False for production
```

**⚠️ Warning**: Production API uses real market data. Make sure your API keys have correct permissions.

---

### Step 2: Check Symbol Names

Delta Exchange might use different symbol formats. Check their documentation.

**Common formats:**
- `BTCUSDT` ✅
- `BTCUSD` (might be this)
- `BTC_USDT` (with underscore)
- `BTCUSDTPERP` (with contract type)

**How to verify:**

1. Go to Delta Exchange website
2. Find the trading pair you want
3. Look at the URL or contract details
4. Use exact symbol name in `config/coins.py`

**Example:**
```python
# In config/coins.py
TRADING_COINS = [
    "BTCUSD",      # Try without 'T' at end
    "ETHUSD",
    "SOLUSD",
    # etc
]
```

---

### Step 3: Adjust Date Range

Ask for data Delta Exchange actually has.

**Recent data (more reliable):**
```python
# In config/settings.py
BACKTEST_START_DATE = "2024-12-01"  # Last 2 months
BACKTEST_END_DATE = "2025-01-21"
```

**Very recent (most reliable):**
```python
BACKTEST_START_DATE = "2025-01-01"  # Last 3 weeks
BACKTEST_END_DATE = "2025-01-21"
```

---

### Step 4: Check API Response Details

Add debug logging to see what's happening:

**Edit `exchange/data_fetcher.py`** - Find the `fetch_historical_data` method and add:

```python
def fetch_historical_data(self, ...):
    # ... existing code ...

    while current_start < end_ts:
        current_end = min(current_start + (batch_size * timeframe_seconds), end_ts)

        print(f"  Fetching batch: {datetime.fromtimestamp(current_start)} to {datetime.fromtimestamp(current_end)}")

        candles = self.client.get_candles(symbol, timeframe, current_start, current_end)

        if candles:
            all_candles.extend(candles)
            print(f"    ✅ Got {len(candles)} candles (total: {len(all_candles)})")
        else:
            print(f"    ❌ No data returned - stopping")
            break  # Stop if no data returned

        # ... rest of code ...
```

This will show you exactly where the data fetching stops.

---

### Step 5: Reduce Batch Size

The API might have a limit on candles per request.

**Edit `exchange/data_fetcher.py`:**

```python
def fetch_historical_data(self, ...):
    # ... existing code ...

    batch_size = 500  # Reduce from 1000 to 500

    # Or try even smaller:
    batch_size = 200
```

---

### Step 6: Add More Delay Between Requests

Rate limiting might be kicking in.

**Edit `exchange/data_fetcher.py`:**

```python
# Find this line:
time.sleep(0.5)  # Rate limiting

# Change to:
time.sleep(2.0)  # Longer delay to avoid rate limits
```

---

### Step 7: Check Delta Exchange API Documentation

1. Visit: https://docs.delta.exchange/
2. Find "Historical Data" or "Candles" endpoint
3. Check:
   - Maximum candles per request
   - Maximum lookback period
   - Symbol naming convention
   - Rate limits

---

### Step 8: Contact Delta Exchange Support

If nothing works:

1. Check Delta Exchange status page
2. Contact their support
3. Ask:
   - "What's the maximum historical data available?"
   - "What's the correct symbol format for BTC perpetual?"
   - "What are the API rate limits?"
   - "Does testnet have limited historical data?"

---

## 🔬 Diagnosis Commands

**Check what data you actually got:**
```bash
python analyze_downloaded_data.py
```

**Check what symbols are available:**
```bash
python check_data_availability.py
```

**Manually test API:**
```python
from exchange.client import DeltaExchangeClient

client = DeltaExchangeClient("your_key", "your_secret", testnet=False)

# Check products
products = client.get_products()
for p in products[:10]:
    print(p.get('symbol'), p.get('contract_type'))

# Check specific symbol
ticker = client.get_ticker("BTCUSD")
print(ticker)

# Try getting candles
import time
end = int(time.time())
start = end - (7 * 24 * 60 * 60)  # Last 7 days
candles = client.get_candles("BTCUSD", "15m", start, end)
print(f"Got {len(candles)} candles")
```

---

## 📋 Quick Checklist

When running on your local machine:

- [ ] Using production API (not testnet)
- [ ] Verified symbol names are correct
- [ ] Using recent date range (last 30-90 days)
- [ ] API keys have correct permissions
- [ ] Not behind restrictive firewall/proxy
- [ ] Added debug logging to see what's happening
- [ ] Checked Delta Exchange documentation
- [ ] Tested with different batch sizes
- [ ] Added rate limit delays

---

## 🎯 Expected Results

**For 90 days of 15-minute data:**
```
90 days × 24 hours × 4 candles/hour = 8,640 candles per symbol
```

**For 30 days:**
```
30 days × 24 hours × 4 candles/hour = 2,880 candles per symbol
```

**For 7 days:**
```
7 days × 24 hours × 4 candles/hour = 672 candles per symbol
```

If you're getting close to these numbers, your data fetching is working correctly!

---

## 💡 Pro Tip

Start small and work your way up:

1. First, get 7 days of data working
2. Then try 30 days
3. Then try 90 days
4. Then try longer periods

This helps identify where the limit is.

---

## 🆘 Still Having Issues?

If you've tried everything and still can't get enough data:

**Option A**: Use a different data source
- Consider using Binance, Bybit, or other exchanges
- They often have better data availability

**Option B**: Use a data provider
- CryptoDataDownload
- CoinAPI
- CryptoCompare
- Kaiko

**Option C**: Accept limited data
- Adjust your backtest period
- Use 30-90 days instead of 1 year
- Still valuable for strategy validation

---

Remember: Even 30 days of data (2,880 candles) is usually enough to validate a strategy!
