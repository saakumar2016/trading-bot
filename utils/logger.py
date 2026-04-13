import logging
import sys
from config import LOG_LEVEL

# Configure logging
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('/workspaces/trading-bot/logs/bot.log', mode='a')
    ]
)

def get_logger(name):
    return logging.getLogger(name)
