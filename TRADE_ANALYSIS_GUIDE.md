# Trade Analysis Framework

Your system now includes automated trade analysis that identifies patterns, detects issues, and suggests improvements.

## How It Works

### 1. **Automatic Analysis**  
- Every time you run the bot, trades are automatically saved to `~/.streamlit_trades/trades.csv`
- Analysis dashboard processes closed trades (WIN, LOSS, TIMEOUT)
- Generates insights on performance, patterns, and improvements

### 2. **Access Analysis Dashboard**
```
Streamlit UI → Pages → 4_Analysis
```

Or programmatically:
```python
from utils.trade_analysis import TradeAnalyzer

analyzer = TradeAnalyzer()
if analyzer.load_trades():
    report = analyzer.generate_report()
    print(report)
```

## What Gets Analyzed

### Overall Metrics
- **Win Rate**: % of closed trades that hit target
- **Total P&L**: Sum of all trade profits and losses
- **Avg Win/Loss**: Average profit per win vs average loss per loss
- **Win/Loss Ratio**: Expected value indicator

### By Trade Type
- **BUY Performance**: Separate stats for long trades
- **SELL Performance**: Separate stats for short trades
- Helps identify if one direction is consistently better/worse

### By Trend
- **UP Trend**: Performance when trend indicator shows uptrend
- **DOWN Trend**: Performance when trend shows downtrend
- **SIDEWAYS**: Performance in consolidation/ranging markets
- Reveals if strategy works better in specific market conditions

### Risk/Reward Analysis
- **Avg R/R Ratio**: How much reward per unit of risk
- **Profitable High-RR Trades**: Wins where risk/reward >= 1.5x
- **Losing Low-RR Trades**: Losses where risk/reward < 1.2x

## Pattern Detection

### ❌ Failure Patterns (Why Trades Lose)

**WRONG_TREND**
- SELL signals in UP trend or BUY in DOWN
- Root Cause: Trend filter not strict enough
- Fix: Only trade with trend direction

**BAD_RR**
- Risk > Reward (unfavorable setup)
- Root Cause: Targets too small, SL too wide
- Fix: Expand targets, tighten stop-loss

**QUICK_LOSS**
- Hit stop loss immediately (>15 point loss)
- Root Cause: Whipsaws from being too close to level
- Fix: Reduce SL_BUFFER, increase WICK_RATIO filter

**TIMEOUT_LOSS**
- Trade still open after 30 minutes (closed as TIMEOUT)
- Root Cause: Trend changed, trade stuck at support
- Fix: Reduce TRADES_TIMEOUT_MINUTES, close at breakeven

### ✅ Win Patterns (Why Trades Win)

**STRONG_TREND**
- BUY in UP or SELL in DOWN
- Shows: Trading with momentum is profitable
- Action: Protect this - don't weaken trend filter

**HIGH_RR**
- Risk/Reward >= 1.5x with win
- Shows: High conviction setups pay off
- Action: Prioritize high-RR opportunities

**QUICK_WIN**
- Hit target fast (>10 point profit)
- Shows: Momentum plays work
- Action: Consider earlier exits at partial targets

**SUPPORT_BOUNCES**
- BUY trades near support work well
- Shows: Level relevance is high
- Action: Strengthen support/resistance detection

## Suggested Improvements

The system automatically generates prioritized improvement suggestions based on your data:

### Priority Levels
- **HIGH**: Directly impacts win rate or P&L
- **MEDIUM**: Improves efficiency or reduces whipsaws
- **LOW**: Fine-tuning after core issues resolved

### Example Issues & Fixes

| Issue | Detection | Fix |
|-------|-----------|-----|
| Low Win Rate (<50%) | Overall win_rate metric | Tighten entry filters, require stronger wicks |
| Asymmetric Payoff | avg_win < avg_loss | Increase target %, reduce SL buffer |
| Wrong Trend Entries | WRONG_TREND pattern | Enforce trend direction, disable conflicting signals |
| Quick Stops | QUICK_LOSS pattern high | Reduce SL_BUFFER, increase WICK_RATIO |
| Stuck Trades | TIMEOUT_LOSS pattern | Reduce timeout duration, close at breakeven |
| Type Imbalance | One trade type underperforms | Review entry logic for weak type, disable temporarily |

## How to Use Results

### Step 1: Run Enough Trades
- Collect minimum 20-30 closed trades for statistically significant analysis
- Analysis becomes more reliable with more data

### Step 2: Review Dashboard
- Check "Improvement Suggestions" first (sorted by impact)
- Note which patterns account for most losses

### Step 3: Identify Root Cause
- Pick ONE issue to fix (usually the highest impact)
- Understand why it's happening in the code

### Step 4: Implement Fix
Example fixes for common issues:

**Fix #1: Low Win Rate from Wrong Trend Entries**
```python
# In core/strategy.py
# Make trend filter more strict - ONLY trade TREND direction
# Change from: trend in ["UP", "SIDEWAYS"] allows buys
# Change to: trend in ["UP"] only, require pure uptrend
```

**Fix #2: Asymmetric Payoff from Small Targets**
```python
# In core/strategy.py
# Increase target percentage
# Change: raw_target = round(entry + (range_size * 0.3), 2)
# To:     raw_target = round(entry + (range_size * 0.4), 2)
```

**Fix #3: Quick Losses from Wide Stop-Loss**
```python
# In core/strategy.py
# Reduce SL_BUFFER
# Change: SL_BUFFER = 10
# To:     SL_BUFFER = 5
```

### Step 5: Run Again & Compare
- After fix, run bot for another 20-30 trades
- Generate fresh report
- Compare metrics to baseline

## Key Metrics to Track

After each improvement cycle, track these KPIs:

```
Baseline:  [Initial values]
After Fix #1: [Compare improvement]
After Fix #2: [Continue improving]

Target:
- Win Rate: 55-60%
- Avg Win/Loss Ratio: 1.3-1.5x
- Total P&L: Positive
- Quick Losses: <10% of trades
```

## When to Make Changes

✅ **Make changes when:**
- You have 20+ closed trades
- One pattern accounts for >20% of losses
- Dashboard suggests specific fix with high impact

❌ **Don't change when:**
- Less than 10 closed trades (not enough data)
- All metrics healthy (>55% win rate, positive P&L)
- Multiple issues detected (fix one at a time)

## Anatomy of Trade Fields

Each trade record contains:
- `id`: Unique trade identifier  
- `timestamp`: Entry time
- `type`: BUY or SELL
- `entry`: Entry price
- `sl`: Stop-loss price
- `target`: Target/Exit price
- `status`: WIN/LOSS/TIMEOUT
- `exit_price`: Actual exit price
- `exit_time`: Exit time
- `pnl`: Profit/Loss in points
- `trend`: Market trend at entry
- `support`/`resistance`: Pre-calculated levels

## Automation

To run analysis programmatically after each trading session:

```python
from utils.trade_analysis import analyze_trades_and_print

report = analyze_trades_and_print()
print(report)

# Or store to file
with open("trade_analysis_report.txt", "w") as f:
    f.write(report)
```

## Troubleshooting

**"No trades found" error**
- Wait for at least one signal to generate
- Check: `ls -la ~/.streamlit_trades/trades.csv`

**"No closed trades" error**
- Trades need to complete (hit target or SL)
- With 30min timeout, wait up to 30 minutes

**Analysis shows no issues but P&L negative**
- Win rate may be healthy but avg_loss > avg_win
- Focus on R/R ratio improvement
- Or win rate not sustainable (need > 60% for negative RR)

---

**Next Steps**: Run the bot, generate 20-30 trades, check the Analysis dashboard for improvement suggestions.
