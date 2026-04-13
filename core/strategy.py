import pandas as pd
from typing import Optional, Dict
from utils.helpers import val
from core.levels import get_levels
from utils.logger import get_logger

logger = get_logger(__name__)

# === Configuration ===
MIN_CANDLES = 5

# SUPPORT_BUFFER = 5
# RESISTANCE_BUFFER = 5
# WICK_RATIO = 0.8
SUPPORT_BUFFER = 2
RESISTANCE_BUFFER = 2
WICK_RATIO = 0.5
TARGET_MULTIPLIER = 0.6
SL_BUFFER = 10

def check_signal(df: pd.DataFrame, trend: str) -> Optional[Dict]:
    try:
        if len(df) < MIN_CANDLES:
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

        # ❗ Fix doji issue
        if body == 0:
            return None

        upper_wick = h1 - max(o1, cl1)
        lower_wick = min(o1, cl1) - l1

        support, resistance = get_levels(df)

        # ===== BUY =====
        if trend in ["UP", "SIDEWAYS"]:
            if (l1 < support - SUPPORT_BUFFER and 
                cl1 > support and 
                lower_wick > body * WICK_RATIO and 
                cl2 > o2):

                entry = round(cl2, 2)
                sl = round(l1 - SL_BUFFER, 2)
                target = round(resistance - 2, 2)

                risk = entry - sl
                reward = target - entry

                if risk <= 0 or reward / risk < 1.2:
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
            if (h1 > resistance + RESISTANCE_BUFFER and 
                cl1 < resistance and 
                upper_wick > body * WICK_RATIO and 
                cl2 < o2):

                entry = round(cl2, 2)
                sl = round(h1 + SL_BUFFER, 2)
                target = round(support + 2, 2)

                risk = sl - entry
                reward = entry - target

                if risk <= 0 or reward / risk < 1.2:
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