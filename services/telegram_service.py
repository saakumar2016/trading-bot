import hashlib
import os
from typing import Dict, Optional
from datetime import datetime
from utils.logger import get_logger

logger = get_logger(__name__)

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN', '')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '')


class AlertTracker:
    """Track sent alerts to prevent spam."""
    
    def __init__(self):
        self._sent_alerts: Dict[str, int] = {}
    
    def _get_alert_key(self, trade_id: str, event_type: str) -> str:
        """Get unique key for trade + event type combination."""
        return f"{trade_id}_{event_type}"
    
    def _get_hash_key(self, content: str) -> str:
        """Get hash of content for deduplication."""
        return hashlib.md5(content.encode()).hexdigest()
    
    def mark_sent(self, trade_id: str, event_type: str) -> None:
        """Mark alert as sent for this trade and event type."""
        key = self._get_alert_key(trade_id, event_type)
        self._sent_alerts[key] = int(datetime.now().timestamp())
    
    def is_sent(self, trade_id: str, event_type: str) -> bool:
        """Check if alert already sent for this trade and event type."""
        key = self._get_alert_key(trade_id, event_type)
        return key in self._sent_alerts
    
    def clear_trade_alerts(self, trade_id: str) -> None:
        """Clear all alerts for a specific trade (when trade closes)."""
        keys_to_remove = [k for k in self._sent_alerts.keys() if k.startswith(f"{trade_id}_")]
        for key in keys_to_remove:
            del self._sent_alerts[key]
        logger.debug(f"Cleared {len(keys_to_remove)} alerts for trade {trade_id}")


_alert_tracker = AlertTracker()


def get_alert_tracker() -> AlertTracker:
    return _alert_tracker


def send_telegram(message: str) -> bool:
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        logger.warning("Telegram credentials not configured")
        return False

    try:
        import requests
        
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        payload = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message,
            "parse_mode": "HTML"
        }
        
        response = requests.post(url, json=payload, timeout=10)
        
        if response.status_code == 200:
            logger.info("Telegram message sent successfully")
            return True
        else:
            logger.error(f"Telegram error: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"Error sending Telegram message: {str(e)}")
        return False


def format_signal_alert(signal: Dict) -> str:
    signal_type = signal.get('type', 'UNKNOWN')
    entry = signal.get('entry', 0)
    sl = signal.get('sl', 0)
    target = signal.get('target', 0)
    trend = signal.get('trend', 'N/A')
    
    return (
        f"<b>🔔 NEW SIGNAL</b>\n"
        f"Type: <b>{signal_type}</b>\n"
        f"Entry: {entry}\n"
        f"SL: {sl}\n"
        f"Target: {target}\n"
        f"Trend: {trend}\n"
        f"Time: {datetime.now().strftime('%H:%M:%S')}"
    )


def format_win_alert(trade: Dict) -> str:
    trade_type = trade.get('type', 'UNKNOWN')
    entry = trade.get('entry', 0)
    exit_price = trade.get('exit_price', 0)
    pnl = trade.get('pnl', 0)
    
    return (
        f"<b>✅ TRADE WIN</b>\n"
        f"Type: <b>{trade_type}</b>\n"
        f"Entry: {entry}\n"
        f"Exit: {exit_price}\n"
        f"PnL: <b>+{pnl}</b>\n"
        f"Time: {datetime.now().strftime('%H:%M:%S')}"
    )


def format_loss_alert(trade: Dict) -> str:
    trade_type = trade.get('type', 'UNKNOWN')
    entry = trade.get('entry', 0)
    exit_price = trade.get('exit_price', 0)
    pnl = trade.get('pnl', 0)
    
    return (
        f"<b>❌ TRADE LOSS</b>\n"
        f"Type: <b>{trade_type}</b>\n"
        f"Entry: {entry}\n"
        f"Exit: {exit_price}\n"
        f"PnL: <b>{pnl}</b>\n"
        f"Time: {datetime.now().strftime('%H:%M:%S')}"
    )


def format_timeout_alert(trade: Dict) -> str:
    trade_type = trade.get('type', 'UNKNOWN')
    entry = trade.get('entry', 0)
    exit_price = trade.get('exit_price', 0)
    pnl = trade.get('pnl', 0)
    
    return (
        f"<b>⏱️ TRADE TIMEOUT</b>\n"
        f"Type: <b>{trade_type}</b>\n"
        f"Entry: {entry}\n"
        f"Exit (current): {exit_price}\n"
        f"PnL: <b>{pnl}</b>\n"
        f"Reason: 30min timeout\n"
        f"Time: {datetime.now().strftime('%H:%M:%S')}"
    )


def send_signal_alert(signal: Dict, trade_id: str) -> bool:
    tracker = get_alert_tracker()
    
    if tracker.is_sent(trade_id, 'signal'):
        logger.debug(f"Signal alert already sent for trade {trade_id}")
        return False
    
    message = format_signal_alert(signal)
    success = send_telegram(message)
    
    if success:
        tracker.mark_sent(trade_id, 'signal')
        logger.info(f"Signal alert sent for trade {trade_id}")
    
    return success


def send_win_alert(trade: Dict) -> bool:
    tracker = get_alert_tracker()
    trade_id = trade.get('id', '')
    
    if tracker.is_sent(trade_id, 'win'):
        logger.debug(f"Win alert already sent for trade {trade_id}")
        return False
    
    message = format_win_alert(trade)
    success = send_telegram(message)
    
    if success:
        tracker.mark_sent(trade_id, 'win')
        logger.info(f"Win alert sent for trade {trade_id}")
    
    return success


def send_loss_alert(trade: Dict) -> bool:
    tracker = get_alert_tracker()
    trade_id = trade.get('id', '')
    
    if tracker.is_sent(trade_id, 'loss'):
        logger.debug(f"Loss alert already sent for trade {trade_id}")
        return False
    
    message = format_loss_alert(trade)
    success = send_telegram(message)
    
    if success:
        tracker.mark_sent(trade_id, 'loss')
        logger.info(f"Loss alert sent for trade {trade_id}")
    
    return success


def send_timeout_alert(trade: Dict) -> bool:
    tracker = get_alert_tracker()
    trade_id = trade.get('id', '')
    
    if tracker.is_sent(trade_id, 'timeout'):
        logger.debug(f"Timeout alert already sent for trade {trade_id}")
        return False
    
    message = format_timeout_alert(trade)
    success = send_telegram(message)
    
    if success:
        tracker.mark_sent(trade_id, 'timeout')
        logger.info(f"Timeout alert sent for trade {trade_id}")
    
    return success


def clear_trade_alerts(trade_id: str) -> None:
    """Clear all alerts for a closed trade."""
    tracker = get_alert_tracker()
    tracker.clear_trade_alerts(trade_id)
