import pandas as pd
from typing import Optional, Dict
from utils.helpers import val
from core.levels import get_levels
from utils.logger import get_logger

logger = get_logger(__name__)

# ===== INTRADAY CONFIG =====
MIN_CANDLES = 80

SUPPORT_BUFFER = 8
RESISTANCE_BUFFER = 8
WICK_RATIO = 0.4
SL_BUFFER = 10

NEAR_LEVEL_RANGE = 12   # NEW
MIN_RANGE_FILTER = 50   # NEW

def check_signal(df: pd.DataFrame, trend: str) -> Optional[Dict]:
    try:
        if df is None:
            logger.warning("Signal check aborted: data frame is None")
            return None

        if len(df) < MIN_CANDLES:
            logger.warning(f"Signal check aborted: insufficient candles ({len(df)} < {MIN_CANDLES})")
            return None

        signal_candle = df.iloc[-3]
        confirm_candle = df.iloc[-2]

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

        # 🚫 Avoid bad market
        if range_size < MIN_RANGE_FILTER:
            logger.warning(f"Signal check aborted: range too narrow ({range_size} < {MIN_RANGE_FILTER})")
            return None

        price = cl2

        # ===== BUY =====
        if trend in ["UP", "SIDEWAYS"]:

            near_support = abs(price - support) < NEAR_LEVEL_RANGE

            if (
                (l1 < support - SUPPORT_BUFFER or near_support) and
                cl1 > support and
                lower_wick > body * WICK_RATIO and
                cl2 > cl1   # relaxed confirmation
            ):
                entry = round(cl2, 2)
                sl = round(l1 - SL_BUFFER, 2)

                # 🎯 realistic intraday target
                target = round(entry + (range_size * 0.3), 2)

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

            near_resistance = abs(price - resistance) < NEAR_LEVEL_RANGE

            if (
                (h1 > resistance + RESISTANCE_BUFFER or near_resistance) and
                cl1 < resistance and
                upper_wick > body * WICK_RATIO and
                cl2 < cl1   # relaxed confirmation
            ):
                entry = round(cl2, 2)
                sl = round(h1 + SL_BUFFER, 2)

                # 🎯 realistic intraday target
                target = round(entry - (range_size * 0.3), 2)

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