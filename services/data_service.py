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

# Initialize Dhan if configured
_dhan_initialized = False
if DHAN_AVAILABLE and DHAN_CLIENT_ID and DHAN_ACCESS_TOKEN:
    if DATA_SOURCE.upper() == "DHAN":
        _dhan_initialized = initialize_dhan(DHAN_CLIENT_ID, DHAN_ACCESS_TOKEN)
        if _dhan_initialized:
            logger.info("Dhan API initialized as primary data source")
        else:
            logger.error("Failed to initialize Dhan API; Dhan-only data service unavailable")
else:
    if DATA_SOURCE.upper() == "DHAN":
        logger.error("Dhan configured as DATA_SOURCE but credentials not provided. Dhan-only data service unavailable.")


def get_data(symbol: str, timeframe: str = None) -> Optional[pd.DataFrame]:
    """
    Fetch OHLC data from Dhan API only.

    Args:
        symbol: Trading symbol (e.g., "50" for Dhan)
        timeframe: Timeframe (1m, 5m, 15m, 1h, 1d). Defaults to config TIMEFRAME

    Returns:
        DataFrame with OHLC data or None if Dhan is unavailable
    """
    if timeframe is None:
        timeframe = TIMEFRAME

    # Validate timeframe
    if timeframe not in ["1m", "5m", "15m", "1h", "1d"]:
        logger.error(f"Invalid timeframe: {timeframe}")
        return None

    if DATA_SOURCE.upper() != "DHAN":
        logger.error("DATA_SOURCE is not DHAN. This service only supports Dhan API.")
        return None

    if not _dhan_initialized:
        logger.error("Dhan API not initialized; cannot fetch OHLC data")
        return None

    logger.debug(f"Fetching OHLC data from Dhan for {symbol} at {timeframe}")
    df = get_dhan_ohlc(symbol, timeframe)

    if df is not None and not df.empty:
        logger.info(f"Successfully fetched OHLC from Dhan for {symbol} at {timeframe}")
        return df

    logger.error(f"Failed to fetch OHLC from Dhan for {symbol} at {timeframe}")
    return None


def get_live_price(symbol: str, source: str = None) -> Optional[float]:
    """
    Get live price exclusively from Dhan API.

    Args:
        symbol: Trading symbol
        source: Data source. Only "DHAN" is supported.

    Returns:
        Live price or None if unavailable
    """
    if source is None:
        source = DATA_SOURCE

    if source.upper() != "DHAN":
        logger.error("Only Dhan live prices are supported")
        return None

    if not DHAN_AVAILABLE:
        logger.error("Dhan library not available")
        return None

    if not _dhan_initialized:
        logger.error("Dhan API not initialized; cannot fetch live price")
        return None

    try:
        price = get_dhan_live_price(symbol)
        if price is not None:
            logger.debug(f"Live price from Dhan: {symbol} = {price}")
            return price
        logger.warning(f"Dhan returned no price for {symbol}")
        return None
    except Exception as e:
        logger.error(f"Failed to get live price from Dhan: {str(e)}")
        return None