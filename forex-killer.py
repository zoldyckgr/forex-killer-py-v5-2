import os
import time
import requests
import yfinance as yf
import pandas as pd
from flask import Flask
from threading import Thread

app = Flask('')
@app.route('/')
def home(): return "Bot V5.5 - Stability Fix"

def run_web():
    app.run(host='0.0.0.0', port=os.getenv("PORT", 8080))

TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

# تخزين وقت آخر سينيال لكل زوج
last_signal_time = {"EURUSD": 0, "GOLD": 0}

def calculate_rsi(series, period=14):
    # نسخة Wilder's المعتمدة عالمياً
    delta = series.diff()
    gain = (delta.where(delta > 0, 0))
    loss = (-delta.where(delta < 0, 0))
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()
    
    # تجنب القسمة على صفر
    rs = avg_gain / avg_loss.replace(0, 0.00001)
    return 100 - (100 / (100 + rs))

def analyze_market():
    global last_signal_time
    pairs = {"EURUSD": "EURUSD=X", "GOLD": "GC=F"}
    
    for name, sym in pairs.items():
        try:
            # فلتر الوقت: إذا جاز أقل من ساعة على آخر سينيال، ما تحللش هاد الزوج
            if time.time() - last_signal_time[name] < 3600:
                continue

            df = yf.download(sym, period="3d", interval="15m", progress=False, auto_adjust=True)
            if df.empty: continue
            if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)

            df['RSI'] = calculate_rsi(df['Close'])
            
            # تحديد السيولة "البعيدة" عن السعر الحالي بـ 10 شمعات
            potential_highs = df['High'].iloc[:-15]
            potential_lows = df['Low'].iloc[:-15]
            major_high = potential_highs.max()
            major_low = potential_lows.min()
            
            curr = df.iloc[-1]
            
            setup = None
            # شروط قاسية للفلترة
            if curr['High'] > major_high and curr['Close'] < major_high and 70 < curr['RSI'] < 85:
                setup = "💎 PURE BEARISH SWEEP"
            elif curr['Low'] < major_low and curr['Close'] > major_low and 15 < curr['RSI'] < 30:
                setup = "💎 PURE BULLISH SWEEP"

            if setup:
                msg = (f"🎯 **{name} STABLE SIGNAL**\n\n"
                       f"🔥 Strategy: {setup}\n"
                       f"📍 Entry: `{curr['Close']:.5f}`\n"
                       f"📉 RSI: `{curr['RSI']:.2f}`\n"
                       f"⏳ Next scan in: 1 Hour")
                
                requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", 
                             data={'chat_id': CHAT_ID, 'text': msg, 'parse_mode': 'Markdown'})
                
                last_signal_time[name] = time.time() # تحديث وقت السينيال

        except Exception as e:
            print(f"Error: {e}")

def main_loop():
    while True:
        analyze_market()
        time.sleep(300) # يسكاني كل 5 دقائق بصح يبعت كل ساعة (بسبب الفلتر)

if __name__ == "__main__":
    Thread(target=run_web).start()
    main_loop()
