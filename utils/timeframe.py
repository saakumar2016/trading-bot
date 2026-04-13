"""
Timeframe configuration and utilities for multi-timeframe analysis.
"""
from typing import List, Literal
from config import LOG_LEVEL
from utils.logger import get_logger

logger = get_logger(__name__)

# Supported timeframes
TIMEFRAME_VALUES = ["1m", "5m", "15m", "1h", "1d"]
TIMEFRAME_TO_MINUTES = {
    "1m": 1,
    "5m": 5,
    "15m": 15,
    "1h": 60,
    "1d": 1440
}
TIMEFRAME_TO_PERIOD = {
    "1m": "1d",      # Last 1 day for 1-min data
    "5m": "2d",      # Last 2 days for 5-min data
    "15m": "5d",     # Last 5 days for 15-min data
    "1h": "30d",     # Last 30 days for hourly data
    "1d": "1y"       # Last 1 year for daily data
}

class TimeframeConfig:
    """
    Configuration for trading timeframe.
    
    Attributes:
        value: Timeframe string (1m, 5m, 15m, 1h, 1d)
        minutes: Minutes in timeframe
        period: yfinance period for data collection
    """
    
    def __init__(self, value: str = "1m"):
        """
        Initialize timeframe configuration.
        
        Args:
            value: Timeframe string from TIMEFRAME_VALUES
            
        Raises:
            ValueError: If timeframe not supported
        """
        if value not in TIMEFRAME_VALUES:
            raise ValueError(f"Unsupported timeframe: {value}. Must be one of {TIMEFRAME_VALUES}")
        
        self.value = value
        self.minutes = TIMEFRAME_TO_MINUTES[value]
        self.period = TIMEFRAME_TO_PERIOD[value]
        
        logger.info(f"Timeframe configured: {value} ({self.minutes} min, period: {self.period})")
    
    def __str__(self) -> str:
        return self.value
    
    def __repr__(self) -> str:
        return f"TimeframeConfig({self.value})"


def get_timeframe_from_env() -> TimeframeConfig:
    """
    Get timeframe configuration from environment.
    
    Returns:
        TimeframeConfig object with configured timeframe
    """
    import os
    timeframe_str = os.getenv("TIMEFRAME", "1m")
    
    try:
        return TimeframeConfig(timeframe_str)
    except ValueError as e:
        logger.warning(f"Invalid timeframe in .env: {e}. Using default 1m")
        return TimeframeConfig("1m")
