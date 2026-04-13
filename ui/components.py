import streamlit as st
import pandas as pd
from typing import Optional, Dict

def market_panel(
    price: float,
    trend: str,
    support: float,
    resistance: float,
    df: pd.DataFrame
) -> None:
    """
    Display market analysis panel.
    
    Args:
        price: Current price
        trend: Current trend
        support: Support level
        resistance: Resistance level
        df: OHLC data
    """
    st.subheader("📊 Market")

    c1, c2, c3 = st.columns(3)
    c1.metric("Price", price)
    c2.metric("Trend", trend)
    c3.metric("Range", round(resistance - support, 2))

    st.line_chart(df['Close'].tail(100))


def signal_panel(signal: Optional[Dict]) -> None:
    """
    Display trading signal panel.
    
    Args:
        signal: Signal dictionary or None
    """
    st.subheader("🚨 Signal")

    if signal:
        st.success(f"{signal['type']} @ {signal['entry']}")
        st.write(f"SL: {signal['sl']}")
        st.write(f"Target: {signal['target']}")
    else:
        st.info("No Signal")