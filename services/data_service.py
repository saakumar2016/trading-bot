import yfinance as yf
import pandas as pd
from utils.logger import get_logger
from config import TIMEFRAME

logger = get_logger(__name__)

# Timeframe mappings
TIMEFRAME_TO_PERIOD = {
    "1m": "1d",
    "5m": "2d",
    "15m": "5d",
    "1h": "30d",
    "1d": "1y"
}

def get_data(symbol: str, timeframe: str = None) -> pd.DataFrame | None:
    """
    Fetch OHLC data for the given symbol and timeframe.
    
    Args:
        symbol: Trading symbol (e.g., "^NSEI")
        timeframe: Timeframe (1m, 5m, 15m, 1h, 1d). Defaults to config TIMEFRAME
        
    Returns:
        DataFrame with OHLC data or None if failed
    """
    if timeframe is None:
        timeframe = TIMEFRAME
    
    try:
        period = TIMEFRAME_TO_PERIOD.get(timeframe, "1d")
        logger.info(f"Fetching {timeframe} data for {symbol}, period: {period}")
        
        df = yf.download(
            symbol, 
            period=period, 
            interval=timeframe, 
            progress=False, 
            auto_adjust=True
        )

        if df is None or df.empty:
            logger.warning(f"No data received for {symbol} at {timeframe}")
            return None

        df = df.dropna()
        
        # Fix multi-index columns (yfinance returns multi-index for single symbol)
        if hasattr(df.columns, "levels"):
            df.columns = [c[0] if isinstance(c, tuple) else c for c in df.columns]

        logger.debug(f"Data fetched successfully: {len(df)} rows of {timeframe} data")
        return df
        
    except Exception as e:
        logger.error(f"Failed to fetch data for {symbol} at {timeframe}: {str(e)}")
        return None