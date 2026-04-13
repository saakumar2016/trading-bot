"""
Analysis Page - Real-time risk/reward and signal analysis
"""
import streamlit as st
import pandas as pd
from services.data_service import get_data
from core.trend import get_trend
from core.levels import get_levels
from core.strategy import check_signal
from utils.analysis import analyze_signal, get_analysis_text
from utils.logger import get_logger

logger = get_logger(__name__)

st.set_page_config(page_title="Analysis", page_icon="📈", layout="wide")

st.title("📈 Signal Analysis")

st.markdown("""
Analyze trading signals with detailed risk/reward metrics.
Understand the quality and probability of each trade setup.
""")

# === Sidebar Controls ===
with st.sidebar:
    st.header("Analysis Parameters")
    
    symbol = st.text_input("Symbol", value="^NSEI")
    
    timeframe = st.selectbox(
        "Timeframe",
        options=["1m", "5m", "15m", "1h", "1d"],
        index=0
    )
    
    st.markdown("---")
    
    analyze_btn = st.button("🔍 Analyze Signal", use_container_width=True)

# === Main Content ===
if analyze_btn:
    with st.spinner("Fetching latest data..."):
        df = get_data(symbol, timeframe)
    
    if df is None or df.empty:
        st.error(f"❌ Could not fetch data for {symbol} at {timeframe}")
    else:
        try:
            # Calculate metrics
            current_price = float(df['Close'].iloc[-1])
            trend = get_trend(df)
            support, resistance = get_levels(df)
            signal = check_signal(df, trend)
            
            # === Current Market Status ===
            st.subheader("📊 Current Market Status")
            
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Price", f"{current_price:.2f}")
            col2.metric("Trend", f"🟢 {trend}" if trend == "UP" else "🔴 DOWN" if trend == "DOWN" else "⚫ SIDEWAYS")
            col3.metric("Support", f"{support:.2f}")
            col4.metric("Resistance", f"{resistance:.2f}")
            
            # === Signal Analysis ===
            if signal:
                st.success("✅ SIGNAL DETECTED")
                
                # Display signal details
                col1, col2 = st.columns(2)
                
                with col1:
                    st.subheader("🎯 Trade Setup")
                    st.write(f"**Type:** {signal['type']}")
                    st.write(f"**Entry:** {signal['entry']:.2f}")
                    st.write(f"**Stop Loss:** {signal['sl']:.2f}")
                    st.write(f"**Target:** {signal['target']:.2f}")
                
                with col2:
                    st.subheader("📍 Levels")
                    st.write(f"**Support:** {signal.get('support', support):.2f}")
                    st.write(f"**Resistance:** {signal.get('resistance', resistance):.2f}")
                    st.write(f"**Trend:** {signal.get('trend', trend)}")
                
                # === Risk/Reward Analysis ===
                analysis = analyze_signal(signal)
                if analysis:
                    st.subheader("💰 Risk/Reward Analysis")
                    
                    col1, col2, col3, col4, col5 = st.columns(5)
                    col1.metric("Risk", f"{analysis.get_risk():.2f}")
                    col2.metric("Reward", f"{analysis.get_reward():.2f}")
                    
                    rr = analysis.get_risk_reward_ratio()
                    col3.metric("R/R Ratio", f"1:{rr:.2f}", delta="Good" if rr >= 2 else "Fair" if rr >= 1.5 else "Poor")
                    
                    breakeven = analysis.get_breakeven_win_rate()
                    col4.metric("Breakeven %", f"{breakeven:.1f}%", delta="Good" if breakeven < 40 else "Fair" if breakeven < 50 else "Poor")
                    
                    quality = analysis.get_position_quality_score()
                    col5.metric("Quality", f"{quality:.0f}/100", delta=analysis.get_quality_rating())
                    
                    # Full analysis text
                    st.text(get_analysis_text(signal))
                    
                    # Metrics table
                    st.subheader("📋 Detailed Metrics")
                    metrics_df = pd.DataFrame([analysis.to_dict()])
                    st.dataframe(metrics_df, use_container_width=True)
            else:
                st.info("⏳ No signal currently (waiting for pattern confirmation)")
        
        except Exception as e:
            st.error(f"❌ Error analyzing signal: {str(e)}")
            logger.error(f"Analysis error: {str(e)}", exc_info=True)

else:
    st.info("👈 Configure parameters and click 'Analyze Signal' to start")
