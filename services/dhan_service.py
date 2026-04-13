"""
Dhan API service for real-time market data.

Provides real-time OHLC data fetching from Dhan broker API.
Falls back gracefully if API is unavailable.
"""

import pandas as pd
from typing import Optional, Dict
from datetime import datetime, timedelta
from utils.logger import get_logger

logger = get_logger(__name__)

# Try to import dhan client
try:
    from dhanhq import dhanhq
    DHAN_AVAILABLE = True
except ImportError:
    DHAN_AVAILABLE = False
    logger.warning("dhanhq not installed. Dhan service will not be available.")


class DhanClient:
    """Wrapper for Dhan API client."""
    
    def __init__(self, client_id: str, access_token: str):
        """
        Initialize Dhan API client.
        
        Args:
            client_id: Dhan client ID
            access_token: Dhan access token
        """
        self.client_id = client_id
        self.access_token = access_token
        self.client = None
        
        if not DHAN_AVAILABLE:
            logger.error("Dhan client library not installed")
            return
            
        try:
            self.client = dhanhq.DhanClient(
                client_id=client_id,
                access_token=access_token
            )
            logger.info("Dhan API client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Dhan client: {str(e)}")
    
    def is_connected(self) -> bool:
        """Check if Dhan client is properly initialized."""
        return self.client is not None
    
    def get_live_price(self, symbol: str) -> Optional[float]:
        """
        Get current live price for a symbol.
        
        Args:
            symbol: Trading symbol (e.g., "50", "BANKNIFTY")
            
        Returns:
            Current price or None if failed
        """
        if not self.is_connected():
            logger.warning("Dhan client not connected")
            return None
        
        try:
            # Dhan API format: exchange=NSE, trading_symbol=symbol
            quote = self.client.get_quote(
                security_id=symbol,
                exchange_token="NSE"
            )
            
            if quote and isinstance(quote, dict):
                price = quote.get('ltp') or quote.get('close')
                logger.debug(f"Live price for {symbol}: {price}")
                return price
            
            logger.warning(f"No price data received for {symbol}")
            return None
            
        except Exception as e:
            logger.error(f"Error fetching live price for {symbol}: {str(e)}")
            return None
    
    def get_ohlc_data(
        self, 
        symbol: str, 
        timeframe: str
    ) -> Optional[pd.DataFrame]:
        """
        Fetch OHLC data from Dhan API.
        
        Args:
            symbol: Trading symbol (e.g., "50", "BANKNIFTY")
            timeframe: Timeframe (1m, 5m, 15m, 1h, 1d)
            
        Returns:
            DataFrame with OHLC data or None if failed
        """
        if not self.is_connected():
            logger.warning("Dhan client not connected")
            return None
        
        if timeframe not in ["1m", "5m", "15m", "1h", "1d"]:
            logger.error(f"Invalid timeframe: {timeframe}")
            return None
        
        try:
            # Map our timeframes to Dhan API format
            dhan_interval = self._map_timeframe(timeframe)
            
            # Determine number of candles and lookback period
            num_candles = self._get_num_candles(timeframe)
            
            # Fetch candles
            candles = self.client.intra_day_data(
                security_id=symbol,
                exchange_token="NSE",
                interval=dhan_interval,
                count=num_candles
            )
            
            if not candles or len(candles) == 0:
                logger.warning(f"No candle data received for {symbol} at {timeframe}")
                return None
            
            # Convert to DataFrame
            df = self._convert_to_dataframe(candles)
            
            if df is None or df.empty:
                logger.warning(f"Empty DataFrame for {symbol} at {timeframe}")
                return None
            
            logger.info(f"Fetched {len(df)} candles for {symbol} at {timeframe} from Dhan")
            return df
            
        except Exception as e:
            logger.error(f"Error fetching OHLC data for {symbol} at {timeframe}: {str(e)}")
            return None
    
    @staticmethod
    def _map_timeframe(timeframe: str) -> str:
        """
        Map our timeframe format to Dhan API format.
        
        Args:
            timeframe: Timeframe (1m, 5m, 15m, 1h, 1d)
            
        Returns:
            Dhan API interval format
        """
        mapping = {
            "1m": "1",
            "5m": "5",
            "15m": "15",
            "1h": "60",
            "1d": "1D"
        }
        return mapping.get(timeframe, "1")
    
    @staticmethod
    def _get_num_candles(timeframe: str) -> int:
        """
        Get number of candles to fetch based on timeframe.
        
        Args:
            timeframe: Timeframe (1m, 5m, 15m, 1h, 1d)
            
        Returns:
            Number of candles to fetch
        """
        mapping = {
            "1m": 1440,      # 1 day of 1m candles
            "5m": 576,       # 2 days of 5m candles
            "15m": 480,      # 5 days of 15m candles
            "1h": 720,       # 30 days of 1h candles
            "1d": 252        # ~1 year of 1d candles
        }
        return mapping.get(timeframe, 100)
    
    @staticmethod
    def _convert_to_dataframe(candles: list) -> Optional[pd.DataFrame]:
        """
        Convert Dhan API candle format to pandas DataFrame.
        
        Args:
            candles: List of candle data from Dhan API
            
        Returns:
            DataFrame with Open, High, Low, Close columns
        """
        if not candles:
            return None
        
        try:
            # Expected format: list of dicts with keys: timestamp, open, high, low, close, volume
            df = pd.DataFrame(candles)
            
            # Normalize column names (case-insensitive)
            df.columns = df.columns.str.lower()
            
            # Ensure required columns exist
            required_cols = ['open', 'high', 'low', 'close']
            missing = [col for col in required_cols if col not in df.columns]
            
            if missing:
                logger.error(f"Missing columns in Dhan response: {missing}")
                return None
            
            # Select and rename columns
            df = df[['open', 'high', 'low', 'close']].copy()
            df.columns = ['Open', 'High', 'Low', 'Close']
            
            # Convert to numeric
            for col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            
            # Handle index
            if 'timestamp' in df.columns:
                df['timestamp'] = pd.to_datetime(df['timestamp'])
                df.set_index('timestamp', inplace=True)
            
            # Drop NaN values
            df = df.dropna()
            
            return df
            
        except Exception as e:
            logger.error(f"Error converting Dhan candles to DataFrame: {str(e)}")
            return None


# Global client instance
_dhan_client: Optional[DhanClient] = None


def initialize_dhan(client_id: str, access_token: str) -> bool:
    """
    Initialize global Dhan API client.
    
    Args:
        client_id: Dhan client ID
        access_token: Dhan access token
        
    Returns:
        True if initialized successfully
    """
    global _dhan_client
    
    if not client_id or not access_token:
        logger.warning("Dhan credentials not provided")
        return False
    
    try:
        _dhan_client = DhanClient(client_id, access_token)
        return _dhan_client.is_connected()
    except Exception as e:
        logger.error(f"Failed to initialize Dhan: {str(e)}")
        return False


def get_dhan_client() -> Optional[DhanClient]:
    """Get global Dhan API client instance."""
    return _dhan_client


def get_live_price(symbol: str) -> Optional[float]:
    """
    Get live price from Dhan API.
    
    Args:
        symbol: Trading symbol
        
    Returns:
        Current price or None
    """
    if _dhan_client is None:
        logger.warning("Dhan client not initialized")
        return None
    
    return _dhan_client.get_live_price(symbol)


def get_ohlc_data(symbol: str, timeframe: str) -> Optional[pd.DataFrame]:
    """
    Get OHLC data from Dhan API.
    
    Args:
        symbol: Trading symbol
        timeframe: Timeframe (1m, 5m, 15m, 1h, 1d)
        
    Returns:
        DataFrame with OHLC data or None
    """
    if _dhan_client is None:
        logger.warning("Dhan client not initialized")
        return None
    
    return _dhan_client.get_ohlc_data(symbol, timeframe)
