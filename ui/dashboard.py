import streamlit as st
import pandas as pd

def header():
    st.set_page_config(layout="wide")
    st.title("💀 NIFTY AI Dashboard")

def controls():
    col1, col2 = st.columns(2)

    start = col1.button("▶️ Start")
    stop = col2.button("⛔ Stop")

    return start, stop

def trade_history(trades):
    st.subheader("📜 Trades")

    if trades:
        st.dataframe(pd.DataFrame(trades))
    else:
        st.info("No trades yet")