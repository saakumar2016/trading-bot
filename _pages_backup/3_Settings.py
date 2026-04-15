"""
Settings Page - Configure bot parameters
"""
import streamlit as st

st.title("⚙️ Settings & Configuration")

st.markdown("""
Configure trading bot parameters and preferences.
Changes are made directly in the `.env` file.
""")

# === Configuration Guide ===
st.subheader("📝 Configuration Guide")

with st.expander("Trading Configuration", expanded=True):
    st.markdown("""
    **SYMBOL** - Trading symbol
    - Default: `^NSEI` (Nifty 50 Index)
    - Change to any valid stock/index symbol
    
    **TIMEFRAME** - Candle timeframe
    - Options: `1m`, `5m`, `15m`, `1h`, `1d`
    - Default: `1m`
    - Longer timeframes = fewer signals, potentially more reliable
    
    **REFRESH_INTERVAL** - Auto-refresh interval (seconds)
    - Default: `10`
    - Lower = more frequent updates (higher API usage)
    - Higher = fewer updates (less real-time)
    """)

with st.expander("Telegram Configuration", expanded=True):
    st.markdown("""
    **TELEGRAM_TOKEN** - Bot token from @BotFather
    - Get from: https://t.me/botfather
    - Create new bot and copy the token
    
    **CHAT_ID** - Your Telegram chat ID
    - Get from: https://t.me/userinfobot
    - Message the bot and it will send your ID
    
    Both are required for trade alerts to work.
    """)

with st.expander("Logging Configuration", expanded=True):
    st.markdown("""
    **LOG_LEVEL** - Logging verbosity
    - Options: `DEBUG`, `INFO`, `WARNING`, `ERROR`
    - Default: `INFO`
    - DEBUG = most verbose, ERROR = least verbose
    - Logs saved to `logs/bot.log`
    """)

# === Current Configuration ===
st.subheader("🔍 Current Configuration")

import os
from dotenv import load_dotenv

load_dotenv()

config_items = {
    "SYMBOL": os.getenv("SYMBOL", "^NSEI"),
    "TIMEFRAME": os.getenv("TIMEFRAME", "1m"),
    "REFRESH_INTERVAL": os.getenv("REFRESH_INTERVAL", "10"),
    "TELEGRAM_TOKEN": "***" if os.getenv("TELEGRAM_TOKEN") else "NOT SET",
    "CHAT_ID": os.getenv("CHAT_ID", "NOT SET"),
    "LOG_LEVEL": os.getenv("LOG_LEVEL", "INFO"),
}

col1, col2 = st.columns(2)

with col1:
    st.write("**Trading Settings:**")
    for key in ["SYMBOL", "TIMEFRAME", "REFRESH_INTERVAL"]:
        st.text(f"  {key}: {config_items[key]}")

with col2:
    st.write("**Telegram Settings:**")
    for key in ["TELEGRAM_TOKEN", "CHAT_ID"]:
        st.text(f"  {key}: {config_items[key]}")

st.write(f"**Logging:**")
st.text(f"  LOG_LEVEL: {config_items['LOG_LEVEL']}")

# === Strategy Parameters ===
st.subheader("🎯 Strategy Parameters")

st.markdown("""
These parameters are defined in the strategy modules and control signal generation behavior.
Modify them directly in the Python files for advanced tuning.

**Trend Detection** (`core/trend.py`):
- `MIN_DATA_POINTS`: 20 candles (minimum data required)
- `LOOKBACK_CANDLES`: 16 candles (comparison period)
- `THRESHOLD`: ±10 points (trend confirmation threshold)

**Support/Resistance** (`core/levels.py`):
- `LOOKBACK_PERIODS`: 80 candles (data window)
- `SAMPLE_SIZE`: 5 (average of extremes)

**Signal Generation** (`core/strategy.py`):
- `SUPPORT_BUFFER`: ±5 points (breakout buffer)
- `WICK_RATIO`: 0.8 (80% of body)
- `TARGET_MULTIPLIER`: 0.6 (60% of range)
- `SL_BUFFER`: 10 points (stop loss buffer)
""")

st.warning("""
⚠️ **Note:** Making changes to `.env` requires restarting the bot to take effect.
For Python constants, the web server must be restarted.
""")

# === File Locations ===
st.subheader("📁 Important File Locations")

st.code("""
Configuration:     /workspaces/trading-bot/.env
Logs:             /workspaces/trading-bot/logs/bot.log
Trade History:    /workspaces/trading-bot/data/trades.csv
Source Code:      /workspaces/trading-bot/

Strategy Logic:   /workspaces/trading-bot/core/
Services:         /workspaces/trading-bot/services/
UI Components:    /workspaces/trading-bot/ui/
Utilities:        /workspaces/trading-bot/utils/
""", language="bash")

# === Environment Setup ===
st.subheader("🚀 Quick Start")

with st.expander("How to Update Configuration"):
    st.markdown("""
    1. **Edit `.env` file** in the project root
    2. **Update values** for your preferences:
       ```
       SYMBOL=^NSEI
       TIMEFRAME=5m
       TELEGRAM_TOKEN=your_token
       CHAT_ID=your_chat_id
       ```
    3. **Restart the bot** for changes to take effect
    4. **Check logs** at `logs/bot.log` for any issues
    """)

st.info("""
💡 **Tip:** Start with default settings and adjust gradually based on backtest results.
Test new configurations on paper trading before live deployment.
""")
