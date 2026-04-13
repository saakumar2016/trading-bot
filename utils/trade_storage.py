import csv
import os
from datetime import datetime
from typing import List, Dict
from utils.logger import get_logger

logger = get_logger(__name__)

TRADES_FILE = "/workspaces/trading-bot/data/trades.csv"

def ensure_data_dir() -> None:
    """Create data directory if it doesn't exist."""
    os.makedirs(os.path.dirname(TRADES_FILE), exist_ok=True)

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
            writer = csv.DictWriter(f, fieldnames=[
                'timestamp', 'type', 'entry', 'sl', 'target', 
                'trend', 'support', 'resistance'
            ])
            
            if not file_exists:
                writer.writeheader()
            
            trade_with_timestamp = {
                'timestamp': datetime.now().isoformat(),
                **trade
            }
            writer.writerow(trade_with_timestamp)
            
        logger.info(f"Trade saved: {trade['type']} @ {trade['entry']}")
        return True
        
    except Exception as e:
        logger.error(f"Error saving trade: {str(e)}")
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
