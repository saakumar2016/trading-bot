import streamlit as st
import pandas as pd
from utils.trade_analysis import TradeAnalyzer
from utils.logger import get_logger

logger = get_logger(__name__)

st.set_page_config(page_title="Trade Analysis", page_icon="📊", layout="wide")

st.title("📊 Trade Analysis Dashboard")

analyzer = TradeAnalyzer()

if not analyzer.load_trades():
    st.warning("⚠️ No trades found. Run the bot to generate trade data.")
    st.stop()

closed_trades = analyzer.get_closed_trades()

if not closed_trades:
    st.warning("⚠️ No closed trades yet. Wait for trades to complete.")
    st.stop()

# Overall Stats
st.subheader("📈 Overall Performance")

stats = analyzer.calculate_basic_stats()

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Trades", stats.get('total_closed', 0))
col2.metric("Win Rate", f"{stats.get('win_rate', 0):.1f}%")
col3.metric("Total P&L", f"{stats.get('total_pnl', 0):.2f}")
col4.metric("Avg Win/Loss Ratio", f"{stats.get('win_loss_ratio', 0):.2f}")

col5, col6, col7, col8 = st.columns(4)
col5.metric("Wins", stats.get('wins', 0))
col6.metric("Losses", stats.get('losses', 0))
col7.metric("Avg Win", f"{stats.get('avg_win', 0):.2f}")
col8.metric("Avg Loss", f"{stats.get('avg_loss', 0):.2f}")

# By Type
st.divider()
st.subheader("🎯 Performance by Trade Type")

by_type = analyzer.analyze_by_type()

type_cols = st.columns(len(by_type))
for col, (trade_type, type_stats) in zip(type_cols, by_type.items()):
    with col:
        st.metric(f"{trade_type} Win Rate", f"{type_stats.get('win_rate', 0):.1f}%")
        st.metric(f"{trade_type} Trades", type_stats.get('count', 0))
        st.metric(f"{trade_type} P&L", f"{type_stats.get('total_pnl', 0):.2f}")

# By Trend
st.divider()
st.subheader("📊 Performance by Trend")

by_trend = analyzer.analyze_by_trend()

if by_trend:
    trend_data = []
    for trend, trend_stats in by_trend.items():
        trend_data.append({
            'Trend': trend,
            'Trades': trend_stats.get('count', 0),
            'Wins': trend_stats.get('wins', 0),
            'Win Rate %': trend_stats.get('win_rate', 0),
            'Total P&L': trend_stats.get('total_pnl', 0)
        })
    
    trend_df = pd.DataFrame(trend_data)
    st.dataframe(trend_df, use_container_width=True, hide_index=True)

# Risk/Reward Analysis
st.divider()
st.subheader("⚖️ Risk/Reward Analysis")

rr = analyzer.analyze_risk_reward()

rr_col1, rr_col2, rr_col3 = st.columns(3)
rr_col1.metric("Avg R/R Ratio", f"{rr.get('avg_rr_ratio', 0):.2f}")
rr_col2.metric("Profitable High-RR Trades", rr.get('profitable_high_rr', 0))
rr_col3.metric("Losing Low-RR Trades", rr.get('losing_low_rr', 0))

# Failure Patterns
st.divider()
st.subheader("❌ Failure Patterns")

failures = analyzer.identify_failure_patterns()

failure_data = []
for pattern in failures:
    if pattern['count'] > 0:
        failure_data.append({
            'Pattern': pattern['pattern'],
            'Count': pattern['count'],
            'Percentage': f"{(pattern['count'] / stats.get('total_closed', 1) * 100):.1f}%"
        })

if failure_data:
    failure_df = pd.DataFrame(failure_data)
    st.dataframe(failure_df, use_container_width=True, hide_index=True)
else:
    st.info("✅ No major failure patterns detected")

# Win Patterns
st.divider()
st.subheader("✅ Win Patterns")

wins = analyzer.identify_win_patterns()

win_data = []
for pattern in wins:
    if pattern['count'] > 0:
        win_data.append({
            'Pattern': pattern['pattern'],
            'Count': pattern['count'],
            'Percentage': f"{(pattern['count'] / stats.get('total_closed', 1) * 100):.1f}%"
        })

if win_data:
    win_df = pd.DataFrame(win_data)
    st.dataframe(win_df, use_container_width=True, hide_index=True)

# Suggestions
st.divider()
st.subheader("💡 Improvement Suggestions")

suggestions = analyzer.suggest_improvements()

if suggestions:
    for i, suggestion in enumerate(suggestions, 1):
        with st.expander(f"{i}. {suggestion['issue']} [{suggestion['impact']}]", expanded=(i <= 2)):
            st.write(f"**Current Value:** {suggestion['value']}")
            st.write("**Recommended Actions:**")
            for action in suggestion['actions']:
                st.write(f"• {action}")
else:
    st.success("✅ No major issues detected - System performing well!")

# Trade History
st.divider()
st.subheader("📋 Trade History")

trade_cols = ['id', 'timestamp', 'type', 'entry', 'exit_price', 'sl', 'target', 'status', 'pnl', 'trend']
display_cols = [col for col in trade_cols if col in analyzer.df.columns]

st.dataframe(analyzer.df[display_cols], use_container_width=True, hide_index=True)
