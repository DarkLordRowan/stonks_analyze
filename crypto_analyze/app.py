import ccxt
import feedparser
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

bybit = ccxt.bybit()
bybit.load_markets()

ALL_SYMBOLS = list(bybit.markets.keys())

COINDESK_RSS_URL = "https://www.coindesk.com/arc/outboundfeeds/rss/"

@app.route('/')
def index():
    return render_template('chat_index.html')

@app.route('/search_pairs', methods=['GET'])
def search_pairs():
    query = request.args.get('q', '').strip().upper()
    if not query:
        return jsonify([])
    filtered = [sym for sym in ALL_SYMBOLS if query in sym.upper()]
    return jsonify(filtered[:50])

@app.route('/get_coin_data', methods=['GET'])
def get_coin_data():
    """
    Возвращает описание монеты + метаданные из Bybit, 
    последние новости (RSS CoinDesk), свечные данные (OHLCV).
    """
    pair = request.args.get('pair', '').strip()
    if not pair:
        return jsonify({"error": "Не указана торговая пара"})

    if pair not in ALL_SYMBOLS:
        return jsonify({"error": f"Пара {pair} не найдена на Bybit"})

    try:
        ohlcv = bybit.fetch_ohlcv(pair, timeframe='1d', limit=365)
    except Exception as e:
        return jsonify({"error": f"Ошибка получения OHLCV: {str(e)}"})

    candles = []
    for row in ohlcv:
        ts = row[0]
        op = row[1]
        hi = row[2]
        lo = row[3]
        cl = row[4]
        candles.append([ts, op, hi, lo, cl])

    description_html = f"""
    <p><b>{pair}</b> — торговая пара на бирже Bybit (данные через ccxt).</p>
    <p>Ниже указана базовая информация о рынке, полученная с Bybit:</p>
    """
    
    feed = feedparser.parse(COINDESK_RSS_URL)
    entries = feed.entries[:5] if feed.entries else []
    news_list = []
    if entries:
        for entry in entries:
            title = getattr(entry, 'title', 'Нет заголовка')
            link  = getattr(entry, 'link', '#')
            pub   = getattr(entry, 'published', '')[:16]
            news_list.append({
                "title": title,
                "date": pub,
                "link": link
            })
    else:
        news_list.append({
            "title": "Не удалось получить новости из CoinDesk RSS",
            "date": "",
            "link": "#"
        })

    return jsonify({
        "pair": pair,
        "description": description_html,
        "news": news_list,
        "candles": candles
    })

if __name__ == '__main__':
    app.run(debug=True)
