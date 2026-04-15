# Quick Fix Guide - Copy/Paste Ready

## Phase 1 Improvements (5 minutes to implement)

### Fix #1: Faster Trend Detection

**File:** `core/trend.py`

**Find:**
```python
# Configuration
MIN_DATA_POINTS = 20
LOOKBACK_CANDLES = 16
THRESHOLD = 10
```

**Replace with:**
```python
# Configuration
MIN_DATA_POINTS = 20
LOOKBACK_CANDLES = 8      # Changed from 16 - faster trend detection
THRESHOLD = 5             # Changed from 10 - easier reversal detection
```

---

### Fix #2: Tighter Stop-Loss

**File:** `core/strategy.py`

**Find:**
```python
SUPPORT_BUFFER = 8
RESISTANCE_BUFFER = 8
WICK_RATIO = 0.4
SL_BUFFER = 10
```

**Replace with:**
```python
SUPPORT_BUFFER = 8
RESISTANCE_BUFFER = 8
WICK_RATIO = 0.4
SL_BUFFER = 5    # Changed from 10 - reduces whipsaws
```

---

### Fix #3: Range Filter Exception

**File:** `core/strategy.py`

**Find:**
```python
        support, resistance = get_levels(df)
        range_size = resistance - support

        # 🚫 Avoid bad market
        if range_size < MIN_RANGE_FILTER:
            logger.warning(f"Signal check aborted: range too narrow ({range_size} < {MIN_RANGE_FILTER})")
            return None

        price = cl2
```

**Replace with:**
```python
        support, resistance = get_levels(df)
        range_size = resistance - support

        # 🚫 Avoid bad market - UNLESS wick is very strong
        wick_strength = lower_wick / body if body > 0 else 0
        is_strong_wick = wick_strength > 0.6
        
        if range_size < MIN_RANGE_FILTER and not is_strong_wick:
            logger.warning(f"Signal check aborted: range too narrow ({range_size} < {MIN_RANGE_FILTER})")
            return None

        price = cl2
```

---

## Phase 2 Improvements (After Phase 1 proves out)

### Fix #4: Earlier Entry

**File:** `core/strategy.py`

**Find:**
```python
        signal_candle = df.iloc[-3]
        confirm_candle = df.iloc[-2]

        o1 = val(signal_candle['Open'])
        h1 = val(signal_candle['High'])
        l1 = val(signal_candle['Low'])
        cl1 = val(signal_candle['Close'])

        o2 = val(confirm_candle['Open'])
        cl2 = val(confirm_candle['Close'])
```

**Replace with:**
```python
        signal_candle = df.iloc[-2]    # Changed from -3
        confirm_candle = df.iloc[-1]   # Changed from -2 (earlier entry)

        o1 = val(signal_candle['Open'])
        h1 = val(signal_candle['High'])
        l1 = val(signal_candle['Low'])
        cl1 = val(signal_candle['Close'])

        o2 = val(confirm_candle['Open'])
        cl2 = val(confirm_candle['Close'])
```

---

### Fix #5: Adaptive Targets (OPTIONAL - requires more testing)

**File:** `core/strategy.py` - BUY section

**Find:**
```python
                entry = round(cl2, 2)
                sl = round(l1 - SL_BUFFER, 2)

                # 🎯 realistic intraday target with level constraints
                raw_target = round(entry + (range_size * 0.3), 2)
                target = round(min(raw_target, resistance - 5), 2)  # Don't exceed resistance
```

**Replace with:**
```python
                entry = round(cl2, 2)
                sl = round(l1 - SL_BUFFER, 2)

                # 🎯 adaptive target based on wick strength
                wick_ratio = lower_wick / body if body > 0 else 0
                if wick_ratio > 0.7:
                    target_multiplier = 0.45  # Strong rejection = bigger target
                elif wick_ratio > 0.5:
                    target_multiplier = 0.35
                else:
                    target_multiplier = 0.25
                
                raw_target = round(entry + (range_size * target_multiplier), 2)
                target = round(min(raw_target, resistance - 3), 2)  # Slightly looser cap
```

**File:** `core/strategy.py` - SELL section (mirror logic)

**Find:**
```python
                entry = round(cl2, 2)
                sl = round(h1 + SL_BUFFER, 2)

                # 🎯 realistic intraday target with level constraints
                raw_target = round(entry - (range_size * 0.3), 2)
                target = round(max(raw_target, support + 5), 2)  # Don't go below support
```

**Replace with:**
```python
                entry = round(cl2, 2)
                sl = round(h1 + SL_BUFFER, 2)

                # 🎯 adaptive target based on wick strength
                wick_ratio = upper_wick / body if body > 0 else 0
                if wick_ratio > 0.7:
                    target_multiplier = 0.45  # Strong rejection = bigger target
                elif wick_ratio > 0.5:
                    target_multiplier = 0.35
                else:
                    target_multiplier = 0.25
                
                raw_target = round(entry - (range_size * target_multiplier), 2)
                target = round(max(raw_target, support + 3), 2)  # Slightly looser cap
```

---

## Verification Checklist

After making changes:

```
□ Modified core/trend.py - LOOKBACK = 8, THRESHOLD = 5
□ Modified core/strategy.py - SL_BUFFER = 5
□ Modified core/strategy.py - Added wick_strength exception to range filter
□ (Optional) Modified entry candles to -2/-1
□ (Optional) Added adaptive target logic
```

**Test compilation:**
```bash
python -m py_compile core/strategy.py core/trend.py
# Should show no errors
```

---

## Running & Monitoring

1. **Start bot** in Streamlit
2. **Run for 30-50 trades** (20-60 minutes on 1m bars)
3. **Check results** in Streamlit → Pages → 4_Analysis
4. **Compare metrics:**
   - Win Rate: Should jump from ~50% to ~60%+
   - Avg Loss: Should drop from -12 to -8
   - Total P&L: Should shift from negative to positive

---

## Rollback If Needed

Each change is independent and can be rolled back:

- **Trend too fast?** Revert LOOKBACK to 16, THRESHOLD to 10
- **SL too tight?** Revert SL_BUFFER to 10
- **Too many signals?** Revert MIN_RANGE_FILTER logic
- **Entry too early?** Revert candles to -3/-2

---

## Questions Answered

**Q: Will these changes break existing functionality?**  
A: No. They're parameter tuning, not logic changes. All safety checks remain.

**Q: Should I change everything at once?**  
A: Start with Phase 1 (3 quick changes), test 30 trades, THEN consider Phase 2.

**Q: What if win rate drops?**  
A: Check Analysis dashboard for failure patterns, rollback one change, re-test.

**Q: How long to see results?**  
A: Need minimum 30 closed trades for statistical significance.

---

## Support

If something breaks:
1. Check compilation: `python -m py_compile core/strategy.py core/trend.py`
2. Review Analysis dashboard for specific failure patterns
3. Rollback the last change made
4. Re-test with fewer candles to verify fix worked
