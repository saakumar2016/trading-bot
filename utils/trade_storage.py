import csv
import os
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from utils.logger import get_logger

logger = get_logger(__name__)

TRADES_FILE = os.path.expanduser("~/.streamlit_trades/trades.csv")
TRADES_TIMEOUT_MINUTES = 30

STATUS_PENDING = "PENDING"
STATUS_WIN = "WIN"
STATUS_LOSS = "LOSS"
STATUS_TIMEOUT = "TIMEOUT"

CSV_FIELDNAMES = [
    'id', 'timestamp', 'type', 'entry', 'sl', 'target',
    'status', 'exit_price', 'exit_time',
    'pnl', 'trend', 'support', 'resistance'
]


def ensure_data_dir() -> None:
    os.makedirs(os.path.dirname(TRADES_FILE), exist_ok=True)


def generate_trade_id() -> str:
    return f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{str(uuid.uuid4())[:8]}"


def create_trade(signal: Dict) -> Dict:
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


def _check_trade_timeout(trade: Dict, current_price: float) -> Tuple[Dict, bool]:
    """Check if trade exceeded timeout duration."""
    if trade.get('status') != STATUS_PENDING:
        return trade, False
    
    try:
        timestamp_str = trade.get('timestamp', '')
        trade_time = datetime.fromisoformat(timestamp_str)
        now = datetime.now()
        elapsed = now - trade_time
        
        if elapsed > timedelta(minutes=TRADES_TIMEOUT_MINUTES):
            trade['status'] = STATUS_TIMEOUT
            trade['exit_price'] = current_price
            trade['exit_time'] = now.isoformat()
            trade['pnl'] = calculate_pnl(trade)
            logger.info(f"Trade {trade['id']}: TIMEOUT after {TRADES_TIMEOUT_MINUTES}m at {current_price}")
            return trade, True
    except Exception as e:
        logger.error(f"Error checking timeout: {str(e)}")
    
    return trade, False


def _update_trade_status(trade: Dict, current_price: float) -> Tuple[Dict, bool]:
    if trade.get('status') != STATUS_PENDING:
        return trade, False

    trade_type = trade.get('type', '')
    
    try:
        sl = float(trade.get('sl', 0))
        target = float(trade.get('target', 0))
    except (ValueError, TypeError):
        return trade, False

    status_changed = False

    try:
        if trade_type == 'BUY':
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

        if status_changed:
            trade['pnl'] = calculate_pnl(trade)

    except (ValueError, TypeError) as e:
        logger.error(f"Error updating trade status: {str(e)}")

    return trade, status_changed


def update_trade_status(trades: List[Dict], current_price: float) -> Tuple[List[Dict], Dict]:
    stats = {
        'closed_count': 0,
        'win_count': 0,
        'loss_count': 0,
        'timeout_count': 0,
        'total_pnl': 0.0
    }

    for trade in trades:
        if trade.get('status') == STATUS_PENDING:
            _, timeout_hit = _check_trade_timeout(trade, current_price)
            if timeout_hit:
                stats['closed_count'] += 1
                stats['timeout_count'] += 1
                if trade.get('pnl'):
                    stats['total_pnl'] += trade['pnl']
            else:
                _, changed = _update_trade_status(trade, current_price)
                if changed:
                    stats['closed_count'] += 1
                    if trade['status'] == STATUS_WIN:
                        stats['win_count'] += 1
                    elif trade['status'] == STATUS_LOSS:
                        stats['loss_count'] += 1
                    if trade.get('pnl') is not None:
                        stats['total_pnl'] += trade['pnl']

    return trades, stats


update_trades_with_price = update_trade_status


def has_active_trade(trades: List[Dict]) -> bool:
    """Check if there's any active PENDING trade."""
    return any(trade.get('status') == STATUS_PENDING for trade in trades)


def save_trade(trade: Dict) -> bool:
    try:
        ensure_data_dir()
        
        file_exists = os.path.exists(TRADES_FILE)
        
        with open(TRADES_FILE, 'a', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=CSV_FIELDNAMES, extrasaction='ignore')
            
            if not file_exists:
                writer.writeheader()
            
            row = {field: trade.get(field, '') for field in CSV_FIELDNAMES}
            writer.writerow(row)
        
        logger.info(f"Trade saved: {trade['id']} - {trade['type']} @ {trade['entry']}")
        return True
        
    except Exception as e:
        logger.error(f"Error saving trade: {str(e)}")
        return False


def update_trade_in_csv(trade: Dict) -> bool:
    try:
        if not os.path.exists(TRADES_FILE):
            return False
        
        trades = []
        with open(TRADES_FILE, 'r') as f:
            reader = csv.DictReader(f)
            trades = list(reader)
        
        for i, t in enumerate(trades):
            if t.get('id') == trade.get('id'):
                for field in CSV_FIELDNAMES:
                    t[field] = trade.get(field, t.get(field, ''))
                break
        
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
    trades = load_trades()
    pending = [t for t in trades if t.get('status') == STATUS_PENDING]
    logger.debug(f"Loaded {len(pending)} pending trades")
    return pending


def get_trade_stats(trades: List[Dict]) -> Dict:
    total = len(trades)
    pending = sum(1 for t in trades if t.get('status') == STATUS_PENDING)
    won = sum(1 for t in trades if t.get('status') == STATUS_WIN)
    lost = sum(1 for t in trades if t.get('status') == STATUS_LOSS)
    timeout = sum(1 for t in trades if t.get('status') == STATUS_TIMEOUT)
    
    total_pnl = 0.0
    closed = won + lost + timeout
    
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
        'timeout': timeout,
        'closed': closed,
        'total_pnl': round(total_pnl, 2),
        'win_rate': round(win_rate, 2)
    }
