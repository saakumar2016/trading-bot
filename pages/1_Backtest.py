"""
Backtest Page - Analyze strategy performance on historical data
"""
import streamlit as st
import pandas as pd
from services.data_service import get_data
from utils.backtest import run_backtest, get_backtest_text_summary
from utils.logger import get_logger
from utils.performance import analyze_trade_performance

logger = get_logger(__name__)

st.set_page_config(page_title="Backtest", page_icon="📊", layout="wide")

st.title("📊 Backtest Strategy")

st.markdown("""
Run backtests to validate the trading strategy on historical data.
Analyze performance metrics and identify optimal parameters.
""")

# === Sidebar Controls ===
with st.sidebar:
    st.header("Backtest Parameters")
    
    symbol = st.text_input("Symbol", value="^NSEI")
    
    timeframe = st.selectbox(
        "Timeframe",
        options=["1m", "5m", "15m", "1h", "1d"],
        index=0
    )
    
    st.markdown("---")
    
    run_test = st.button("🚀 Run Backtest", use_container_width=True)

# === Main Content ===
if run_test:
    with st.spinner("Fetching historical data..."):
        df = get_data(symbol, timeframe)
    
    if df is None or df.empty:
        st.error(f"❌ Could not fetch data for {symbol} at {timeframe}")
    else:
        st.success(f"✅ Data loaded: {len(df)} candles from {timeframe} timeframe")
        
        with st.spinner("Running backtest..."):
            result = run_backtest(df, symbol)
        
        # === Results Display ===
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📈 Performance Summary")
            st.text(get_backtest_text_summary(result))
        
        with col2:
            st.subheader("📊 Metrics")
            metrics_df = pd.DataFrame([result.to_dict()])
            st.dataframe(metrics_df, use_container_width=True)

            performance = analyze_trade_performance(result.trades)
            st.markdown("""
            **Performance Analytics**
            """)
            perf_df = pd.DataFrame([performance])
            st.dataframe(perf_df, use_container_width=True)
        
        # === Trades Table ===
        if result.trades:
            st.subheader("📋 Trades Generated")
            
            trades_display = []
            for trade in result.trades:
                trades_display.append({
                    "Index": trade.get("index", "N/A"),
                    "Type": trade.get("type", "N/A"),
                    "Entry": f"{trade.get('entry', 0):.2f}",
                    "SL": f"{trade.get('sl', 0):.2f}",
                    "Target": f"{trade.get('target', 0):.2f}",
                    "Outcome": trade.get("outcome", "Open"),
                    "P&L": f"{trade.get('pnl', 0):.2f}" if "pnl" in trade else "N/A"
                })
            
            trades_df = pd.DataFrame(trades_display)
            st.dataframe(trades_df, use_container_width=True)
            
            # Download option
            csv = trades_df.to_csv(index=False)
            st.download_button(
                label="📥 Download Trades CSV",
                data=csv,
                file_name=f"backtest_{symbol}_{timeframe}.csv",
                mime="text/csv"
            )
        else:
            st.info("No trades generated in backtest period")

else:
    st.info("👈 Configure parameters and click 'Run Backtest' to start")
