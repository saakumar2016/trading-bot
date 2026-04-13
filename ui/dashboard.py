import streamlit as st
import pandas as pd
from typing import Tuple, List, Dict

def header() -> None:
    """Initialize page config and display header."""
    st.set_page_config(layout="wide")
    st.title("💀 NIFTY AI Dashboard")

def controls() -> Tuple[bool, bool]:
    """
    Display start/stop controls.
    
    Returns:
        Tuple of (start_pressed, stop_pressed)
    """
    col1, col2 = st.columns(2)

    start = col1.button("▶️ Start")
    stop = col2.button("⛔ Stop")

    return start, stop

def trade_history(trades: List[Dict]) -> None:
    """
    Display trade history.
    
    Args:
        trades: List of trade dictionaries
    """
    st.subheader("📜 Trades")

    if trades:
        st.dataframe(pd.DataFrame(trades))
    else:
        st.info("No trades yet")