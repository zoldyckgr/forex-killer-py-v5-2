def analyze_market():
    pairs = {"EURUSD": "EURUSD=X", "GOLD": "GC=F"}
    for name, sym in pairs.items():
        try:
            df = yf.download(sym, period="10d", interval="15m", progress=False, auto_adjust=True)
            if df.empty: continue
            if isinstance(df.columns, pd.MultiIndex): df.columns = df.columns.get_level_values(0)

            df['RSI'] = calculate_rsi(df['Close'])
            df = get_precision_swings(df)

            # --- البحث عن أقرب سيولة "حية" (Unmitigated) ---
            recent_df = df.iloc[-400:] # نركزو على آخر 4 أيام تداول
            
            # نجبدو الـ Swings اللي مازال ما تكسروش
            fresh_highs = []
            fresh_lows = []
            
            for i in range(len(recent_df)-5):
                if not pd.isna(recent_df['Swing_High'].iloc[i]):
                    level = recent_df['Swing_High'].iloc[i]
                    # نثبتو بلي حتى شمعة موراها ما طلعت فوق هاد السعر
                    if recent_df['High'].iloc[i+1:].max() <= level:
                        fresh_highs.append(level)
                
                if not pd.isna(recent_df['Swing_Low'].iloc[i]):
                    level = recent_df['Swing_Low'].iloc[i]
                    # نثبتو بلي حتى شمعة موراها ما هبطت تحت هاد السعر
                    if recent_df['Low'].iloc[i+1:].min() >= level:
                        fresh_lows.append(level)

            if not fresh_highs or not fresh_lows: continue
            
            major_high = max(fresh_highs)
            major_low = min(fresh_lows)
            
            current = df.iloc[-1]
            
            setup = None
            # Sweep لسيولة حية (Fresh) + RSI Extreme
            if current['High'] > major_high and current['Close'] < major_high and current['RSI'] > 75:
                setup = "💎 FRESH MAJOR HIGH SWEEP"
            elif current['Low'] < major_low and current['Close'] > major_low and current['RSI'] < 25:
                setup = "💎 FRESH MAJOR LOW SWEEP"

            if setup:
                msg = (f"🚀 **{name} INTACT SIGNAL**\n\n"
                       f"🔥 Strategy: {setup}\n"
                       f"📍 Entry: `{current['Close']:.5f}`\n"
                       f"🎯 Target: `{major_low if 'HIGH' in setup else major_high:.5f}`\n"
                       f"📊 Status: Unmitigated Level Hit!")
                requests.post(f"https://api.telegram.org/bot{TOKEN}/sendMessage", data={'chat_id': CHAT_ID, 'text': msg, 'parse_mode': 'Markdown'})
        except Exception as e: print(f"Error: {e}")
