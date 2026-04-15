import streamlit as st
from streamlit_autorefresh import st_autorefresh
from utils.logger import get_logger
from utils.trade_storage import (
    save_trade, load_trades, create_trade, 
    update_trades_with_price, update_trade_in_csv,
    get_trade_stats, STATUS_PENDING, has_active_trade,
    STATUS_WIN, STATUS_LOSS, STATUS_TIMEOUT
)
from utils.analysis import analyze_signal, get_analysis_text, analyze_trade_performance
from config import SYMBOL, TIMEFRAME, REFRESH_INTERVAL
from services.data_service import get_data
from services.telegram_service import (
    send_signal_alert, send_win_alert, send_loss_alert,
    send_timeout_alert, get_alert_tracker
)
from core.trend import get_trend
from core.strategy import check_signal
from core.levels import get_levels
from ui.dashboard import header, controls, trade_history
from ui.components import market_panel, signal_panel

logger = get_logger(__name__)

if "running" not in st.session_state:
    st.session_state.running = False

if st.session_state.running:
    st_autorefresh(interval=REFRESH_INTERVAL * 1000, key="refresh")

if "trades" not in st.session_state:
    st.session_state.trades = load_trades()

if "last_signal" not in st.session_state:
    st.session_state.last_signal = None

if "alerted_trades" not in st.session_state:
    st.session_state.alerted_trades = set()

if "timeframe" not in st.session_state:
    st.session_state.timeframe = TIMEFRAME

header()

st.markdown("### ⏱️ Select Timeframe")
timeframe_options = ["1m", "5m", "15m", "1h", "1d"]
selected_timeframe = st.selectbox(
    label="Select Timeframe",
    options=timeframe_options,
    index=timeframe_options.index(st.session_state.timeframe),
    key="timeframe_select"
)

if selected_timeframe != st.session_state.timeframe:
    st.session_state.timeframe = selected_timeframe
    st.rerun()

st.divider()

col1, col2, col3, col4 = st.columns(4)
col1.metric("Symbol", SYMBOL)
col2.metric("Timeframe", st.session_state.timeframe)
col3.metric("Refresh", f"{REFRESH_INTERVAL}s")
col4.metric("Status", "🟢 Running" if st.session_state.running else "🔴 Stopped")

st.divider()

start, stop = controls()

if start:
    st.session_state.running = True
    logger.info("Bot started")

if stop:
    st.session_state.running = False
    logger.info("Bot stopped")

try:
    df = get_data(SYMBOL, st.session_state.timeframe)

    if df is None:
        st.warning("⚠️ No data available")
        st.stop()

    try:
        price = round(float(df['Close'].iloc[-1]), 2)
        trend = get_trend(df)
        support, resistance = get_levels(df)
        signal = check_signal(df, trend)

        left, right = st.columns([2, 1])

        with left:
            market_panel(price, trend, support, resistance, df)

        with right:
            signal_panel(signal)

        if signal:
            st.divider()
            analysis = analyze_signal(signal)
            if analysis:
                st.text(get_analysis_text(signal))
                
                cols = st.columns(3)
                cols[0].metric("Risk Points", f"{analysis.get_risk():.2f}")
                cols[1].metric("Reward Points", f"{analysis.get_reward():.2f}")
                cols[2].metric("R/R Ratio", f"1:{analysis.get_risk_reward_ratio():.2f}")

        if signal:
            signal_id = f"{signal['type']}_{signal['entry']}"
            
            if signal_id != st.session_state.last_signal:
                if not has_active_trade(st.session_state.trades):
                    trade = create_trade(signal)
                    
                    send_signal_alert(signal, trade['id'])
                    
                    if save_trade(trade):
                        st.session_state.trades.append(trade)
                        logger.info(f"Trade: {trade['id']} - {trade['type']} @ {trade['entry']}")

                st.session_state.last_signal = signal_id
        
        st.session_state.trades, close_stats = update_trades_with_price(
            st.session_state.trades,
            price
        )

        if close_stats['closed_count'] > 0:
            for trade in st.session_state.trades:
                trade_id = trade.get('id')

                if not trade_id or trade_id in st.session_state.alerted_trades:
                    continue

                trade_status = trade.get('status')

                if trade_status == STATUS_WIN:
                    if send_win_alert(trade):
                        st.session_state.alerted_trades.add(trade_id)
                        logger.info(f"WIN: {trade_id}")
                    update_trade_in_csv(trade)

                elif trade_status == STATUS_LOSS:
                    if send_loss_alert(trade):
                        st.session_state.alerted_trades.add(trade_id)
                        logger.info(f"LOSS: {trade_id}")
                    update_trade_in_csv(trade)

                elif trade_status == STATUS_TIMEOUT:
                    if send_timeout_alert(trade):
                        st.session_state.alerted_trades.add(trade_id)
                        logger.info(f"TIMEOUT: {trade_id}")
                    update_trade_in_csv(trade)

    except Exception as e:
        st.error(f"❌ Error: {str(e)}")
        logger.error(f"Error: {str(e)}", exc_info=True)

    if st.session_state.trades:
        stats = get_trade_stats(st.session_state.trades)
        performance = analyze_trade_performance(st.session_state.trades)

        st.divider()
        st.subheader("📊 Trading Dashboard")

        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Total Trades", stats['total'])
        col2.metric("Win Rate %", f"{stats['win_rate']:.1f}")
        col3.metric("Total P&L", f"{performance['total_pnl']:.2f} pts",
                   delta="Profit" if performance['total_pnl'] > 0 else "Loss")
        col4.metric("Active Trades", stats['pending'])

        col5, col6, col7 = st.columns(3)
        col5.metric("Avg Win", f"{performance['avg_win']:.2f} pts")
        col6.metric("Avg Loss", f"{performance['avg_loss']:.2f} pts")
        col7.metric("R/R Ratio", f"{performance['risk_reward_ratio']:.2f}")

    trade_history(st.session_state.trades)

    if st.session_state.running:
        st.success(f"🟢 Running ({REFRESH_INTERVAL}s, {st.session_state.timeframe})")
    else:
        st.info(f"🔴 Stopped ({SYMBOL} {st.session_state.timeframe})")
        
except Exception as e:
    st.error(f"❌ Critical: {str(e)}")
    logger.error(f"Critical: {str(e)}", exc_info=True)
