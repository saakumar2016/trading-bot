import streamlit as st

def market_panel(price, trend, support, resistance, df):
    st.subheader("📊 Market")

    c1, c2, c3 = st.columns(3)
    c1.metric("Price", price)
    c2.metric("Trend", trend)
    c3.metric("Range", round(resistance - support, 2))

    st.line_chart(df['Close'].tail(100))


def signal_panel(signal):
    st.subheader("🚨 Signal")

    if signal:
        st.success(f"{signal['type']} @ {signal['entry']}")
        st.write(f"SL: {signal['sl']}")
        st.write(f"Target: {signal['target']}")
    else:
        st.info("No Signal")