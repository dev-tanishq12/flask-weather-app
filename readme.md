# ☁️ WeatherCast Pro

A full-stack weather forecast web app built with **Flask** and **Python**, featuring Google OAuth login, real-time weather data, 7-day forecasts, air quality index, and more.

---

## 🌟 Features

- 🔐 **Google OAuth Login** — Secure one-click sign-in via Google
- 🌡️ **Real-time Weather** — Current temperature, humidity, wind, pressure, visibility
- 📅 **7-Day Forecast** — Daily high/low, conditions, and humidity
- 📈 **Temperature Trend Chart** — Interactive Chart.js line graph
- 💨 **Air Quality Index (AQI)** — Live PM2.5 and PM10 readings
- 📍 **Auto-detect Location** — Fetch weather via GPS in one click
- ⭐ **Save Favourite Cities** — Bookmark cities per user account
- 🔗 **Shareable URLs** — `/weather?city=Delhi` works directly
- 🌙 **Dark / Light Mode** — Toggle with preference saved in browser
- °C / °F **Unit Toggle** — Instant client-side temperature conversion
- 📰 **Live Weather News** — Powered by SerpAPI Google News
- 🛡️ **Rate Limiting** — Flask-Limiter prevents API abuse
- ⚡ **Response Caching** — News cached for 1 hour to reduce API calls

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python, Flask |
| Auth | Google OAuth 2.0 via Authlib |
| Weather API | OpenWeatherMap |
| News API | SerpAPI (Google News) |
| Frontend | HTML, CSS, Bootstrap 5, Bootstrap Icons |
| Charts | Chart.js |
| Session | Flask-Login |
| Caching | Flask-Caching |
| Rate Limiting | Flask-Limiter |

---

## 📁 Project Structure
Flask-Weather-app/
│
├── templates/
│   ├── index.html        # Main weather dashboard
│   └── landing.html      # Public landing page
│
├── app.py                # Main Flask app — routes, API calls, auth
├── config.py             # API keys and configuration
├── secret_key.py         # Secret key generator
├── user_logins.json      # Stores login history (auto-created)
├── favorites.json        # Stores per-user saved cities (auto-created)
└── requirements.txt      # Python dependencies
---

## ⚙️ Setup & Installation

### 1. Clone the repository
```bash
git clone https://github.com/yourusername/flask-weather-app.git
cd flask-weather-app
```

### 2. Create a virtual environment
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure API keys

Create a `config.py` file in the root folder:
```python
SECRET_KEY = "your-secret-key"
API_KEY = "your-openweathermap-api-key"
BASE_URL = "https://api.openweathermap.org/data/2.5/weather"
FORECAST_URL = "https://api.openweathermap.org/data/2.5/forecast"
AQI_URL = "https://api.openweathermap.org/data/2.5/air_pollution"
GOOGLE_CLIENT_ID = "your-google-client-id"
GOOGLE_CLIENT_SECRET = "your-google-client-secret"
SERPAPI_KEY = "your-serpapi-key"
```

### 5. Run the app
```bash
python app.py
```

Visit `http://localhost:5000` in your browser.

---

## 🔑 Getting API Keys

| Service | Where to get it |
|---|---|
| OpenWeatherMap | [openweathermap.org/api](https://openweathermap.org/api) — Free tier works |
| Google OAuth | [console.cloud.google.com](https://console.cloud.google.com) → Create OAuth 2.0 credentials |
| SerpAPI | [serpapi.com](https://serpapi.com) — 100 free searches/month |

### Google OAuth setup steps:
1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create a new project
3. Enable **Google+ API** and **OpenID Connect**
4. Go to **Credentials** → Create **OAuth 2.0 Client ID**
5. Set Authorized redirect URI to: `http://localhost:5000/login/callback`
6. Copy the Client ID and Client Secret into `config.py`

---

## 📦 Requirements
Flask
flask-login
flask-caching
flask-limiter
authlib
requests
google-search-results
Generate your own `requirements.txt` with:
```bash
pip freeze > requirements.txt
```

---

## 🚀 Usage

| Action | How |
|---|---|
| Search weather | Type a city name in the search bar and hit Search |
| Use your location | Click the "My Location" button (allow browser permission) |
| Save a city | Click the ⭐ Save City button on any weather result |
| Switch units | Toggle °C / °F in the top navbar |
| Dark mode | Click the moon icon in the navbar |
| Share weather | Copy the URL — `?city=CityName` is always in the link |

---

## 📸 Screenshots

> Add screenshots here after running the app locally.  
> `![Landing Page](screenshots/landing.png)`  
> `![Weather Dashboard](screenshots/dashboard.png)`

---

## 🔒 Security Notes

- All OAuth redirects are validated against the same domain
- Rate limiting is applied on the weather endpoint (30 requests/minute)
- Session cookies are `HttpOnly` and `SameSite=Lax`
- User login history is logged locally to `user_logins.json`

---

## 🙋‍♂️ Author

**Your Name**  
[GitHub](https://github.com/yourusername) · [LinkedIn](https://linkedin.com/in/yourusername)

---

## 📄 License

This project is open source and available under the [MIT License](LICENSE).
