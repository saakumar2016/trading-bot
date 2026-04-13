import csv
import os
import uuid
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from utils.logger import get_logger

logger = get_logger(__name__)

TRADES_FILE = os.path.expanduser("~/.streamlit_trades/trades.csv")
TRADES_MEMORY_FILE = os.path.expanduser("~/.streamlit_trades/trades_open.json")

# Trade status constants
STATUS_PENDING = "PENDING"
STATUS_WIN = "WIN"
STATUS_LOSS = "LOSS"

# CSV fieldnames - includes new fields for lifecycle tracking
CSV_FIELDNAMES = [
    'id', 'timestamp', 'type', 'entry', 'sl', 'target',
    'status', 'exit_price', 'exit_time',
    'pnl', 'trend', 'support', 'resistance'
]


def ensure_data_dir() -> None:
    """Create data directory if it doesn't exist."""
    os.makedirs(os.path.dirname(TRADES_FILE), exist_ok=True)


def generate_trade_id() -> str:
    """
    Generate unique trade ID.
    
    Returns:
        Unique ID combining timestamp and UUID
    """
    return f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{str(uuid.uuid4())[:8]}"


def create_trade(signal: Dict) -> Dict:
    """
    Create a complete trade object from a signal.
    
    Args:
        signal: Signal dictionary with entry, sl, target, type, etc.
        
    Returns:
        Trade dictionary with all lifecycle fields
    """
    trade = {
        'id': generate_trade_id(),
        'timestamp': datetime.now().isoformat(),
        'type': signal.get('type', 'UNKNOWN'),
        'entry': signal.get('entry', 0),
        'sl': signal.get('sl', 0),
        'target': signal.get('target', 0),
        'status': STATUS_PENDING,
        'exit_price': None,
        'exit_time': None,
        'pnl': None,
        'trend': signal.get('trend', ''),
        'support': signal.get('support', 0),
        'resistance': signal.get('resistance', 0),
    }
    logger.debug(f"Trade created: {trade['id']} - {trade['type']} @ {trade['entry']}")
    return trade


def calculate_pnl(trade: Dict) -> Optional[float]:
    """
    Calculate profit/loss for a trade.
    
    Args:
        trade: Trade dictionary
        
    Returns:
        P&L in points, or None if trade incomplete
    """
    if not trade.get('exit_price'):
        return None
    
    try:
        entry = float(trade['entry'])
        exit_price = float(trade['exit_price'])
        trade_type = trade.get('type', '')
        
        if trade_type == 'BUY':
            return round(exit_price - entry, 2)
        elif trade_type == 'SELL':
            return round(entry - exit_price, 2)
        else:
            return None
    except (ValueError, TypeError):
        return None


def update_trade_status(trade: Dict, current_price: float) -> Tuple[Dict, bool]:
    """
    Update trade status based on current price.
    
    Checks if trade reached target (WIN) or stop loss (LOSS).
    
    Args:
        trade: Trade dictionary to update
        current_price: Current market price
        
    Returns:
        Tuple of (updated_trade, status_changed)
        
    Logic:
        BUY:
            - if price >= target → WIN
            - if price <= sl → LOSS
        SELL:
            - if price <= target → WIN
            - if price >= sl → LOSS
    """
    if trade.get('status') != STATUS_PENDING:
        return trade, False
    
    trade_type = trade.get('type', '')
    entry = float(trade.get('entry', 0))
    sl = float(trade.get('sl', 0))
    target = float(trade.get('target', 0))
    
    status_changed = False
    
    try:
        if trade_type == 'BUY':
            # BUY: profit if price rises to target, loss if falls to SL
            if current_price >= target:
                trade['status'] = STATUS_WIN
                trade['exit_price'] = target
                trade['exit_time'] = datetime.now().isoformat()
                status_changed = True
                logger.info(f"Trade {trade['id']}: BUY reached target {target}")
                
            elif current_price <= sl:
                trade['status'] = STATUS_LOSS
                trade['exit_price'] = sl
                trade['exit_time'] = datetime.now().isoformat()
                status_changed = True
                logger.info(f"Trade {trade['id']}: BUY hit SL {sl}")
        
        elif trade_type == 'SELL':
            # SELL: profit if price falls to target, loss if rises to SL
            if current_price <= target:
                trade['status'] = STATUS_WIN
                trade['exit_price'] = target
                trade['exit_time'] = datetime.now().isoformat()
                status_changed = True
                logger.info(f"Trade {trade['id']}: SELL reached target {target}")
                
            elif current_price >= sl:
                trade['status'] = STATUS_LOSS
                trade['exit_price'] = sl
                trade['exit_time'] = datetime.now().isoformat()
                status_changed = True
                logger.info(f"Trade {trade['id']}: SELL hit SL {sl}")
        
        # Calculate P&L if status changed
        if status_changed:
            trade['pnl'] = calculate_pnl(trade)
        
    except (ValueError, TypeError) as e:
        logger.error(f"Error updating trade status: {str(e)}")
    
    return trade, status_changed


def update_trades_with_price(trades: List[Dict], current_price: float) -> Tuple[List[Dict], Dict]:
    """
    Update all pending trades with current price.
    
    Args:
        trades: List of trade dictionaries
        current_price: Current market price
        
    Returns:
        Tuple of (updated_trades, stats_dict with closed_count and pnl_total)
    """
    stats = {
        'closed_count': 0,
        'win_count': 0,
        'loss_count': 0,
        'total_pnl': 0.0
    }
    
    for trade in trades:
        updated_trade, changed = update_trade_status(trade, current_price)
        if changed:
            stats['closed_count'] += 1
            if updated_trade['status'] == STATUS_WIN:
                stats['win_count'] += 1
            elif updated_trade['status'] == STATUS_LOSS:
                stats['loss_count'] += 1
            
            if updated_trade.get('pnl'):
                stats['total_pnl'] += updated_trade['pnl']
    
    return trades, stats


def save_trade(trade: Dict) -> bool:
    """
    Save trade to CSV file.
    
    Args:
        trade: Trade dictionary
        
    Returns:
        True if successful
    """
    try:
        ensure_data_dir()
        
        file_exists = os.path.exists(TRADES_FILE)
        
        with open(TRADES_FILE, 'a', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=CSV_FIELDNAMES, extrasaction='ignore')
            
            if not file_exists:
                writer.writeheader()
            
            # Prepare row - only include fields in CSV_FIELDNAMES
            row = {field: trade.get(field, '') for field in CSV_FIELDNAMES}
            writer.writerow(row)
        
        logger.info(f"Trade saved: {trade['id']} - {trade['type']} @ {trade['entry']}")
        return True
        
    except Exception as e:
        logger.error(f"Error saving trade: {str(e)}")
        return False


def update_trade_in_csv(trade: Dict) -> bool:
    """
    Update an existing trade in the CSV file.
    
    Args:
        trade: Trade dictionary with updated status/exit info
        
    Returns:
        True if successful
    """
    try:
        if not os.path.exists(TRADES_FILE):
            return False
        
        # Read all trades
        trades = []
        with open(TRADES_FILE, 'r') as f:
            reader = csv.DictReader(f)
            trades = list(reader)
        
        # Update the trade
        for i, t in enumerate(trades):
            if t.get('id') == trade.get('id'):
                # Update with new values
                for field in CSV_FIELDNAMES:
                    t[field] = trade.get(field, t.get(field, ''))
                break
        
        # Write back all trades
        with open(TRADES_FILE, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=CSV_FIELDNAMES)
            writer.writeheader()
            for t in trades:
                row = {field: t.get(field, '') for field in CSV_FIELDNAMES}
                writer.writerow(row)
        
        logger.debug(f"Trade updated in CSV: {trade['id']}")
        return True
        
    except Exception as e:
        logger.error(f"Error updating trade in CSV: {str(e)}")
        return False


def load_trades() -> List[Dict]:
    """
    Load all trades from CSV file.
    
    Returns:
        List of trade dictionaries
    """
    try:
        if not os.path.exists(TRADES_FILE):
            return []
        
        trades = []
        with open(TRADES_FILE, 'r') as f:
            reader = csv.DictReader(f)
            trades = list(reader)
        
        logger.info(f"Loaded {len(trades)} trades from file")
        return trades
        
    except Exception as e:
        logger.error(f"Error loading trades: {str(e)}")
        return []


def load_pending_trades() -> List[Dict]:
    """
    Load only pending trades from CSV file.
    
    Returns:
        List of pending trade dictionaries
    """
    trades = load_trades()
    pending = [t for t in trades if t.get('status') == STATUS_PENDING]
    logger.debug(f"Loaded {len(pending)} pending trades")
    return pending


def get_trade_stats(trades: List[Dict]) -> Dict:
    """
    Calculate statistics for trades.
    
    Args:
        trades: List of trade dictionaries
        
    Returns:
        Dictionary with stats: total, pending, won, lost, total_pnl, win_rate
    """
    total = len(trades)
    pending = sum(1 for t in trades if t.get('status') == STATUS_PENDING)
    won = sum(1 for t in trades if t.get('status') == STATUS_WIN)
    lost = sum(1 for t in trades if t.get('status') == STATUS_LOSS)
    
    total_pnl = 0.0
    closed = won + lost
    
    for trade in trades:
        if trade.get('pnl'):
            try:
                total_pnl += float(trade['pnl'])
            except (ValueError, TypeError):
                pass
    
    win_rate = (won / closed * 100) if closed > 0 else 0
    
    return {
        'total': total,
        'pending': pending,
        'won': won,
        'lost': lost,
        'closed': closed,
        'total_pnl': round(total_pnl, 2),
        'win_rate': round(win_rate, 2)
    }
