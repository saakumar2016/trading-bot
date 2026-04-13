import requests
from config import TELEGRAM_TOKEN, CHAT_ID
from utils.logger import get_logger

logger = get_logger(__name__)

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