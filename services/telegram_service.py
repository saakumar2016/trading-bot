import requests
from typing import Dict, Optional
from config import TELEGRAM_TOKEN, CHAT_ID
from utils.logger import get_logger

logger = get_logger(__name__)

# Track sent messages to prevent duplicates
_sent_messages = set()


def _add_sent_message(msg_hash: str) -> None:
    """Track a sent message hash to prevent duplicates."""
    _sent_messages.add(msg_hash)


def _is_sent(msg_hash: str) -> bool:
    """Check if message hash was already sent."""
    return msg_hash in _sent_messages


def send_telegram(msg: str) -> bool:
    """
    Send message via Telegram.
    
    Args:
        msg: Message to send
        
    Returns:
        True if successful, False otherwise
    """
    if not TELEGRAM_TOKEN or not CHAT_ID:
        logger.warning("Telegram credentials not configured")
        return False
        
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        response = requests.post(
            url, 
            data={"chat_id": CHAT_ID, "text": msg},
            timeout=5
        )
        
        if response.status_code == 200:
            logger.info(f"Telegram message sent successfully")
            return True
        else:
            logger.error(f"Telegram API error: {response.status_code}")
            return False
            
    except requests.exceptions.Timeout:
        logger.error("Telegram request timeout")
        return False
    except requests.exceptions.RequestException as e:
        logger.error(f"Telegram request failed: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error sending Telegram message: {str(e)}")
        return False


def format_signal_alert(signal: Dict) -> str:
    """
    Format a structured message for new trade signal.
    
    Args:
        signal: Signal dict with type, entry, sl, target, trend, support, resistance
        
    Returns:
        Formatted message string
        
    Example output:
        🚨 NEW SIGNAL
        ─────────────
        Type: BUY
        Entry: 45123.50
        SL: 45100.00
        Target: 45200.00
        Trend: UP
        Support: 45080.00
        Resistance: 45300.00
    """
    trade_type = signal.get("type", "UNKNOWN")
    entry = signal.get("entry", 0)
    sl = signal.get("sl", 0)
    target = signal.get("target", 0)
    trend = signal.get("trend", "UNKNOWN")
    support = signal.get("support", 0)
    resistance = signal.get("resistance", 0)
    
    msg = f"""🚨 NEW SIGNAL
─────────────
Type: {trade_type}
Entry: {entry:.2f}
SL: {sl:.2f}
Target: {target:.2f}
Trend: {trend}
Support: {support:.2f}
Resistance: {resistance:.2f}"""
    
    return msg


def format_win_alert(trade: Dict) -> str:
    """
    Format a structured message for target hit (WIN).
    
    Args:
        trade: Trade dict with id, type, entry, sl, target, exit_price, pnl
        
    Returns:
        Formatted message string
        
    Example output:
        ✅ TARGET HIT - WIN
        ─────────────────
        ID: 20240413_120534_a1b2c3d4
        Type: BUY
        Entry: 45123.50
        SL: 45100.00
        Target: 45200.00
        Exit: 45200.00
        P&L: +76.50 pts
    """
    trade_id = trade.get("id", "UNKNOWN")
    trade_type = trade.get("type", "UNKNOWN")
    entry = trade.get("entry", 0)
    sl = trade.get("sl", 0)
    target = trade.get("target", 0)
    exit_price = trade.get("exit_price", 0)
    pnl = trade.get("pnl", 0)
    
    msg = f"""✅ TARGET HIT - WIN
─────────────────
ID: {trade_id}
Type: {trade_type}
Entry: {entry:.2f}
SL: {sl:.2f}
Target: {target:.2f}
Exit: {exit_price:.2f}
P&L: +{pnl:.2f} pts"""
    
    return msg


def format_loss_alert(trade: Dict) -> str:
    """
    Format a structured message for stop loss hit (LOSS).
    
    Args:
        trade: Trade dict with id, type, entry, sl, target, exit_price, pnl
        
    Returns:
        Formatted message string
        
    Example output:
        ❌ STOP LOSS - LOSS
        ───────────────────
        ID: 20240413_120534_a1b2c3d4
        Type: BUY
        Entry: 45123.50
        SL: 45100.00
        Target: 45200.00
        Exit: 45100.00
        P&L: -23.50 pts
    """
    trade_id = trade.get("id", "UNKNOWN")
    trade_type = trade.get("type", "UNKNOWN")
    entry = trade.get("entry", 0)
    sl = trade.get("sl", 0)
    target = trade.get("target", 0)
    exit_price = trade.get("exit_price", 0)
    pnl = trade.get("pnl", 0)
    
    msg = f"""❌ STOP LOSS - LOSS
───────────────────
ID: {trade_id}
Type: {trade_type}
Entry: {entry:.2f}
SL: {sl:.2f}
Target: {target:.2f}
Exit: {exit_price:.2f}
P&L: {pnl:.2f} pts"""
    
    return msg


def send_signal_alert(signal: Dict) -> bool:
    """
    Send alert for new trade signal.
    
    Args:
        signal: Signal dict with all trade details
        
    Returns:
        True if sent successfully, False otherwise
    """
    msg = format_signal_alert(signal)
    msg_hash = hash(f"signal_{signal.get('type')}_{signal.get('entry')}")
    
    if _is_sent(msg_hash):
        logger.debug("Signal alert already sent (duplicate prevention)")
        return False
    
    success = send_telegram(msg)
    if success:
        _add_sent_message(msg_hash)
    
    return success


def send_win_alert(trade: Dict) -> bool:
    """
    Send alert for target hit (WIN).
    
    Args:
        trade: Trade dict with all details
        
    Returns:
        True if sent successfully, False otherwise
    """
    trade_id = trade.get("id")
    if not trade_id:
        logger.warning("Cannot send win alert: trade ID missing")
        return False
    
    msg = format_win_alert(trade)
    msg_hash = hash(f"win_{trade_id}")
    
    if _is_sent(msg_hash):
        logger.debug(f"Win alert already sent: {trade_id} (duplicate prevention)")
        return False
    
    success = send_telegram(msg)
    if success:
        _add_sent_message(msg_hash)
    
    return success


def send_loss_alert(trade: Dict) -> bool:
    """
    Send alert for stop loss hit (LOSS).
    
    Args:
        trade: Trade dict with all details
        
    Returns:
        True if sent successfully, False otherwise
    """
    trade_id = trade.get("id")
    if not trade_id:
        logger.warning("Cannot send loss alert: trade ID missing")
        return False
    
    msg = format_loss_alert(trade)
    msg_hash = hash(f"loss_{trade_id}")
    
    if _is_sent(msg_hash):
        logger.debug(f"Loss alert already sent: {trade_id} (duplicate prevention)")
        return False
    
    success = send_telegram(msg)
    if success:
        _add_sent_message(msg_hash)
    
    return success