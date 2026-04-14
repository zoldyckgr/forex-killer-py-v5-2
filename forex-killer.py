import os
import time
import requests
import yfinance as yf
import pandas as pd
import pandas_ta as ta
from flask import Flask
from threading import Thread
from bs4 import BeautifulSoup

app = Flask('')
@app.route('/')
def home(): return "Bot V5 Precision Active!"

def run_web():
    app.run(host='0.0.0.0', port=os.getenv("PORT", 8080))

TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

# --- تحديد القمم والقيعان الحقيقية (Swing Points) ---
def get_precision_swings(df):
    # يحوس على قمة أعلى من 2 قبلها و 2 بعدها (Logic: Intact Swing)
    df['Swing_High'] = df['High'][(df['High'] > df['High'].shift(1)) & (df['High'] > df['High'].shift(2)) & 
                                  (df['High'] > df['High'].shift(-1)) & (df['High'] > df['High'].shift(-2))]
    df['Swing_Low'] = df['Low'][(df['Low'] < df['Low'].shift(1)) & (df['Low'] < df['Low'].shift(2)) & 
                                 (df['Low'] < df['Low'].shift(-1)) & (df['Low'] < df['Low'].shift(-2))]
    return df

# --- جلب تقويم الأخبار ---
def get_today_news():
    try:
        url = "https://nfs.faireconomy.media/ff_calendar_thisweek.xml"
        response = requests.get(url)
        soup = BeautifulSoup(response.content, "xml")
        today = time.strftime('%m-%d-%Y')
        news_list = []
        for event in soup.find_all('event'):
            if event.date.text == today and event.impact.text in ['High', 'Medium']:
                news_list.append(f"⚠️ {event.title.text} ({event.currency.text})")
        return "\n".join(news_list) if news_list else "No major news."
    except: return "News fetch error."

# --- التحليل الرئيسي (ICT + SK + Eliot Logic) ---
def analyze_market():
    pairs = {"EURUSD": "EURUSD=X", "GOLD": "GC=F"}
    for name, sym in pairs.items():
        try:
            # نجيبو داتا كافية للتحليل (5 أيام على فريم 15د)
            df = yf.download(sym, period="5d", interval="15m", progress=False, auto_adjust=True)
            if df.empty: continue
            if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)

            df = get_precision_swings(df)
            df['RSI'] = ta.rsi(df['Close'], length=14)

            # تركيز على Major High/Low فقط (آخر 100 شمعة)
            recent = df.iloc[-100:-1]
            major_high = recent['Swing_High'].max()
            major_low = recent['Swing_Low'].min()
            
            current = df.iloc[-1]
            prev = df.iloc[-2]

            # SK System: Fibonacci Calculation
            fib_range = major_high - major_low
            fib_618 = major_high - (fib_range * 0.618)
            
            setup = None
            # منطق Sweep الحقيقي: كسر قمة حقيقية + Rejection + RSI Confirmation
            if current['High'] > major_high and current['Close'] < major_high and current['RSI'] > 70:
                setup = "🐻 BEARISH INTACT SWEEP (Eliot Wave 5/C Exhaustion)"
            elif current['Low'] < major_low and current['Close'] > major_low and current['RSI'] < 30:
                setup = "🐂 BULLISH INTACT SWEEP (SK Sequence Start)"

            if setup:
                target = major_low if "BEARISH" in setup else major_high
                msg = (f"🎯 **{name} PRECISION SETUP**\n\n"
                       f"🔥 Strategy: {setup}\n"
                       f"📍 Entry: `{current['Close']:.5f}`\n"
                       f"🛑 Stop: `{major_high if 'BEARISH' in setup else major_low:.5f}`\n"
                       f"🎯 Target: `{target:.5f}`\n"
                       f"📉 RSI: `{current['RSI']:.2f}`\n\n"
                       f"⚠️ *Check News before entry!*")
                requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", data={'chat_id': CHAT_ID, 'text': msg, 'parse_mode': 'Markdown'})
        except Exception as e: print(f"Error analyzing {name}: {e}")

# --- التقرير الصباحي ---
def morning_report():
    news = get_today_news()
    msg = f"🌅 **Morning Oussama!**\n\n📅 **High Impact News:**\n{news}\n\n📊 *Market Status: Intact & Scanning...*"
    requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", data={'chat_id': CHAT_ID, 'text': msg})

def main_loop():
    report_sent = False
    while True:
        curr_h = time.strftime('%H:%M')
        if curr_h == "08:00" and not report_sent:
            morning_report()
            report_sent = True
        if curr_h == "00:00": report_sent = False
        
        analyze_market()
        time.sleep(900) # يسكاني كل 15 دقيقة

if __name__ == "__main__":
    Thread(target=run_web).start()
    main_loop()
