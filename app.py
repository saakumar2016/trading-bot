st.title("📊 NIFTY Smart Bot")

run = st.button("▶️ Start Bot")

if run:
    st.success("Bot Running 🚀")

    placeholder = st.empty()

    for i in range(1000):  # controlled loop

        df = get_data()

        if df is None:
            st.write("No data...")
            time.sleep(5)
            continue

        trend = get_trend(df)
        price = round(val(df['Close'].iloc[-1]), 2)
        support, resistance = get_levels(df)

        update_results(price)

        signal = check_signal(df, trend)

        # UI DISPLAY
        with placeholder.container():
            st.markdown("### 📊 Market Status")
            st.write(f"Price: {price}")
            st.write(f"Trend: {trend}")
            st.write(f"Support: {support}")
            st.write(f"Resistance: {resistance}")

        # SIGNAL
        if signal:
            signal_id = f"{signal['type']}_{signal['entry']}"

            global last_signal
            if signal_id != last_signal:

                msg = f"""
🚨 TRADE

{signal['type']}
Entry: {signal['entry']}
SL: {signal['sl']}
Target: {signal['target']}
Trend: {trend}
"""

                st.success(msg)
                send_telegram(msg)

                open_trades.append(signal)
                last_signal = signal_id

        time.sleep(10)

# import yfinance as yf
# import time
# import requests
# import csv
# import os
# from datetime import datetime

# # ===== CONFIG =====
# SYMBOL = "^NSEI"
# TELEGRAM_TOKEN = "YOUR_TOKEN"
# CHAT_ID = "5647013625"
# LOG_FILE = "trades_log.csv"

# open_trades = []
# last_signal = None

# # ===== TELEGRAM =====
# def send_telegram(msg):
#     try:
#         url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
#         requests.post(url, data={"chat_id": CHAT_ID, "text": msg}, timeout=10)
#     except:
#         print("Telegram error")

# # ===== SAFE VALUE =====
# def val(x):
#     return x.item() if hasattr(x, "item") else float(x)

# # ===== DATA =====
# def get_data():
#     df = yf.download(SYMBOL, period="2d", interval="1m", progress=False, auto_adjust=True)
#     if df is None or df.empty:
#         return None

#     df = df.dropna()

#     if hasattr(df.columns, "levels"):
#         df.columns = [c[0] if isinstance(c, tuple) else c for c in df.columns]

#     return df

# # ===== TREND =====
# def get_trend(df):
#     if len(df) < 20:
#         return "SIDEWAYS"

#     curr = val(df['Close'].iloc[-1])
#     prev = val(df['Close'].iloc[-16])

#     diff = curr - prev

#     if abs(diff) < 10:
#         return "SIDEWAYS"
#     return "UP" if diff > 0 else "DOWN"

# # ===== LEVELS =====
# def get_levels(df):
#     recent = df.tail(80)
#     support = round(recent.nsmallest(5, 'Low')['Low'].mean(), 2)
#     resistance = round(recent.nlargest(5, 'High')['High'].mean(), 2)
#     return support, resistance

# # ===== TRAILING SL =====
# def update_trailing_sl(trade, price):
#     if trade["type"].startswith("BUY"):
#         if price > trade["entry"] + 30:
#             trade["sl"] = max(trade["sl"], trade["entry"])

#     if trade["type"].startswith("SELL"):
#         if price < trade["entry"] - 30:
#             trade["sl"] = min(trade["sl"], trade["entry"])

# # ===== RESULT CHECK =====
# def update_results(price):
#     global open_trades
#     remaining = []

#     for trade in open_trades:
#         update_trailing_sl(trade, price)

#         result = None

#         if trade["type"].startswith("BUY"):
#             if price >= trade["target"]:
#                 result = "TARGET HIT"
#             elif price <= trade["sl"]:
#                 result = "SL HIT"

#         if trade["type"].startswith("SELL"):
#             if price <= trade["target"]:
#                 result = "TARGET HIT"
#             elif price >= trade["sl"]:
#                 result = "SL HIT"

#         if result:
#             send_telegram(f"✅ {result} | {trade['type']} @ {price}")

#             with open(LOG_FILE, 'a', newline='') as f:
#                 writer = csv.writer(f)
#                 writer.writerow([datetime.now(), trade["type"], trade["entry"], trade["sl"], trade["target"], result])
#         else:
#             remaining.append(trade)

#     open_trades = remaining

# # ===== SIGNAL =====
# def check_signal(df, trend):
#     signal_candle = df.iloc[-3]
#     confirm_candle = df.iloc[-2]

#     o1, h1, l1, c1 = val(signal_candle['Open']), val(signal_candle['High']), val(signal_candle['Low']), val(signal_candle['Close'])
#     o2, c2 = val(confirm_candle['Open']), val(confirm_candle['Close'])

#     body = abs(c1 - o1)
#     upper_wick = h1 - max(o1, c1)
#     lower_wick = min(o1, c1) - l1

#     support, resistance = get_levels(df)

#     # ===== VOLATILITY FILTER =====
#     recent_range = df.tail(20)['High'].max() - df.tail(20)['Low'].min()
#     if recent_range < 30:
#         return None

#     range_size = resistance - support

#     # ===== BUY =====
#     if trend in ["UP", "SIDEWAYS"]:
#         if l1 < support - 5 and c1 > support and lower_wick > body * 0.8 and c2 > o2:
#             entry = round(c2, 2)
#             return {
#                 "type": "BUY CONFIRMED",
#                 "entry": entry,
#                 "sl": round(l1 - 10, 2),
#                 "target": round(entry + (range_size * 0.6), 2),
#                 "support": support,
#                 "resistance": resistance
#             }

#     # ===== SELL =====
#     if trend in ["DOWN", "SIDEWAYS"]:
#         if h1 > resistance + 5 and c1 < resistance and upper_wick > body * 0.8 and c2 < o2:
#             entry = round(c2, 2)
#             return {
#                 "type": "SELL CONFIRMED",
#                 "entry": entry,
#                 "sl": round(h1 + 10, 2),
#                 "target": round(entry - (range_size * 0.6), 2),
#                 "support": support,
#                 "resistance": resistance
#             }

#     return None

# # ===== START =====
# print("🚀 PRO BOT RUNNING...\n")
# send_telegram("🚀 PRO BOT STARTED")

# # ===== LOOP =====
# while True:
#     try:
#         df = get_data()

#         if df is None:
#             print("No data...")
#             time.sleep(30)
#             continue

#         trend = get_trend(df)
#         price = round(val(df['Close'].iloc[-1]), 2)

#         support, resistance = get_levels(df)

#         update_results(price)

#         signal = check_signal(df, trend)

#         print(f"""
# 📊 MARKET
# Price: {price}
# Trend: {trend}
# Support: {support}
# Resistance: {resistance}
# """)

#         if signal:
#             signal_id = f"{signal['type']}_{signal['entry']}"

#             if signal_id != last_signal:
#                 msg = f"""
# 🚨 TRADE

# {signal['type']}
# Entry: {signal['entry']}
# SL: {signal['sl']}
# Target: {signal['target']}
# Trend: {trend}
# """
#                 print(msg)
#                 send_telegram(msg)

#                 open_trades.append(signal)

#                 with open(LOG_FILE, 'a', newline='') as f:
#                     writer = csv.writer(f)
#                     writer.writerow([datetime.now(), signal["type"], signal["entry"], signal["sl"], signal["target"], "OPEN"])

#                 last_signal = signal_id

#         time.sleep(60)

#     except Exception as e:
#         print("Error:", e)
#         time.sleep(30)