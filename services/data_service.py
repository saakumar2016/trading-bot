import pandas as pd
from typing import Optional
from datetime import datetime, timedelta
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


SYMBOL_MAPPING = {
    "^NSEI": "50",
    "^BANKNIFTY": "25"
}


def _map_symbol(symbol: str) -> str:
    mapped = SYMBOL_MAPPING.get(symbol, symbol)
    if mapped != symbol:
        logger.debug(f"Mapped symbol '{symbol}' to Dhan symbol '{mapped}'")
    return mapped


def _normalize_dataframe(df: pd.DataFrame) -> Optional[pd.DataFrame]:
    if df is None:
        return None

    # Normalize columns to expected Dhan output
    df = df.copy()
    column_map = {
        "open": "Open",
        "high": "High",
        "low": "Low",
        "close": "Close"
    }

    lower_cols = {col.lower(): col for col in df.columns}
    normalized = {}
    for lower_name, expected_name in column_map.items():
        if lower_name in lower_cols:
            original = lower_cols[lower_name]
            normalized[original] = expected_name

    if not normalized:
        logger.error("Dhan data has no OHLC columns to normalize")
        return None

    df = df.rename(columns=normalized)

    required_columns = list(column_map.values())
    missing = [col for col in required_columns if col not in df.columns]
    if missing:
        logger.error(f"Dhan data missing required columns after normalization: {missing}")
        return None

    df = df[required_columns].copy()
    df = df.apply(pd.to_numeric, errors="coerce")
    df = df.dropna()

    return df


def _validate_dataframe(df: pd.DataFrame) -> bool:
    if df is None:
        logger.error("Dhan OHLC data is None")
        return False

    if df.empty:
        logger.error("Dhan OHLC data is empty")
        return False

    if len(df) < 80:
        logger.error(f"Dhan OHLC data has too few candles: {len(df)} < 80")
        return False

    # Check if last candle is recent (not stale)
    if 'timestamp' in df.columns:
        try:
            last_timestamp = pd.to_datetime(df['timestamp'].iloc[-1])
            now = datetime.now()
            # Allow up to 5 minutes staleness for intraday data
            max_age = timedelta(minutes=5)
            if now - last_timestamp > max_age:
                logger.error(f"Dhan data is stale: last candle at {last_timestamp}, current time {now}")
                return False
        except Exception as e:
            logger.warning(f"Could not validate timestamp freshness: {str(e)}")

    return True


def _fetch_with_retry(symbol: str, timeframe: str, max_retries: int = 3) -> Optional[pd.DataFrame]:
    """
    Fetch data from Dhan with retry mechanism.

    Args:
        symbol: Mapped symbol
        timeframe: Timeframe
        max_retries: Maximum number of retry attempts

    Returns:
        DataFrame or None if all retries fail
    """
    for attempt in range(max_retries):
        try:
            logger.debug(f"Fetching Dhan data for {symbol} at {timeframe} (attempt {attempt + 1}/{max_retries})")
            df = get_dhan_ohlc(symbol, timeframe)

            if df is not None:
                logger.info(f"Successfully fetched Dhan data for {symbol} at {timeframe} on attempt {attempt + 1}")
                return df
            else:
                logger.warning(f"Dhan returned no data for {symbol} at {timeframe} (attempt {attempt + 1})")

        except Exception as e:
            logger.error(f"Dhan fetch failed for {symbol} at {timeframe} (attempt {attempt + 1}): {str(e)}")

        # Wait before retry (exponential backoff)
        if attempt < max_retries - 1:
            import time
            wait_time = 2 ** attempt  # 1s, 2s, 4s
            logger.info(f"Retrying in {wait_time} seconds...")
            time.sleep(wait_time)

    logger.error(f"All {max_retries} attempts failed for Dhan data fetch: {symbol} at {timeframe}")
    return None


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

    mapped_symbol = _map_symbol(symbol)
    logger.debug(f"Fetching OHLC data from Dhan for {mapped_symbol} at {timeframe}")

    # Use retry mechanism
    df = _fetch_with_retry(mapped_symbol, timeframe, max_retries=3)

    if df is None:
        logger.error(f"Failed to fetch data from Dhan for {mapped_symbol} at {timeframe} after retries")
        return None

    df = _normalize_dataframe(df)
    if df is None:
        logger.error(f"Failed to normalize Dhan data for {mapped_symbol} at {timeframe}")
        return None

    if not _validate_dataframe(df):
        logger.error(f"Invalid Dhan data for {mapped_symbol} at {timeframe}")
        return None

    logger.info(f"Successfully fetched and validated Dhan OHLC data for {mapped_symbol} at {timeframe} ({len(df)} candles)")
    return df


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