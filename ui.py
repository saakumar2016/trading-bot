import streamlit as st
import pandas as pd

# ===== HEADER =====
def render_header():
    st.set_page_config(layout="wide")
    st.title("💀 NIFTY AI Trading Dashboard")

# ===== CONTROLS =====
def render_controls():
    col1, col2 = st.columns(2)

    with col1:
        start = st.button("▶️ Start Bot")

    with col2:
        stop = st.button("⛔ Stop Bot")

    return start, stop

# ===== MARKET PANEL =====
def render_market(price, trend, support, resistance, df):
    st.subheader("📊 Market")

    c1, c2, c3 = st.columns(3)
    c1.metric("Price", price)
    c2.metric("Trend", trend)
    c3.metric("Range", round(resistance - support, 2))

    st.line_chart(df['Close'].tail(100))

# ===== SIGNAL PANEL =====
def render_signal(signal):
    st.subheader("🚨 Signal")

    if signal:
        st.success(f"{signal['type']} @ {signal['entry']}")
        st.write(f"SL: {signal['sl']}")
        st.write(f"Target: {signal['target']}")
    else:
        st.info("No Signal")

# ===== TRADE HISTORY =====
def render_trade_history(trades):
    st.subheader("📜 Trade History")

    if trades:
        st.dataframe(pd.DataFrame(trades))
    else:
        st.info("No trades yet")