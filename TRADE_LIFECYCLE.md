# 📊 Trade Lifecycle Tracking

Comprehensive guide to the new full trade lifecycle tracking system.

## Overview

Each trade is now tracked through its complete lifecycle: **PENDING → WIN/LOSS**, with detailed metadata including exit price, exit time, and calculated P&L.

---

## Trade Lifecycle Stages

```
Signal Generated
    ↓
Trade Created (PENDING status)
    ↓
Trade Saved to CSV
    ↓
[Every price update]
    ↓
Target/SL Reached?
    ├→ YES: Status → WIN/LOSS
    │        Exit Price/Time recorded
    │        P&L calculated
    │        CSV updated
    │        Alert sent
    │
    └→ NO: Status remains PENDING
```

---

## Trade Object Structure

Each trade contains:

```python
{
    'id': 'unique_trade_id',           # UUID: 20240413_120534_a1b2c3d4
    'timestamp': '2024-04-13T12:05:34', # Trade creation time
    'type': 'BUY',                      # BUY or SELL
    'entry': 45123.50,                  # Entry price
    'sl': 45100.00,                     # Stop loss
    'target': 45200.00,                 # Take profit target
    'status': 'PENDING',                # PENDING, WIN, or LOSS
    'exit_price': None,                 # Price where trade closed (NULL if pending)
    'exit_time': None,                  # Time of exit (NULL if pending)
    'pnl': None,                        # P&L in points (NULL if pending)
    'trend': 'UP',                      # Trend at entry
    'support': 45080.00,                # Support level
    'resistance': 45300.00              # Resistance level
}
```

---

## API Reference

### 1. `create_trade(signal: Dict) -> Dict`

Creates a complete trade object from a signal.

**Example:**
```python
from utils.trade_storage import create_trade

signal = {
    'type': 'BUY',
    'entry': 45123.50,
    'sl': 45100.00,
    'target': 45200.00,
    'trend': 'UP',
    'support': 45080.00,
    'resistance': 45300.00
}

trade = create_trade(signal)
# Returns: trade with id, timestamp, status='PENDING', exit fields=None
```

---

### 2. `update_trade_status(trade: Dict, current_price: float) -> Tuple[Dict, bool]`

Check if trade reached target or SL and update status.

**Logic:**
- **BUY:** WIN if price ≥ target, LOSS if price ≤ SL
- **SELL:** WIN if price ≤ target, LOSS if price ≥ SL

**Example:**
```python
from utils.trade_storage import update_trade_status

trade = {...}  # existing trade
current_price = 45210.00

updated_trade, status_changed = update_trade_status(trade, current_price)

if status_changed:
    print(f"Trade closed: {updated_trade['status']}")
    print(f"P&L: {updated_trade['pnl']} pts")
```

**Returns:**
- `updated_trade`: Trade dict with updated status/exit info
- `status_changed`: Boolean indicating if status was updated

---

### 3. `update_trades_with_price(trades: List[Dict], current_price: float) -> Tuple[List[Dict], Dict]`

Update all pending trades in a list with current price.

**Example:**
```python
from utils.trade_storage import update_trades_with_price

trades = [...]  # list of trades
current_price = 45210.00

updated_trades, stats = update_trades_with_price(trades, current_price)

print(f"Closed: {stats['closed_count']}")
print(f"Wins: {stats['win_count']}")
print(f"Losses: {stats['loss_count']}")
print(f"Total P&L: {stats['total_pnl']}")
```

**Returns stats:**
```python
{
    'closed_count': 2,      # Number of trades that closed
    'win_count': 1,         # Number of winning trades
    'loss_count': 1,        # Number of losing trades
    'total_pnl': 75.50      # Sum of all P&L
}
```

---

### 4. `save_trade(trade: Dict) -> bool`

Save trade to CSV file.

**Example:**
```python
from utils.trade_storage import save_trade

trade = create_trade(signal)
success = save_trade(trade)

if success:
    print(f"Trade {trade['id']} saved!")
```

---

### 5. `update_trade_in_csv(trade: Dict) -> bool`

Update an existing trade in the CSV file (when it closes).

**Example:**
```python
from utils.trade_storage import update_trade_in_csv

# Trade was updated with closing info
trade['status'] = 'WIN'
trade['exit_price'] = 45200.00
trade['exit_time'] = '2024-04-13T12:15:00'
trade['pnl'] = 76.50

success = update_trade_in_csv(trade)
```

---

### 6. `load_trades() -> List[Dict]`

Load all trades from CSV (both closed and pending).

**Example:**
```python
from utils.trade_storage import load_trades

all_trades = load_trades()
print(f"Total trades: {len(all_trades)}")
```

---

### 7. `load_pending_trades() -> List[Dict]`

Load only pending trades (status = PENDING).

**Example:**
```python
from utils.trade_storage import load_pending_trades

pending = load_pending_trades()
print(f"Pending trades: {len(pending)}")
```

---

### 8. `get_trade_stats(trades: List[Dict]) -> Dict`

Calculate statistics for a list of trades.

**Example:**
```python
from utils.trade_storage import get_trade_stats

stats = get_trade_stats(st.session_state.trades)

print(f"Total: {stats['total']}")
print(f"Closed: {stats['closed']}")
print(f"Win Rate: {stats['win_rate']}%")
print(f"Total P&L: {stats['total_pnl']} pts")
```

**Returns stats:**
```python
{
    'total': 10,           # Total trades
    'pending': 2,          # Pending trades
    'won': 6,              # Winning trades
    'lost': 2,             # Losing trades
    'closed': 8,           # Total closed
    'total_pnl': 150.75,   # Sum of all P&L
    'win_rate': 75.0       # Percentage
}
```

---

## CSV Format

Trades are stored in `~/.streamlit_trades/trades.csv` with these columns:

```
id,timestamp,type,entry,sl,target,status,exit_price,exit_time,pnl,trend,support,resistance
```

**Example row:**
```
20240413_120534_a1b2c3d4,2024-04-13T12:05:34,BUY,45123.50,45100.00,45200.00,WIN,45200.00,2024-04-13T12:15:00,76.50,UP,45080.00,45300.00
```

---

## Real-Time Usage in App.py

The main app automatically:

1. **Creates trades** when signals are generated
2. **Updates pending trades** on every price tick
3. **Closes trades** when target/SL is reached
4. **Updates CSV** when trades close
5. **Sends alerts** when trades close
6. **Calculates stats** for display

**Example flow:**
```python
# Every app.py refresh (every 10 seconds):

1. Fetch latest price
2. Check for new signals → create trades
3. Update all pending trades with new price
4. For closed trades:
   - Update status (WIN/LOSS)
   - Set exit_price and exit_time
   - Calculate P&L
   - Update CSV
   - Send Telegram alert
5. Display stats on dashboard
```

---

## Trade Matching Logic

### BUY Trades
```
Entry: 100
Target: 110
SL: 95

Price movement:
  95 → SL Hit → LOSS, exit @ 95
 100 → In progress → PENDING
 110 → Target Hit → WIN, exit @ 110
 115 → Price higher → Would be WIN (exit @ 110)
```

### SELL Trades
```
Entry: 100
Target: 90
SL: 105

Price movement:
  85 → Target Hit → WIN, exit @ 90
 100 → In progress → PENDING
 105 → SL Hit → LOSS, exit @ 105
  95 → In range → PENDING
```

---

## Performance Summary

The dashboard displays:

```
📊 Trade Statistics
─────────────────────
Total Trades: 25
Pending:      3
Won:          15
Lost:         7
Win Rate:     68.2%

Total P&L: +287.50 pts [Profit]
```

---

## Data Persistence

- **Local Development**: Stores in `~/.streamlit_trades/trades.csv`
- **Streamlit Cloud**: Stores in cloud filesystem (ephemeral during reruns, persistent between sessions)
- **Docker**: Stores in container's home directory
- **Network**: CSV file is human-readable for analysis

---

## Backward Compatibility

✅ **Existing CSV files** are automatically migrated:
- Old trades without ID/status get defaults
- Missing fields are populated
- New fields are added on next save

---

## Troubleshooting

### Trades not updating?
```python
# Check pending trades
from utils.trade_storage import load_pending_trades
pending = load_pending_trades()
print(f"Pending: {len(pending)}")
```

### CSV file not found?
```python
# Ensure data directory exists
from utils.trade_storage import ensure_data_dir
ensure_data_dir()
```

### Status not changing?
```python
# Check trade format
from utils.trade_storage import update_trade_status
trade, changed = update_trade_status(trade, current_price)
print(f"Status changed: {changed}")
print(f"New status: {trade['status']}")
```

---

## Examples

### Example 1: Manual trade tracking
```python
from utils.trade_storage import (
    create_trade, save_trade, update_trade_status,
    load_trades, get_trade_stats
)

# Create a trade
signal = {'type': 'BUY', 'entry': 100, 'sl': 95, 'target': 110}
trade = create_trade(signal)
save_trade(trade)

# Update it
current_price = 105
trade, changed = update_trade_status(trade, current_price)

# Query results
all_trades = load_trades()
stats = get_trade_stats(all_trades)
print(stats['win_rate'])
```

### Example 2: Batch update all trades
```python
from utils.trade_storage import update_trades_with_price, update_trade_in_csv

current_price = 45210.00
trades, stats = update_trades_with_price(trades, current_price)

# Update closed trades in CSV
for trade in trades:
    if trade['status'] != 'PENDING':
        update_trade_in_csv(trade)

print(f"Closed: {stats['closed_count']}, P&L: {stats['total_pnl']}")
```

---

## Summary

✅ Full trade lifecycle tracking
✅ Unique IDs for each trade
✅ Automatic status updates (PENDING → WIN/LOSS)
✅ Exit price and time recording
✅ P&L calculation
✅ CSV persistence
✅ Statistics and reporting
✅ Real-time dashboard display
✅ Backward compatible
✅ Clean, modular API
