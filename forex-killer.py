import os
import time
import requests
import yfinance as yf
import pandas as pd
from flask import Flask
from threading import Thread

app = Flask('')
@app.route('/')
def home(): return "Bot V6.0 - All Fixed & Precision RR Active"

def run_web():
    # استعمال بورت 10000 الافتراضي لـ Render لتفادي أخطاء الربط
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

last_signal_time = {"EURUSD": 0, "GOLD": 0}

def calculate_rsi(series, period=14):
    # معادلة RSI احترافية (Wilder's Smoothing) لتفادي أرقام الـ 99 الغالطة
    delta = series.diff()
    gain = (delta.where(delta > 0, 0))
    loss = (-delta.where(delta < 0, 0))
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()
    rs = avg_gain / avg_loss.replace(0, 0.00001)
    return 100 - (100 / (100 + rs))

def analyze_market():
    global last_signal_time
    pairs = {"EURUSD": "EURUSD=X", "GOLD": "GC=F"}
    
    for name, sym in pairs.items():
        try:
            # فلتر ساعة بين السينيالات لتفادي السبام
            if time.time() - last_signal_time[name] < 3600:
                continue

            df = yf.download(sym, period="4d", interval="15m", progress=False, auto_adjust=True)
            if df.empty: continue
            if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)

            df['RSI'] = calculate_rsi(df['Close'])
            
            # تحديد سيولة آخر 48 ساعة (بدون الشمعات الحالية)
            structure_df = df.iloc[:-10]
            major_high = structure_df['High'].max()
            major_low = structure_df['Low'].min()
            
            curr = df.iloc[-1]
            entry_p = curr['Close']
            
            setup = None
            sl, tp = 0, 0

            # منطق الـ Sweep + RSI (من 15 لـ 30 ومن 70 لـ 85)
            if curr['High'] > major_high and curr['Close'] < major_high and 70 < curr['RSI'] < 85:
                setup = "🐻 BEARISH INTACT SWEEP"
                sl = curr['High'] + (0.00015 if name == "EURUSD" else 0.8)
                tp = entry_p - ((sl - entry_p) * 5) # هدف 1:5
                
            elif curr['Low'] < major_low and curr['Close'] > major_low and 15 < curr['RSI'] < 35:
                setup = "🐂 BULLISH INTACT SWEEP"
                sl = curr['Low'] - (0.00015 if name == "EURUSD" else 0.8)
                tp = entry_p + ((entry_p - sl) * 5) # هدف 1:5

            if setup:
                msg = (f"🛡️ **{name} INTACT SETUP**\n\n"
                       f"🔥 Strategy: {setup}\n"
                       f"📍 **ENTRY: `{entry_p:.5f}`**\n"
                       f"🛑 **SL: `{sl:.5f}`**\n"
                       f"✅ **TP (1:5 RR): `{tp:.5f}`**\n\n"
                       f"📉 RSI: `{curr['RSI']:.2f}`")
                
                requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", 
                             data={'chat_id': CHAT_ID, 'text': msg, 'parse_mode': 'Markdown'})
                
                last_signal_time[name] = time.time()

        except Exception as e:
            print(f"Error in {name}: {e}")

def main_loop():
    while True:
        analyze_market()
        time.sleep(300) # فحص كل 5 دقائق

if __name__ == "__main__":
    t = Thread(target=run_web)
    t.daemon = True
    t.start()
    main_loop()
