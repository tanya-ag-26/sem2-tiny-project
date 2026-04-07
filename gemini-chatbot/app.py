from flask import Flask, request, jsonify, render_template
from dotenv import load_dotenv
from google import genai
import requests
import os
import re

load_dotenv()

app = Flask(__name__)

client = genai.Client(api_key=os.getenv("GENAI_API_KEY"))


conversations = {}




# @app.route("/")
# def index():
#     return render_template("index.html")


# ── Does this message need live data? ────────────────────────────────────────
def needs_search(message):
    message = message.lower()

    # Real-time indicators
    realtime_keywords = [
        "price", "weather", "news", "today", "latest", "current",
        "stock", "rate", "temperature"
    ]

    # Always trigger for crypto keywords
    crypto_keywords = ["bitcoin", "btc", "ethereum", "eth"]

    if any(k in message for k in crypto_keywords):
        return True

    if any(k in message for k in realtime_keywords):
        return True

    return False

# ── Real-time crypto price (CoinGecko) ───────────────────────────────────────
def get_crypto_price(query):
    query = query.lower()
    if "bitcoin" in query:
        url = "https://api.coingecko.com/api/v3/simple/price"
        params = {
            "ids": "bitcoin",
            "vs_currencies": "usd,inr"
        }
        data = requests.get(url, params=params).json()
        price_usd = data["bitcoin"]["usd"]
        price_inr = data["bitcoin"]["inr"]
        return f"Bitcoin price: ${price_usd} USD (₹{price_inr} INR)"
    elif "ethereum" in query or "eth" in query:
        url = "https://api.coingecko.com/api/v3/simple/price"
        params = {
            "ids": "ethereum",
            "vs_currencies": "usd,inr"
        }
        data = requests.get(url, params=params).json()
        price_usd = data["ethereum"]["usd"]
        price_inr = data["ethereum"]["inr"]
        return f"Ethereum price: ${price_usd} USD (₹{price_inr} INR)"
    return ""

# ── Weather API (OpenWeatherMap) ───────────────────────────────────────────
def get_weather(query):
    city_match = re.search(r'weather in (\w+)', query.lower())
    city = city_match.group(1) if city_match else "Delhi"

    url = "http://api.openweathermap.org/data/2.5/weather"
    params = {
        "q": city,
        "appid": os.getenv("OPENWEATHER_API_KEY"),
        "units": "metric"
    }
    data = requests.get(url, params=params).json()

    if data.get("main"):
        temp = data["main"]["temp"]
        desc = data["weather"][0]["description"]
        return f"Weather in {city.title()}: {temp}°C, {desc}"
    return "Weather data not available."

# ── News API (NewsAPI) ──────────────────────────────────────────────────────
def get_news(query):
    url = "https://newsapi.org/v2/everything"
    params = {
        "q": query,
        "apiKey": os.getenv("NEWS_API_KEY"),
        "language": "en",
        "pageSize": 5,
        "sortBy": "publishedAt"
    }
    data = requests.get(url, params=params).json()

    articles = data.get("articles", [])
    if not articles:
        return "No news found."

    headlines = [f"- {a['title']}" for a in articles]
    return "Latest news:\n" + "\n".join(headlines)

# ── Stock API (Finnhub free API) ───────────────────────────────────────────
def get_stock_price(query):
    symbol_match = re.search(r'stock (\w+)', query.lower())
    symbol = symbol_match.group(1).upper() if symbol_match else "AAPL"

    url = "https://finnhub.io/api/v1/quote"
    params = {
        "symbol": symbol,
        "token": os.getenv("FINNHUB_API_KEY")
    }
    data = requests.get(url, params=params).json()
    if data.get("c"):
        current_price = data["c"]
        return f"Current price of {symbol}: ${current_price}"
    return "Stock data not available."

# ── Search Google / DuckDuckGo ─────────────────────────────────────────────
def google_search(query):
    url = "https://api.duckduckgo.com/"
    params = {
        "q": query,
        "format": "json",
        "no_html": 1
    }

    response = requests.get(url, params=params)
    data = response.json()

    results = []

    if data.get("AbstractText"):
        results.append(data["AbstractText"])
    if data.get("Heading"):
        results.append(data["Heading"])
    for topic in data.get("RelatedTopics", []):
        if isinstance(topic, dict):
            if "Text" in topic:
                results.append(topic["Text"])
            elif "Topics" in topic:
                for sub in topic.get("Topics", []):
                    if "Text" in sub:
                        results.append(sub["Text"])

    return "\n".join(results[:5])

# ── Unified live data handler ──────────────────────────────────────────────
def get_live_data(user_msg):
    user_msg_lower = user_msg.lower()
    if any(k in user_msg_lower for k in ["bitcoin", "btc", "ethereum", "eth"]):
        return get_crypto_price(user_msg)
    elif "weather" in user_msg_lower:
        return get_weather(user_msg)
    elif "news" in user_msg_lower:
        return get_news(user_msg)
    elif "stock" in user_msg_lower:
        return get_stock_price(user_msg)
    else:
        return google_search(user_msg)

# ── Chat route ─────────────────────────────────────────────────────────────
@app.route("/chat", methods=["POST"])
def chat():
    data       = request.get_json()
    session_id = data.get("session_id", "default")
    user_msg   = data.get("message", "")

    if session_id not in conversations:
        conversations[session_id] = []

    history = conversations[session_id]

    # Build history text
    history_text = ""
    for msg in history:
        if msg["role"] == "user":
            history_text += f"User: {msg['content']}\n"
        else:
            history_text += f"Assistant: {msg['content']}\n"

    # Check if live search is needed
    search_context = ""
    search_used    = False
    if needs_search(user_msg):
        results = get_live_data(user_msg)

        if results.strip():
            search_context = f"\n[Live search results]\n{results}\n"
            search_used = True
        else:
            search_context = "\n[No live data found, answer from knowledge]\n"
            search_used = False

    # Build full prompt
    if search_used:
        system_instruction = (
            "You are a helpful assistant. Use the provided live search results to answer accurately."
        )
    else:
        system_instruction = (
            "You are a helpful assistant. If live data is not available, answer using general knowledge "
            "without mentioning missing search results."
        )

    prompt = (
        system_instruction + "\n\n"
        + history_text
        + search_context
        + f"User: {user_msg}\nAssistant:"
    )

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        reply = response.text.strip()
    except Exception as e:
        return jsonify({"error": str(e)}), 200

    history.append({"role": "user",      "content": user_msg})
    history.append({"role": "assistant", "content": reply})

    return jsonify({"reply": reply, "search_used": search_used})

if __name__ == "__main__":
    app.run(debug=True, port=5000)













