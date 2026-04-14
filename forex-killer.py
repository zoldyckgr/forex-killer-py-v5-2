import os
import time
import requests
import yfinance as yf
import pandas as pd
from flask import Flask
from threading import Thread

app = Flask('')
@app.route('/')
def home(): return "Bot V5.7 - All Fixed & Precision 1:5 RR"

def run_web():
    # سقمنا هاد السطر باش ما يصرى حتى Conflict في الـ Port
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

last_signal_time = {"EURUSD": 0, "GOLD": 0}

def calculate_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0))
    loss = (-delta.where(delta < 0, 0))
    # الطريقة الصحيحة (Wilder's Smoothing)
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()
    rs = avg_gain / avg_loss.replace(0, 0.00001)
    return 100 - (100 / (100 + rs))

def analyze_market():
    global last_signal_time
    pairs = {"EURUSD": "EURUSD=X", "GOLD": "GC=F"}
    
    for name, sym in pairs.items():
        try:
            # فلتر ساعة بين كل سينيال وسينيال
            if time.time() - last_signal_time[name] < 3600:
                continue

            df = yf.download(sym, period="3d", interval="15m", progress=False, auto_adjust=True)
            if df.empty: continue
            if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)

            df['RSI'] = calculate_rsi(df['Close'])
            
            # سيولة الـ 48 ساعة الماضية (Fresh High/Low)
            potential_highs = df['High'].iloc[:-15]
            potential_lows = df['Low'].iloc[:-15]
            major_high = potential_highs.max()
            major_low = potential_lows.min()
            
            curr = df.iloc[-1]
            entry_price = curr['Close']

            setup = None
            sl = 0
            tp = 0

            # الـ Logic تع الـ Sweep والـ 1:5 RR
            if curr['High'] > major_high and curr['Close'] < major_high and 70 < curr['RSI'] < 85:
                setup = "🐻 BEARISH INTACT SWEEP"
                sl = curr['High'] + (0.00015 if name == "EURUSD" else 0.8)
                risk = sl - entry_price
                tp = entry_price - (risk * 5)
                
            elif curr['Low'] < major_low and curr['Close'] > major_low and 15 < curr['RSI'] < 30:
                setup = "🐂 BULLISH INTACT SWEEP"
                sl = curr['Low'] - (0.00015 if name == "EURUSD" else 0.8)
                risk = entry_price - sl
                tp = entry_price + (risk * 5)

            if setup:
                msg = (f"🎯 **{name} PRECISION SETUP**\n\n"
                       f"🔥 Strategy: {setup}\n"
                       f"📍 **ENTRY: `{entry_price:.5f}`**\n"
                       f"🛑 **SL: `{sl:.5f}`**\n"
                       f"✅ **TP (1:5): `{tp:.5f}`**\n\n"
                       f"📉 RSI: `{curr['RSI']:.2f}`\n"
                       f"📊 Check structural rejection on 15M.")
                
                requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", 
                             data={'chat_id': CHAT_ID, 'text': msg, 'parse_mode': 'Markdown'})
                
                last_signal_time[name] = time.time()

        except Exception as e:
            print(f"Error: {e}")

def main_loop():
    while True:
        analyze_market()
        time.sleep(300)

if __name__ == "__main__":
    Thread(target=run_web).start()
    main_loop()
