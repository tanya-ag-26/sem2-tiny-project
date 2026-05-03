# 🤖 AI Chatbot with Real-Time Data (Flask + Gemini)

## 📌 Overview
A lightweight **AI chatbot** built with **Python Flask** and **Google Gemini API** that supports **context-aware conversations** and fetches **real-time data** (weather, news, crypto, stocks) using external APIs.

---

## 🚀 Features

### 💬 AI Chat
- Google Gemini integration (Generative AI)
- Context-aware replies using **session-based memory**
- Chat-style interaction via a simple web UI

### 🌐 Real-Time Data
- 💰 Crypto (CoinGecko)  
- 🌦 Weather (OpenWeather)  
- 📰 News (NewsAPI)  
- 📈 Stocks (Finnhub)  
- 🔎 Fallback search (DuckDuckGo)

### 🧠 Smart Routing
- Detects when a query needs **fresh data**
- Combines **conversation history + live data** before sending to Gemini

---

## 🛠 Tech Stack
- **Backend:** Python, Flask  
- **AI:** Google Gemini API (`google-generativeai`)  
- **APIs:** CoinGecko, OpenWeather, NewsAPI, Finnhub, DuckDuckGo  
- **Frontend:** HTML, CSS  
- **Env Management:** python-dotenv  

---

## 📂 Project Structure
```
project/
│
├── app.py                # Flask app (routes, Gemini calls, orchestration)
├── templates/            # HTML files
├── static/               # CSS, JS, assets
├── .env                  # Secrets (NOT committed)
├── requirements.txt      # Dependencies
├── README.md
```

---

## ⚙️ Setup

### 1) Clone
```bash
git clone https://github.com/tanya-ag-26/sem2-tiny-project.git
cd sem2-tiny-project
```

### 2) Install
```bash
pip install -r requirements.txt
```

### 3) Environment
Create a `.env` file:

```env
GENAI_API_KEY=your_gemini_api_key
OPENWEATHER_API_KEY=your_weather_api_key
NEWS_API_KEY=your_news_api_key
FINNHUB_API_KEY=your_stock_api_key
```

### 4) Create Required Files
This project uses local JSON files for storing data. These are not included in the repository.

Create the following files manually:

```json
// users.json
[]
```

```json
// chat_history.json
{}
```

### 5) Run
```bash
python app.py
```

Open: http://localhost:5000

---

## 🔌 API

### POST `/chat`

**Request**
```json
{
  "session_id": "user1",
  "message": "What is the price of Bitcoin today?"
}
```

**Response**
```json
{
  "reply": "Bitcoin price: $XXXXX USD (₹XXXXX INR)",
  "search_used": true
}
```

---

## 🧠 How It Works
1. Receive message at `/chat`  
2. Validate input and attach `session_id`  
3. Check if **real-time data** is needed  
4. Fetch data from APIs (if required)  
5. Build prompt using **history + live data**  
6. Send to Gemini → return response  

---

## 🧩 Architecture
User → Flask API → Smart Router →  
→ (Live APIs if needed) →  
→ Gemini API → Response  

Conversation history is stored locally using JSON files.

---

## 🔒 Security Notes
- Never commit `.env` file  
- API keys must remain private  
- `users.json` contains user data → keep it local  
- `chat_history.json` stores conversations → not pushed to GitHub  

---

## 👥 Team
- Tanya Agrawal  
- Aishani Agrawal  
- Yash Vardhan  

---

## 📊 Status
- ✅ Flask backend  
- ✅ Gemini integration  
- ✅ Session memory  
- ✅ Real-time APIs  
- 🔄 UI improvements ongoing  

---

## ⭐ Highlights
- AI + real-time data fusion  
- Context-aware chatbot  
- Multi-API orchestration  
- Simple, extendable Flask design  

---

## 📌 License
Educational use (college mini project)
