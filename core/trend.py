import pandas as pd
from utils.helpers import val
from utils.logger import get_logger

logger = get_logger(__name__)

# Configuration
MIN_DATA_POINTS = 20
LOOKBACK_CANDLES = 8
THRESHOLD = 10

def get_trend(df: pd.DataFrame) -> str:
    """
    Determine current trend.
    
    Args:
        df: OHLC DataFrame
        
    Returns:
        Trend: "UP", "DOWN", or "SIDEWAYS"
    """
    try:
        if len(df) < MIN_DATA_POINTS:
            logger.debug(f"Insufficient data for trend: {len(df)} < {MIN_DATA_POINTS}")
            return "SIDEWAYS"

        curr = val(df['Close'].iloc[-1])
        prev = val(df['Close'].iloc[-LOOKBACK_CANDLES])

        diff = curr - prev

        if abs(diff) < THRESHOLD:
            trend = "SIDEWAYS"
        else:
            trend = "UP" if diff > 0 else "DOWN"
            
        logger.debug(f"Trend: {trend} (diff: {diff})")
        return trend
        
    except Exception as e:
        logger.error(f"Error calculating trend: {str(e)}")
        return "SIDEWAYS"