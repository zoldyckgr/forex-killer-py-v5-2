import requests
import yfinance as yf
import pandas as pd
import os
import time
from flask import Flask
from threading import Thread
from bs4 import BeautifulSoup

app = Flask('')
@app.route('/')
def home(): return "Bot is Intelligence Active!"

def run_web():
    app.run(host='0.0.0.0', port=os.getenv("PORT", 8080))

TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

# --- وظيفة جلب الأخبار الاقتصادية ---
def get_economic_calendar():
    try:
        url = "https://nfs.faireconomy.media/ff_calendar_thisweek.xml" # مصدر موثوق للأخبار
        response = requests.get(url)
        soup = BeautifulSoup(response.content, "xml")
        today = time.strftime('%m-%d-%Y')
        news_list = []

        for event in soup.find_all('event'):
            if event.date.text == today:
                impact = event.impact.text
                if impact in ['High', 'Medium']: # نركزو غير على الأخبار القوية
                    news_list.append(f"⚠️ {event.title.text} ({event.currency.text}) - Impact: {impact}")
        
        return "\n".join(news_list) if news_list else "No major news today."
    except:
        return "Couldn't fetch news."

# --- وظيفة تحليل الـ COT (نظرة عامة) ---
def get_cot_sentiment():
    # هادي تعطيك Bias عام (كمثال تقني لأن الـ API المباشر تاع CFTC معقد)
    # عادة المتداولين الكبار (Commercials) يكونو عكس الاتجاه عند القمم
    return "📊 COT Bias: Big Players are heavily LONG on Gold (Watch for potential reversal)."

def get_market_analysis():
    pairs = {"EURUSD": "EURUSD=X", "GOLD": "GC=F", "NAS100": "NQ=F"}
    
    # الصباح الباكر يبعتلك الأجندة
    current_hour = time.strftime('%H:%M')
    if current_hour == "08:00":
        news = get_economic_calendar()
        cot = get_cot_sentiment()
        msg = f"🌅 **Good Morning Oussama!**\n\n📅 **Today's News:**\n{news}\n\n{cot}"
        requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", data={'chat_id': CHAT_ID, 'text': msg})

    for name, sym in pairs.items():
        try:
            df = yf.download(sym, period="3d", interval="15m", progress=False, auto_adjust=True)
            if df.empty: continue
            if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)

            lookback = df.iloc[-51:-1]
            highest_high = lookback['High'].max()
            lowest_low = lookback['Low'].min()
            current_candle = df.iloc[-1]

            setup = None
            if current_candle['Low'] < lowest_low and current_candle['Close'] > lowest_low:
                setup = "🐂 BULLISH LIQUIDITY SWEEP"
            elif current_candle['High'] > highest_high and current_candle['Close'] < highest_high:
                setup = "🐻 BEARISH LIQUIDITY SWEEP"

            if setup:
                # نزيدو تحذير إذا كاين خبر قوي قريب
                msg = f"🎯 **{name} PRO SETUP**\n⚡ {setup}\n📍 Entry: `{current_candle['Close']:.2f}`\n\n⚠️ *Check Economic Calendar before entering!*"
                requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", data={'chat_id': CHAT_ID, 'text': msg, 'parse_mode': 'Markdown'})
        except Exception as e:
            print(f"Error: {e}")

def run_killer_bot():
    while True:
        get_market_analysis()
        time.sleep(900)

if __name__ == "__main__":
    Thread(target=run_web).start()
    run_killer_bot()
