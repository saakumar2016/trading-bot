import pandas as pd
from typing import Optional, Dict
from datetime import datetime
from utils.helpers import val
from core.levels import get_levels
from utils.logger import get_logger

logger = get_logger(__name__)

# ===== INTRADAY CONFIG =====
MIN_CANDLES = 80

SUPPORT_BUFFER = 8
RESISTANCE_BUFFER = 8
WICK_RATIO = 0.4
SL_BUFFER = 5

NEAR_LEVEL_RANGE = 10   # Distance from level threshold (points)
MIN_RANGE_FILTER = 80   # Minimum range for signal generation

def _is_trading_hours(df: pd.DataFrame) -> bool:
    """Check if current time is within trading windows."""
    try:
        if df is None or len(df) == 0:
            return False
        
        last_idx = df.index[-1]
        if isinstance(last_idx, pd.Timestamp):
            hour = last_idx.hour + last_idx.minute / 60.0
        else:
            return False
        
        # 09:30-11:30 (9.5-11.5) and 13:30-15:00 (13.5-15.0)
        return (9.5 <= hour <= 11.5) or (13.5 <= hour <= 15.0)
    except:
        return False

def check_signal(df: pd.DataFrame, trend: str) -> Optional[Dict]:
    try:
        if df is None:
            logger.warning("Signal check aborted: data frame is None")
            return None

        if len(df) < MIN_CANDLES:
            logger.warning(f"Signal check aborted: insufficient candles ({len(df)} < {MIN_CANDLES})")
            return None

        signal_candle = df.iloc[-2]    # Changed from -3 (earlier entry)
        confirm_candle = df.iloc[-1]   # Changed from -2

        o1 = val(signal_candle['Open'])
        h1 = val(signal_candle['High'])
        l1 = val(signal_candle['Low'])
        cl1 = val(signal_candle['Close'])

        o2 = val(confirm_candle['Open'])
        cl2 = val(confirm_candle['Close'])

        body = abs(cl1 - o1)

        if body == 0:
            return None

        upper_wick = h1 - max(o1, cl1)
        lower_wick = min(o1, cl1) - l1

        support, resistance = get_levels(df)
        range_size = resistance - support

        # 🚫 Strict filters for high-quality signals
        if range_size < MIN_RANGE_FILTER:
            logger.warning(f"Signal check aborted: range too narrow ({range_size} < {MIN_RANGE_FILTER})")
            return None
        
        if not _is_trading_hours(df):
            logger.debug("Signal check aborted: outside trading hours")
            return None

        price = cl2

        # ===== BUY =====
        if trend in ["UP", "SIDEWAYS"]:

            distance_to_support = abs(price - support)
            near_support = distance_to_support <= NEAR_LEVEL_RANGE

            if (
                distance_to_support <= NEAR_LEVEL_RANGE and
                (l1 < support - SUPPORT_BUFFER or near_support) and
                cl1 > support and
                lower_wick > body * 2.0 and
                cl2 > cl1   # confirmation candle
            ):
                entry = round(cl2, 2)
                sl = round(l1 - SL_BUFFER, 2)

                # 🎯 realistic intraday target with level constraints
                raw_target = round(entry + (range_size * 0.3), 2)
                target = round(min(raw_target, resistance - 5), 2)  # Don't exceed resistance

                risk = entry - sl
                reward = target - entry

                if risk <= 0 or reward / risk < 1.1:
                    return None

                return {
                    "type": "BUY",
                    "entry": entry,
                    "sl": sl,
                    "target": target,
                    "trend": trend,
                    "support": support,
                    "resistance": resistance
                }

        # ===== SELL =====
        if trend in ["DOWN", "SIDEWAYS"]:

            distance_to_resistance = abs(price - resistance)
            near_resistance = distance_to_resistance <= NEAR_LEVEL_RANGE

            if (
                distance_to_resistance <= NEAR_LEVEL_RANGE and
                (h1 > resistance + RESISTANCE_BUFFER or near_resistance) and
                cl1 < resistance and
                upper_wick > body * 2.0 and
                cl2 < cl1   # confirmation candle
            ):
                entry = round(cl2, 2)
                sl = round(h1 + SL_BUFFER, 2)

                # 🎯 realistic intraday target with level constraints
                raw_target = round(entry - (range_size * 0.3), 2)
                target = round(max(raw_target, support + 5), 2)  # Don't go below support

                risk = sl - entry
                reward = entry - target

                if risk <= 0 or reward / risk < 1.1:
                    return None

                return {
                    "type": "SELL",
                    "entry": entry,
                    "sl": sl,
                    "target": target,
                    "trend": trend,
                    "support": support,
                    "resistance": resistance
                }

        return None

    except Exception as e:
        logger.error(f"Error checking signal: {str(e)}")
        return None