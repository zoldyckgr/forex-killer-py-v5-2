import requests
import yfinance as yf
import pandas as pd
import os
import time
from flask import Flask
from threading import Thread

app = Flask('')
@app.route('/')
def home(): return "Bot is Active!"

def run_web():
    app.run(host='0.0.0.0', port=os.getenv("PORT", 8080))

TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

def get_market_analysis():
    # قائمة الأزواج اللي يهموك
    pairs = {"EURUSD": "EURUSD=X", "GOLD": "GC=F", "NAS100": "NQ=F"}
    
    for name, sym in pairs.items():
        try:
            # سحب بيانات 15 دقيقة بنطاق أوسع (3 أيام)
            df = yf.download(sym, period="3d", interval="15m", progress=False, auto_adjust=True)
            if df.empty: continue
            
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)

            # تحديد أعلى قمة وأدنى قاع في آخر 50 شمعة (باستثناء الشمعة الحالية)
            lookback = df.iloc[-51:-1]
            highest_high = lookback['High'].max()
            lowest_low = lookback['Low'].min()
            
            current_candle = df.iloc[-1]
            prev_candle = df.iloc[-2]

            setup = None
            # منطق الـ Bullish Sweep: السعر نزل تحت القاع وعاود طلع غلق فوقه
            if current_candle['Low'] < lowest_low and current_candle['Close'] > lowest_low:
                setup = "🐂 BULLISH LIQUIDITY SWEEP (Fakeout Low)"
            
            # منطق الـ Bearish Sweep: السعر طلع فوق القمة وعاود نزل غلق تحتها
            elif current_candle['High'] > highest_high and current_candle['Close'] < highest_high:
                setup = "🐻 BEARISH LIQUIDITY SWEEP (Fakeout High)"

            if setup:
                msg = f"🎯 **{name} PRO SETUP**\n\n⚡ {setup}\n📍 Entry: `{current_candle['Close']:.5f}`\n🛑 Liquidity at: `{highest_high if 'BEARISH' in setup else lowest_low:.5f}`"
                requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", 
                             data={'chat_id': CHAT_ID, 'text': msg, 'parse_mode': 'Markdown'})
                print(f"✅ Alert sent for {name}")
                
        except Exception as e:
            print(f"Error analyzing {name}: {e}")

def run_killer_bot():
    while True:
        get_market_analysis()
        time.sleep(900) # فحص كل 15 دقيقة

if __name__ == "__main__":
    Thread(target=run_web).start()
    run_killer_bot()
