import requests
from typing import Dict, Optional
from config import TELEGRAM_TOKEN, CHAT_ID
from utils.logger import get_logger

logger = get_logger(__name__)

_sent_messages = set()


def _add_sent_message(msg_hash: str) -> None:
    """Track a sent message to prevent duplicates."""
    _sent_messages.add(msg_hash)


def _is_sent(msg_hash: str) -> bool:
    """Check if message was already sent."""
    return msg_hash in _sent_messages


def send_telegram(msg: str) -> bool:
    """
    Send message via Telegram.
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
            logger.info("Telegram message sent")
            return True
        else:
            logger.error(f"Telegram error: {response.status_code}")
            return False
            
    except Exception as e:
        logger.error(f"Telegram failed: {str(e)}")
        return False


def format_signal_alert(signal: Dict) -> str:
    """
    Format new signal alert.
    """
    return (
        f"🚨 NEW SIGNAL\n"
        f"ID: {signal.get('id', 'N/A')}\n"
        f"Type: {signal.get('type', 'N/A')}\n"
        f"Entry: {signal.get('entry', 0):.2f}\n"
        f"SL: {signal.get('sl', 0):.2f}\n"
        f"Target: {signal.get('target', 0):.2f}"
    )


def format_win_alert(trade: Dict) -> str:
    """
    Format WIN alert.
    """
    return (
        f"✅ TARGET HIT - WIN\n"
        f"ID: {trade.get('id', 'N/A')}\n"
        f"Type: {trade.get('type', 'N/A')}\n"
        f"Entry: {trade.get('entry', 0):.2f}\n"
        f"Exit: {trade.get('exit_price', 0):.2f}\n"
        f"P&L: +{trade.get('pnl', 0):.2f}"
    )


def format_loss_alert(trade: Dict) -> str:
    """
    Format LOSS alert.
    """
    return (
        f"❌ STOP LOSS - LOSS\n"
        f"ID: {trade.get('id', 'N/A')}\n"
        f"Type: {trade.get('type', 'N/A')}\n"
        f"Entry: {trade.get('entry', 0):.2f}\n"
        f"Exit: {trade.get('exit_price', 0):.2f}\n"
        f"P&L: {trade.get('pnl', 0):.2f}"
    )


def send_signal_alert(signal: Dict) -> bool:
    """
    Send signal alert.
    """
    trade_id = signal.get("id", "")
    msg_hash = hash(f"signal_{trade_id}")

    if _is_sent(msg_hash):
        logger.debug("Signal alert already sent")
        return False

    success = send_telegram(format_signal_alert(signal))
    if success:
        _add_sent_message(msg_hash)
    return success


def send_win_alert(trade: Dict) -> bool:
    """
    Send WIN alert.
    """
    trade_id = trade.get("id")
    if not trade_id:
        return False

    msg_hash = hash(f"win_{trade_id}")
    if _is_sent(msg_hash):
        logger.debug(f"Win alert sent: {trade_id}")
        return False

    success = send_telegram(format_win_alert(trade))
    if success:
        _add_sent_message(msg_hash)
    return success


def send_loss_alert(trade: Dict) -> bool:
    """
    Send LOSS alert.
    """
    trade_id = trade.get("id")
    if not trade_id:
        return False

    msg_hash = hash(f"loss_{trade_id}")
    if _is_sent(msg_hash):
        logger.debug(f"Loss alert sent: {trade_id}")
        return False

    success = send_telegram(format_loss_alert(trade))
    if success:
        _add_sent_message(msg_hash)
    return success