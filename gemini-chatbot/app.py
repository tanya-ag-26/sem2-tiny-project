from flask import Flask, request, jsonify, render_template
from dotenv import load_dotenv
from google import genai
import requests
import json
import os
import re
from datetime import datetime

# ═══════════════════════════════════════════════════════
#  FILE PATHS
# ═══════════════════════════════════════════════════════
CHAT_FILE  = "chat_history.json"
USERS_FILE = "users.json"

# ═══════════════════════════════════════════════════════
#  JSON HELPERS
# ═══════════════════════════════════════════════════════
def load_chat_history():
    if not os.path.exists(CHAT_FILE):
        return {}
    with open(CHAT_FILE, "r") as f:
        return json.load(f)

def save_chat_history(data):
    with open(CHAT_FILE, "w") as f:
        json.dump(data, f, indent=4)

def load_users():
    if not os.path.exists(USERS_FILE):
        return []
    with open(USERS_FILE, "r") as f:
        return json.load(f)

def save_users(data):
    with open(USERS_FILE, "w") as f:
        json.dump(data, f, indent=4)

# ═══════════════════════════════════════════════════════
#  STARTUP
# ═══════════════════════════════════════════════════════
load_dotenv()

app = Flask(__name__)

client = genai.Client(api_key=os.getenv("GENAI_API_KEY"))

# Load persisted chat history on startup
conversations = load_chat_history()

# ═══════════════════════════════════════════════════════
#  TOPICS  (rendered on home screen)
# ═══════════════════════════════════════════════════════
TOPICS = [
    {"id": "finance",     "label": "Finance",   "icon": "💰"},
    {"id": "health",      "label": "Health",    "icon": "🏥"},
    {"id": "development", "label": "Dev",       "icon": "💻"},
    {"id": "business",    "label": "Business",  "icon": "📊"},
    {"id": "science",     "label": "Science",   "icon": "🔬"},
    {"id": "education",   "label": "Education", "icon": "📚"},
    {"id": "travel",      "label": "Travel",    "icon": "✈️"},
    {"id": "food",        "label": "Food",      "icon": "🍜"},
]

# ═══════════════════════════════════════════════════════
#  HISTORY HELPER — builds recent items from chat_history.json
# ═══════════════════════════════════════════════════════
def build_recent_history(limit=5):
    """
    Flatten all sessions, pick the most recent user messages,
    and return them formatted for the home screen history list.
    """
    all_msgs = []

    for session_id, msgs in conversations.items():
        for msg in msgs:
            if msg["role"] == "user":
                all_msgs.append({
                    "question":  msg["content"],
                    "timestamp": msg.get("timestamp", ""),
                    "session":   session_id,
                })

    # Sort newest-first (ISO timestamps sort lexicographically)
    all_msgs.sort(key=lambda x: x["timestamp"], reverse=True)

    # Format a human-readable display time
    result = []
    now = datetime.utcnow()
    for item in all_msgs[:limit]:
        ts_str = item.get("timestamp", "")
        try:
            ts   = datetime.fromisoformat(ts_str)
            diff = now - ts
            if diff.days == 0 and diff.seconds < 3600:
                display = f"{diff.seconds // 60} mins ago"
            elif diff.days == 0:
                display = f"{diff.seconds // 3600} hrs ago"
            elif diff.days == 1:
                display = "Yesterday"
            else:
                display = f"{diff.days} days ago"
        except Exception:
            display = "Recently"

        result.append({"question": item["question"], "time": display})

    # Fallback placeholders when no real history exists yet
    if not result:
        result = [
            {"question": "What is compound interest?",         "time": "Example"},
            {"question": "How to build a REST API in Python?", "time": "Example"},
            {"question": "Best diet for muscle gain?",         "time": "Example"},
        ]

    return result


# ═══════════════════════════════════════════════════════
#  ROUTE — home page
# ═══════════════════════════════════════════════════════
@app.route("/")
def index():
    history = build_recent_history()
    return render_template("index.html", topics=TOPICS, history=history)


# ═══════════════════════════════════════════════════════
#  ROUTE — /save-user  (called from login screen)
# ═══════════════════════════════════════════════════════
@app.route("/save-user", methods=["POST"])
def save_user():
    data  = request.get_json(silent=True) or {}
    name  = data.get("name",  "").strip()
    email = data.get("email", "").strip()

    if not name:
        return jsonify({"error": "Name is required"}), 400

    users = load_users()

    # Update existing entry if email matches, otherwise add new
    existing = next((u for u in users if u.get("email") == email), None)
    if existing:
        existing["name"]       = name
        existing["last_login"] = datetime.utcnow().isoformat()
    else:
        users.append({
            "name":       name,
            "email":      email,
            "joined":     datetime.utcnow().isoformat(),
            "last_login": datetime.utcnow().isoformat(),
        })

    save_users(users)
    return jsonify({"status": "ok", "name": name})


# ═══════════════════════════════════════════════════════
#  LIVE DATA — keyword detection
# ═══════════════════════════════════════════════════════
def needs_search(message):
    message = message.lower()
    realtime_keywords = [
        "price", "weather", "news", "today", "latest", "current",
        "stock", "rate", "temperature"
    ]
    crypto_keywords = ["bitcoin", "btc", "ethereum", "eth"]

    if any(k in message for k in crypto_keywords):
        return True
    if any(k in message for k in realtime_keywords):
        return True
    return False


# ═══════════════════════════════════════════════════════
#  LIVE DATA — API fetchers
# ═══════════════════════════════════════════════════════
def get_crypto_price(query):
    query = query.lower()
    try:
        if "bitcoin" in query or "btc" in query:
            url    = "https://api.coingecko.com/api/v3/simple/price"
            params = {"ids": "bitcoin", "vs_currencies": "usd,inr"}
            data   = requests.get(url, params=params).json()
            return f"Bitcoin price: ${data['bitcoin']['usd']} USD (₹{data['bitcoin']['inr']} INR)"
        elif "ethereum" in query or "eth" in query:
            url    = "https://api.coingecko.com/api/v3/simple/price"
            params = {"ids": "ethereum", "vs_currencies": "usd,inr"}
            data   = requests.get(url, params=params).json()
            return f"Ethereum price: ${data['ethereum']['usd']} USD (₹{data['ethereum']['inr']} INR)"
        return ""
    except Exception:
        return "(Mock API response due to SSL/API error)"


def get_weather(query):
    city_match = re.search(r'weather in (\w+)', query.lower())
    city   = city_match.group(1) if city_match else "Delhi"
    url    = "http://api.openweathermap.org/data/2.5/weather"
    params = {
        "q":     city,
        "appid": os.getenv("OPENWEATHER_API_KEY"),
        "units": "metric"
    }
    try:
        data = requests.get(url, params=params).json()
        if data.get("main"):
            temp = data["main"]["temp"]
            desc = data["weather"][0]["description"]
            return f"Weather in {city.title()}: {temp}°C, {desc}"
        return "Weather data not available."
    except Exception:
        return "(Mock API response due to SSL/API error)"


def get_news(query):
    url    = "https://newsapi.org/v2/everything"
    params = {
        "q":        query,
        "apiKey":   os.getenv("NEWS_API_KEY"),
        "language": "en",
        "pageSize": 5,
        "sortBy":   "publishedAt"
    }
    try:
        data     = requests.get(url, params=params).json()
        articles = data.get("articles", [])
        if not articles:
            return "No news found."
        headlines = [f"- {a['title']}" for a in articles]
        return "Latest news:\n" + "\n".join(headlines)
    except Exception:
        return "(Mock API response due to SSL/API error)"


def get_stock_price(query):
    symbol_match = re.search(r'stock (\w+)', query.lower())
    symbol = symbol_match.group(1).upper() if symbol_match else "AAPL"
    url    = "https://finnhub.io/api/v1/quote"
    params = {"symbol": symbol, "token": os.getenv("FINNHUB_API_KEY")}
    try:
        data = requests.get(url, params=params).json()
        if data.get("c"):
            return f"Current price of {symbol}: ${data['c']}"
        return "Stock data not available."
    except Exception:
        return "(Mock API response due to SSL/API error)"


def google_search(query):
    url    = "https://api.duckduckgo.com/"
    params = {"q": query, "format": "json", "no_html": 1}
    try:
        data    = requests.get(url, params=params).json()
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
    except Exception:
        return "(Mock API response due to SSL/API error)"


def get_live_data(user_msg):
    msg = user_msg.lower()
    if any(k in msg for k in ["bitcoin", "btc", "ethereum", "eth"]):
        return get_crypto_price(user_msg)
    elif "weather" in msg:
        return get_weather(user_msg)
    elif "news" in msg:
        return get_news(user_msg)
    elif "stock" in msg:
        return get_stock_price(user_msg)
    else:
        return google_search(user_msg)


# ═══════════════════════════════════════════════════════
#  ROUTE — /chat  (main AI endpoint)
# ═══════════════════════════════════════════════════════
@app.route("/chat", methods=["POST"])
def chat():
    data       = request.get_json()
    session_id = data.get("session_id", "default")
    user_msg   = data.get("message", "")

    if session_id not in conversations:
        conversations[session_id] = []

    history = conversations[session_id]

    # Build conversation history text for the prompt
    history_text = ""
    for msg in history:
        role = "User" if msg["role"] == "user" else "Assistant"
        history_text += f"{role}: {msg['content']}\n"

    # Fetch live data if needed
    search_context = ""
    search_used    = False
    results        = ""
    if needs_search(user_msg):
        results = get_live_data(user_msg)
        if results.strip():
            search_context = f"\n[Live search results]\n{results}\n"
            search_used    = True
        else:
            search_context = "\n[No live data found, answer from knowledge]\n"

    # Build prompt
    if search_used:
        system_instruction = (
            "You are Echo Mind, a helpful AI assistant. "
            "Use the provided live search results to answer accurately."
        )
    else:
        system_instruction = (
            "You are Echo Mind, a helpful AI assistant. "
            "Answer using general knowledge without mentioning missing search results."
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
    except Exception:
        if search_used and results.strip():
            reply = f"(Live API only) {results}"
        else:
            reply = f"(Mock reply) Gemini would answer: '{user_msg}'"

    # Save messages with timestamp so history panel shows correct times
    now_iso = datetime.utcnow().isoformat()
    history.append({"role": "user",      "content": user_msg, "timestamp": now_iso})
    history.append({"role": "assistant", "content": reply,    "timestamp": now_iso})

    save_chat_history(conversations)
    return jsonify({"reply": reply, "search_used": search_used})


# ═══════════════════════════════════════════════════════
#  ROUTE — /history  (optional live refresh from frontend)
# ═══════════════════════════════════════════════════════
@app.route("/history", methods=["GET"])
def get_history():
    return jsonify(build_recent_history())


if __name__ == "__main__":
    app.run(debug=True, port=5000)
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













