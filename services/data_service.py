import yfinance as yf

def get_data(symbol):
    df = yf.download(symbol, period="2d", interval="1m", progress=False, auto_adjust=True)

    if df is None or df.empty:
        return None

    df = df.dropna()

    if hasattr(df.columns, "levels"):
        df.columns = [c[0] if isinstance(c, tuple) else c for c in df.columns]

    return df