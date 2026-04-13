from utils.helpers import val
from core.levels import get_levels

def check_signal(df, trend):
    if len(df) < 5:
        return None

    c1 = df.iloc[-3]
    c2 = df.iloc[-2]

    o1, h1, l1, cl1 = val(c1['Open']), val(c1['High']), val(c1['Low']), val(c1['Close'])
    o2, cl2 = val(c2['Open']), val(c2['Close'])

    body = abs(cl1 - o1)
    upper_wick = h1 - max(o1, cl1)
    lower_wick = min(o1, cl1) - l1

    support, resistance = get_levels(df)
    range_size = resistance - support

    if trend in ["UP", "SIDEWAYS"]:
        if l1 < support - 5 and cl1 > support and lower_wick > body * 0.8 and cl2 > o2:
            entry = round(cl2, 2)
            return {
                "type": "BUY",
                "entry": entry,
                "sl": round(l1 - 10, 2),
                "target": round(entry + range_size * 0.6, 2)
            }

    if trend in ["DOWN", "SIDEWAYS"]:
        if h1 > resistance + 5 and cl1 < resistance and upper_wick > body * 0.8 and cl2 < o2:
            entry = round(cl2, 2)
            return {
                "type": "SELL",
                "entry": entry,
                "sl": round(h1 + 10, 2),
                "target": round(entry - range_size * 0.6, 2)
            }

    return None