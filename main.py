import time, requests, os, yfinance as yf, threading
from flask import Flask
app = Flask(__name__)
@app.route('/')
def home(): return "Bot is running!"
threading.Thread(target=lambda: app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 10000)))).start()
TOKEN = os.getenv("TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
def send(msg):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, data={"chat_id": CHAT_ID, "text": msg, "parse_mode": "Markdown"})
def get_signal():
    df = yf.download("GC=F", period="2d", interval="15m", progress=False)
    df.columns = [c[0] if isinstance(c, tuple) else c for c in df.columns]
    close = df['Close']
    ema9 = close.ewm(span=9).mean().iloc[-1]
    ema21 = close.ewm(span=21).mean().iloc[-1]
    ema9_prev = close.ewm(span=9).mean().iloc[-2]
    ema21_prev = close.ewm(span=21).mean().iloc[-2]
    delta = close.diff()
    gain = delta.where(delta > 0, 0).rolling(14).mean()
    loss = -delta.where(delta < 0, 0).rolling(14).mean()
    rsi = 100 - (100 / (1 + gain/loss))
    rsi_now = rsi.iloc[-1]
    price = float(close.iloc[-1])
    if ema9 > ema21 and ema9_prev <= ema21_prev and rsi_now > 50:
        return "BUY", price, price + 15, price - 10, rsi_now
    if ema9 < ema21 and ema9_prev >= ema21_prev and rsi_now < 50:
        return "SELL", price, price - 15, price + 10, rsi_now
    return None, price, 0, 0, rsi_now
send("✅ بوت الدهب خدام دابا - سكالبنج M15")
last_signal = ""
while True:
    try:
        typ, price, tp, sl, rsi = get_signal()
        if typ and typ != last_signal:
            emoji = "🟢" if typ == "BUY" else "🔴"
            msg = f"{emoji} *صفقة جديدة - GOLD SCALPING M15*\n\n📊 النوع: {typ}\n💰 الدخول: {price:.2f}\n🎯 الهدف TP: {tp:.2f}\n🛑 وقف الخسارة SL: {sl:.2f}\n📈 RSI: {rsi:.1f}"
            send(msg)
            last_signal = typ
        time.sleep(900)
    except Exception as e:
        print(e)
        time.sleep(60)
