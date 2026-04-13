from utils.helpers import val

def get_trend(df):
    if len(df) < 20:
        return "SIDEWAYS"

    curr = val(df['Close'].iloc[-1])
    prev = val(df['Close'].iloc[-16])

    diff = curr - prev

    if abs(diff) < 10:
        return "SIDEWAYS"

    return "UP" if diff > 0 else "DOWN"