import os
import time
import requests
import yfinance as yf
import pandas as pd
from flask import Flask
from threading import Thread

app = Flask('')
@app.route('/')
def home(): return "Bot V5.4 - Fresh Liquidity Only!"

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
    pairs = {"EURUSD": "EURUSD=X", "GOLD": "GC=F"}
    for name, sym in pairs.items():
        try:
            # نجيبو داتا تاع 3 أيام باش نلقاو الـ Structure
            df = yf.download(sym, period="3d", interval="15m", progress=False, auto_adjust=True)
            if df.empty: continue
            if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)

            df['RSI'] = calculate_rsi(df['Close'])
            
            # --- تحديد السيولة "الحية" (Unmitigated) ---
            # نحوسو على أعلى قمة وأقل قاع بشرط السعر الحالي مازال ما فاتهمش
            
            # السيولة العلوية (Buy Side Liquidity)
            potential_highs = df['High'].iloc[:-10] # نحيو آخر 10 شمعات باش ما نحكموش السعر الحالي
            major_high = potential_highs.max()
            
            # السيولة السفلية (Sell Side Liquidity)
            potential_lows = df['Low'].iloc[:-10]
            major_low = potential_lows.min()
            
            current_price = df['Close'].iloc[-1]
            current_high = df['High'].iloc[-1]
            current_low = df['Low'].iloc[-1]
            current_rsi = df['RSI'].iloc[-1]

            setup = None
            # منطق الـ Sweep: لازم يضرب القمة/القاع ويرجع يغلق تحتها/فوقها (Rejection)
            # زدنا شرط أن الـ RSI يكون "Extreme" باش نضمنو الـ Eliot Wave Exhaustion
            if current_high > major_high and current_price < major_high and current_rsi > 72:
                setup = "💎 FRESH HIGH SWEEP (ICT + ELIOT)"
            elif current_low < major_low and current_price > major_low and current_rsi < 28:
                setup = "💎 FRESH LOW SWEEP (ICT + SK)"

            if setup:
                msg = (f"🎯 **{name} INTACT SIGNAL**\n\n"
                       f"🔥 Strategy: {setup}\n"
                       f"📍 Entry: `{current_price:.5f}`\n"
                       f"📉 RSI: `{current_rsi:.2f}`\n"
                       f"🚀 Target: {'Opposite Liquidity'}")
                requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", data={'chat_id': CHAT_ID, 'text': msg, 'parse_mode': 'Markdown'})
        except Exception as e:
            print(f"Error: {e}")

def main_loop():
    while True:
        analyze_market()
        time.sleep(900)

if __name__ == "__main__":
    Thread(target=run_web).start()
    main_loop()
