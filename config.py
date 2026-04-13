import os
import sys

# Try to import Streamlit for cloud deployment
try:
    import streamlit as st
    HAS_STREAMLIT = True
except ImportError:
    HAS_STREAMLIT = False

# Try to load .env for local development
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # dotenv not available (OK for Streamlit Cloud, will use env vars)
    pass

# === Trading Configuration ===
# Try Streamlit secrets first, then .env, then defaults
if HAS_STREAMLIT and hasattr(st, 'secrets'):
    try:
        SYMBOL = st.secrets.get("symbol", os.getenv("SYMBOL", "^NSEI"))
        TIMEFRAME = st.secrets.get("timeframe", os.getenv("TIMEFRAME", "1m"))
        REFRESH_INTERVAL = int(st.secrets.get("refresh_interval", os.getenv("REFRESH_INTERVAL", "10")))
        LOG_LEVEL = st.secrets.get("log_level", os.getenv("LOG_LEVEL", "INFO"))
        TELEGRAM_TOKEN = st.secrets.get("telegram_token", os.getenv("TELEGRAM_TOKEN", ""))
        CHAT_ID = st.secrets.get("chat_id", os.getenv("CHAT_ID", ""))
        
        # Dhan API Configuration
        DHAN_CLIENT_ID = st.secrets.get("dhan_client_id", os.getenv("DHAN_CLIENT_ID", ""))
        DHAN_ACCESS_TOKEN = st.secrets.get("dhan_access_token", os.getenv("DHAN_ACCESS_TOKEN", ""))
        DATA_SOURCE = st.secrets.get("data_source", os.getenv("DATA_SOURCE", "YFINANCE"))
    except Exception as e:
        # Fall back to .env if secrets fail
        SYMBOL = os.getenv("SYMBOL", "^NSEI")
        TIMEFRAME = os.getenv("TIMEFRAME", "1m")
        REFRESH_INTERVAL = int(os.getenv("REFRESH_INTERVAL", "10"))
        LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
        TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "")
        CHAT_ID = os.getenv("CHAT_ID", "")
        DHAN_CLIENT_ID = os.getenv("DHAN_CLIENT_ID", "")
        DHAN_ACCESS_TOKEN = os.getenv("DHAN_ACCESS_TOKEN", "")
        DATA_SOURCE = os.getenv("DATA_SOURCE", "YFINANCE")
else:
    # Local development or non-Streamlit environment
    SYMBOL = os.getenv("SYMBOL", "^NSEI")
    TIMEFRAME = os.getenv("TIMEFRAME", "1m")
    REFRESH_INTERVAL = int(os.getenv("REFRESH_INTERVAL", "10"))
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "")
    CHAT_ID = os.getenv("CHAT_ID", "")
    DHAN_CLIENT_ID = os.getenv("DHAN_CLIENT_ID", "")
    DHAN_ACCESS_TOKEN = os.getenv("DHAN_ACCESS_TOKEN", "")
    DATA_SOURCE = os.getenv("DATA_SOURCE", "YFINANCE")

# === Validation ===
if not TELEGRAM_TOKEN or TELEGRAM_TOKEN == "":
    import warnings
    warnings.warn("TELEGRAM_TOKEN not set - alerts will not be sent")

# Validate timeframe
VALID_TIMEFRAMES = ["1m", "5m", "15m", "1h", "1d"]
if TIMEFRAME not in VALID_TIMEFRAMES:
    import warnings
    warnings.warn(f"Invalid TIMEFRAME '{TIMEFRAME}'. Using '1m'. Valid: {VALID_TIMEFRAMES}")
    TIMEFRAME = "1m"