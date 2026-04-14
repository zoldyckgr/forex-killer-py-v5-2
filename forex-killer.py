import os
import time
import requests
import yfinance as yf
import pandas as pd
from flask import Flask
from threading import Thread
from bs4 import BeautifulSoup

app = Flask('')
@app.route('/')
def home(): return "Bot V5-Stable Active!"

def run_web():
    app.run(host='0.0.0.0', port=os.getenv("PORT", 8080))

TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

# --- وظيفة حساب RSI يدوياً ---
def calculate_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (100 + rs))

# --- تحديد الـ Swings الحقيقية ---
def get_precision_swings(df):
    df['Swing_High'] = df['High'][(df['High'] > df['High'].shift(1)) & (df['High'] > df['High'].shift(2)) & 
                                  (df['High'] > df['High'].shift(-1)) & (df['High'] > df['High'].shift(-2))]
    df['Swing_Low'] = df['Low'][(df['Low'] < df['Low'].shift(1)) & (df['Low'] < df['Low'].shift(2)) & 
                                 (df['Low'] < df['Low'].shift(-1)) & (df['Low'] < df['Low'].shift(-2))]
    return df

def analyze_market():
    pairs = {"EURUSD": "EURUSD=X", "GOLD": "GC=F"}
    for name, sym in pairs.items():
        try:
            df = yf.download(sym, period="5d", interval="15m", progress=False, auto_adjust=True)
            if df.empty: continue
            if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)

            # الحسابات لداخل الماركت لوب
            df['RSI'] = calculate_rsi(df['Close'])
            df = get_precision_swings(df)

            recent = df.iloc[-100:-1]
            major_high = recent['Swing_High'].max()
            major_low = recent['Swing_Low'].min()
            
            current = df.iloc[-1]
            
            setup = None
            # شروط الدخول: Sweep + RSI
            if current['High'] > major_high and current['Close'] < major_high and current['RSI'] > 70:
                setup = "🐻 BEARISH INTACT SWEEP (Eliot Wave 5/C)"
            elif current['Low'] < major_low and current['Close'] > major_low and current['RSI'] < 30:
                setup = "🐂 BULLISH INTACT SWEEP (SK Sequence Start)"

            if setup:
                msg = (f"🎯 **{name} PRECISION SETUP**\n\n"
                       f"🔥 Strategy: {setup}\n"
                       f"📍 Entry: `{current['Close']:.5f}`\n"
                       f"📉 RSI: `{current['RSI']:.2f}`\n\n"
                       f"⚠️ *Intact Liquidity Level: {major_high if 'BEARISH' in setup else major_low:.5f}*")
                requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", data={'chat_id': CHAT_ID, 'text': msg, 'parse_mode': 'Markdown'})
        except Exception as e: print(f"Error: {e}")

def main_loop():
    while True:
        analyze_market()
        time.sleep(900)

if __name__ == "__main__":
    Thread(target=run_web).start()
    main_loop()
