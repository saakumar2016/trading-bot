import logging
import sys
import os
from config import LOG_LEVEL

# Determine log file path (works for both local and Streamlit Cloud)
log_dir = os.path.join(os.path.expanduser('~'), '.streamlit_logs')
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, 'bot.log')

# Configure logging
handlers = [logging.StreamHandler(sys.stdout)]

# Try to add file handler
try:
    handlers.append(logging.FileHandler(log_file, mode='a'))
except Exception as e:
    # If file logging fails, just use console
    print(f"Warning: Could not setup file logging: {e}")

logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=handlers
)

def get_logger(name):
    return logging.getLogger(name)
