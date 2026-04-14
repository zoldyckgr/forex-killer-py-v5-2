import os
import time
import requests
import yfinance as yf
import pandas as pd
from flask import Flask
from threading import Thread

app = Flask('')
@app.route('/')
def home(): return "Bot V5.3 Intact & Live!"

def run_web():
    app.run(host='0.0.0.0', port=os.getenv("PORT", 8080))

TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

def calculate_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (100 + rs))

def analyze_market():
    # ركزنا غير على EURUSD والذهب باش يكون دقيق
    pairs = {"EURUSD": "EURUSD=X", "GOLD": "GC=F"}
    for name, sym in pairs.items():
        try:
            # نجبدو داتا تاع آخر 48 ساعة فقط (باش ما يروحش للقديم)
            df = yf.download(sym, period="2d", interval="15m", progress=False, auto_adjust=True)
            if df.empty: continue
            if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)

            df['RSI'] = calculate_rsi(df['Close'])
            
            # تحديد السيولة تاع البارح (Previous Day High/Low)
            # هادي هي السيولة اللي يحترمها الـ ICT صح
            major_high = df['High'].iloc[:-20].max() # أعلى قمة قبل الساعات الأخيرة
            major_low = df['Low'].iloc[:-20].min()   # أقل قاع قبل الساعات الأخيرة
            
            current_price = df['Close'].iloc[-1]
            current_high = df['High'].iloc[-1]
            current_low = df['Low'].iloc[-1]
            current_rsi = df['RSI'].iloc[-1]

            setup = None
            # شرط الـ Sweep: لازم يضرب قمة البارح ويرجع تحتها + RSI
            if current_high > major_high and current_price < major_high and current_rsi > 70:
                setup = "🐻 BEARISH SWEEP (Previous Day High)"
            elif current_low < major_low and current_price > major_low and current_rsi < 30:
                setup = "🐂 BULLISH SWEEP (Previous Day Low)"

            if setup:
                msg = (f"💎 **{name} INTACT SIGNAL**\n\n"
                       f"🔥 Type: {setup}\n"
                       f"📍 Entry: `{current_price:.5f}`\n"
                       f"📉 RSI: `{current_rsi:.2f}`\n"
                       f"🛡️ Target: {'Previous Day Low' if 'BEARISH' in setup else 'Previous Day High'}")
                requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", data={'chat_id': CHAT_ID, 'text': msg, 'parse_mode': 'Markdown'})
        except Exception as e:
            print(f"Error analyzing {name}: {e}")

def main_loop():
    while True:
        analyze_market()
        time.sleep(900) # يسكاني كل 15 دقيقة

if __name__ == "__main__":
    Thread(target=run_web).start()
    main_loop()
