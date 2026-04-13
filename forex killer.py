import requests
import yfinance as yf
import pandas as pd
import mplfinance as mpf
import pytz
from datetime import datetime
import time
import os
from flask import Flask
from threading import Thread

# --- سيرفر وهمي لإبقاء السيرفر حياً في الخطة المجانية ---
app = Flask('')

@app.route('/')
def home():
    return "Bot is Running 24/7!"

def run_web():
    app.run(host='0.0.0.0', port=os.getenv("PORT", 8080))

# --- إعدادات البوت ---
TOKEN = os.getenv('TELEGRAM_TOKEN', "8683911369:AAG1_9AIuUJUVRlL2pyh_sYGtXYSzESbYwc")
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', "941661354")

def sanitize_df(df):
    if df is None or df.empty: return None
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)
    return df

def get_market_analysis():
    pairs = {"EURUSD": "EURUSD=X", "GOLD": "GC=F", "NAS100": "NQ=F"}
    for name, sym in pairs.items():
        try:
            df = sanitize_df(yf.download(sym, period="2d", interval="15m", progress=False, auto_adjust=True))
            if df is None: continue
            curr_close = float(df['Close'].iloc[-1])
            low_liq = float(df['Low'].iloc[-30:-5].min())
            high_liq = float(df['High'].iloc[-30:-5].max())
            
            setup = None
            if float(df['Low'].iloc[-1]) < low_liq and curr_close > low_liq:
                setup = "🔥 BULLISH SWEEP"
            elif float(df['High'].iloc[-1]) > high_liq and curr_close < high_liq:
                setup = "🔥 BEARISH SWEEP"
                
            if setup:
                report = f"🎯 **{name} SETUP**\n⚡ `{setup}`\n📍 Price: `{curr_close:.5f}`"
                requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", data={'chat_id': CHAT_ID, 'text': report, 'parse_mode': 'Markdown'})
        except: continue

def run_killer_bot():
    print("🚀 Forensic Bot is LIVE on Render Free Tier!")
    while True:
        get_market_analysis()
        time.sleep(900)

if __name__ == "__main__":
    # تشغيل السيرفر الوهمي في Background
    t = Thread(target=run_web)
    t.start()
    # تشغيل البوت
    run_killer_bot()