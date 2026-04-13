import yfinance as yf
import pandas as pd
from typing import Optional
from utils.logger import get_logger
from config import TIMEFRAME, DATA_SOURCE, DHAN_CLIENT_ID, DHAN_ACCESS_TOKEN

logger = get_logger(__name__)

# Try to import Dhan service
try:
    from services.dhan_service import (
        initialize_dhan,
        get_ohlc_data as get_dhan_ohlc,
        get_live_price as get_dhan_live_price
    )
    DHAN_AVAILABLE = True
except ImportError:
    DHAN_AVAILABLE = False
    logger.warning("Dhan service not available")

# Timeframe mappings for yfinance
TIMEFRAME_TO_PERIOD = {
    "1m": "1d",
    "5m": "2d",
    "15m": "5d",
    "1h": "30d",
    "1d": "1y"
}

# Initialize Dhan if configured
_dhan_initialized = False
if DHAN_AVAILABLE and DHAN_CLIENT_ID and DHAN_ACCESS_TOKEN:
    if DATA_SOURCE.upper() == "DHAN":
        _dhan_initialized = initialize_dhan(DHAN_CLIENT_ID, DHAN_ACCESS_TOKEN)
        if _dhan_initialized:
            logger.info("Dhan API initialized as primary data source")
        else:
            logger.warning("Failed to initialize Dhan API, will use yfinance")
else:
    if DATA_SOURCE.upper() == "DHAN":
        logger.warning("Dhan configured as DATA_SOURCE but credentials not provided, using yfinance")


def _get_data_from_yfinance(symbol: str, timeframe: str) -> Optional[pd.DataFrame]:
    """
    Fetch OHLC data from yfinance.
    
    Args:
        symbol: Trading symbol (e.g., "^NSEI")
        timeframe: Timeframe (1m, 5m, 15m, 1h, 1d)
        
    Returns:
        DataFrame with OHLC data or None if failed
    """
    try:
        period = TIMEFRAME_TO_PERIOD.get(timeframe, "1d")
        logger.debug(f"Fetching {timeframe} data from yfinance for {symbol}, period: {period}")
        
        df = yf.download(
            symbol, 
            period=period, 
            interval=timeframe, 
            progress=False, 
            auto_adjust=True
        )

        if df is None or df.empty:
            logger.warning(f"No data received from yfinance for {symbol} at {timeframe}")
            return None

        df = df.dropna()
        
        # Fix multi-index columns (yfinance returns multi-index for single symbol)
        if hasattr(df.columns, "levels"):
            df.columns = [c[0] if isinstance(c, tuple) else c for c in df.columns]

        logger.info(f"Fetched {len(df)} rows of {timeframe} data from yfinance for {symbol}")
        return df
        
    except Exception as e:
        logger.error(f"Failed to fetch data from yfinance for {symbol} at {timeframe}: {str(e)}")
        return None


def get_data(symbol: str, timeframe: str = None) -> Optional[pd.DataFrame]:
    """
    Fetch OHLC data with smart fallback.
    
    Strategy:
    - If Dhan configured: Try Dhan first, fallback to yfinance on error
    - If yfinance configured: Use yfinance directly
    
    Args:
        symbol: Trading symbol (e.g., "^NSEI" for yfinance, "50" for Dhan)
        timeframe: Timeframe (1m, 5m, 15m, 1h, 1d). Defaults to config TIMEFRAME
        
    Returns:
        DataFrame with OHLC data or None if all sources fail
    """
    if timeframe is None:
        timeframe = TIMEFRAME
    
    # Validate timeframe
    if timeframe not in ["1m", "5m", "15m", "1h", "1d"]:
        logger.error(f"Invalid timeframe: {timeframe}")
        return None
    
    # Try Dhan if it's the primary source and initialized
    if _dhan_initialized and DATA_SOURCE.upper() == "DHAN":
        logger.debug(f"Attempting to fetch OHLC from Dhan for {symbol} at {timeframe}")
        df = get_dhan_ohlc(symbol, timeframe)
        
        if df is not None and not df.empty:
            logger.info(f"Successfully fetched OHLC from Dhan for {symbol} at {timeframe}")
            return df
        
        # Fallback to yfinance if Dhan fails (historical data)
        logger.warning(f"Dhan OHLC fetch failed for {symbol}, falling back to yfinance for historical data")
    
    # Use yfinance as primary or fallback
    return _get_data_from_yfinance(symbol, timeframe)


def get_live_price(symbol: str, source: str = None) -> Optional[float]:
    """
    Get live price using configured data source.
    
    Args:
        symbol: Trading symbol
        source: Data source ("DHAN" or "YFINANCE"). Uses config if not specified.
        
    Returns:
        Live price or None if failed
    """
    if source is None:
        source = DATA_SOURCE
    
    # Use Dhan for live prices when configured
    if source.upper() == "DHAN":
        if not DHAN_AVAILABLE:
            logger.error("Dhan requested but library not available")
            return None
        
        if not _dhan_initialized:
            logger.error("Dhan requested but not initialized (missing credentials)")
            return None
        
        try:
            price = get_dhan_live_price(symbol)
            if price is not None:
                logger.debug(f"Live price from Dhan: {symbol} = {price}")
                return price
            else:
                logger.warning(f"Dhan returned no price for {symbol}")
                return None
        except Exception as e:
            logger.error(f"Failed to get live price from Dhan: {str(e)}")
            return None
    
    # Use yfinance for live prices (fallback only if DATA_SOURCE != DHAN)
    try:
        ticker = yf.Ticker(symbol)
        price = ticker.info.get('currentPrice') or ticker.info.get('regularMarketPrice')
        if price:
            logger.debug(f"Got live price from yfinance for {symbol}: {price}")
            return price
    except Exception as e:
        logger.error(f"Failed to get live price from yfinance: {str(e)}")
    
    return None