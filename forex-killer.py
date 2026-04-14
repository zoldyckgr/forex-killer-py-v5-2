# تعويض pandas_ta بحساب يدوي بسيط للـ RSI
def calculate_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (100 + rs))

# داخل وظيفة analyze_market عدل هاد السطر:
# بدل df['RSI'] = ta.rsi(...) بـ:
df['RSI'] = calculate_rsi(df['Close'])
