import pandas as pd
from typing import Tuple
from utils.logger import get_logger

logger = get_logger(__name__)

# Configuration
LOOKBACK_PERIODS = 80
SAMPLE_SIZE = 5

def get_levels(df: pd.DataFrame) -> Tuple[float, float]:
    """
    Calculate support and resistance levels.
    
    Args:
        df: OHLC DataFrame
        
    Returns:
        Tuple of (support, resistance) prices
    """
    try:
        if len(df) < LOOKBACK_PERIODS:
            logger.warning(f"Insufficient data: {len(df)} < {LOOKBACK_PERIODS}")
            return 0.0, 0.0
            
        recent = df.tail(LOOKBACK_PERIODS)

        support = round(recent.nsmallest(SAMPLE_SIZE, 'Low')['Low'].mean(), 2)
        resistance = round(recent.nlargest(SAMPLE_SIZE, 'High')['High'].mean(), 2)

        logger.debug(f"Levels calculated - Support: {support}, Resistance: {resistance}")
        return support, resistance
        
    except Exception as e:
        logger.error(f"Error calculating levels: {str(e)}")
        return 0.0, 0.0