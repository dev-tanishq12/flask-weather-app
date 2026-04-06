from flask import Flask, render_template, redirect, url_for, request, session, flash, abort, jsonify
import requests
import datetime
import config
import json
import os
from authlib.integrations.flask_client import OAuth
from flask_login import (
    LoginManager,
    UserMixin,
    login_user,
    login_required,
    logout_user,
    current_user
)
from serpapi import GoogleSearch
from flask_caching import Cache
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from urllib.parse import urlparse, urljoin

app = Flask(__name__)
app.secret_key = config.SECRET_KEY

cache = Cache(app, config={'CACHE_TYPE': 'SimpleCache'})

limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["200 per day", "50 per hour"]
)

app.config.update(
    SESSION_COOKIE_SECURE=False,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
    PERMANENT_SESSION_LIFETIME=datetime.timedelta(hours=1)
)

oauth = OAuth(app)
google = oauth.register(
    name="google",
    client_id=config.GOOGLE_CLIENT_ID,
    client_secret=config.GOOGLE_CLIENT_SECRET,
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={
        "scope": "openid email profile",
        "prompt": "select_account"
    },
)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"
login_manager.login_message = "Please log in to access this page."
login_manager.login_message_category = "info"

class User(UserMixin):
    def __init__(self, user_id, name, email):
        self.id = user_id
        self.name = name
        self.email = email

users = {}
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
USER_LOGINS_FILE = os.path.join(BASE_DIR, "user_logins.json")
FAVORITES_FILE = os.path.join(BASE_DIR, "favorites.json")

def load_user_logins():
    if not os.path.exists(USER_LOGINS_FILE):
        return []
    try:
        with open(USER_LOGINS_FILE, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return []

def save_user_login(user_data):
    logins = load_user_logins()
    logins.append(user_data)
    try:
        with open(USER_LOGINS_FILE, "w") as f:
            json.dump(logins, f, indent=2)
    except IOError as e:
        print(f"Error saving user login: {e}")

def load_favorites():
    if not os.path.exists(FAVORITES_FILE):
        return {}
    try:
        with open(FAVORITES_FILE, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {}

def save_favorites(data):
    try:
        with open(FAVORITES_FILE, "w") as f:
            json.dump(data, f, indent=2)
    except IOError as e:
        print(f"Error saving favorites: {e}")

@login_manager.user_loader
def load_user(user_id):
    return users.get(user_id)

def is_safe_url(target):
    ref_url = urlparse(request.host_url)
    test_url = urlparse(urljoin(request.host_url, target))
    return test_url.scheme in ('http', 'https') and ref_url.netloc == test_url.netloc

@cache.cached(timeout=3600, key_prefix='weather_news')
def get_google_weather_news():
    try:
        params = {
            "engine": "google",
            "q": "weather news",
            "tbm": "nws",
            "api_key": config.SERPAPI_KEY,
            "num": 5,
            "hl": "en",
            "gl": "us"
        }
        search = GoogleSearch(params)
        results = search.get_dict()
        if not isinstance(results, dict) or 'error' in results:
            return get_fallback_news()
        if not isinstance(results.get('news_results'), list):
            return get_fallback_news()
        formatted_news = []
        for item in results.get('news_results', []):
            if not isinstance(item, dict):
                continue
            try:
                news_item = {
                    "title": item.get("title", "No title available"),
                    "date": format_news_date(item.get("date", "")) if item.get("date") else "Unknown date",
                    "source": item.get("source", {}).get("name", "Unknown source"),
                    "url": item.get("link", "https://news.google.com/search?q=weather"),
                    "content": item.get("snippet", "Read more about this weather update..."),
                }
                if news_item["title"] and news_item["url"]:
                    formatted_news.append(news_item)
                    if len(formatted_news) >= 4:
                        break
            except Exception:
                continue
        return formatted_news if formatted_news else get_fallback_news()
    except Exception as e:
        print(f"SerpAPI Error: {str(e)}")
        return get_fallback_news()

def format_news_date(date_str):
    try:
        date_obj = datetime.datetime.fromisoformat(date_str)
        return date_obj.strftime('%b %d, %Y')
    except (ValueError, TypeError):
        return date_str if isinstance(date_str, str) else "Unknown date"

def get_fallback_news():
    current_date = datetime.datetime.now().strftime('%b %d')
    return [
        {
            "title": "National Weather Service Issues New Advisory",
            "date": current_date,
            "source": "NOAA",
            "url": "https://news.google.com/search?q=weather",
            "content": "Latest weather alerts and advisories from the National Weather Service"
        },
        {
            "title": "Global Warming Effects Accelerating",
            "date": current_date,
            "source": "Climate Research",
            "url": "https://news.google.com/search?q=climate",
            "content": "New studies show increasing impacts of climate change worldwide"
        }
    ]

def get_weather(city=None, lat=None, lon=None):
    try:
        params = {'appid': config.API_KEY, 'units': 'metric'}
        if city:
            params['q'] = city
        elif lat is not None and lon is not None:
            params['lat'] = lat
            params['lon'] = lon
        else:
            return None

        response = requests.get(config.BASE_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        lat_data = data["coord"]["lat"]
        lon_data = data["coord"]["lon"]

        # Fetch AQI
        aqi_data = get_aqi(lat_data, lon_data)

        # Fetch forecast
        forecast_data = get_forecast(lat=lat_data, lon=lon_data)

        return {
            "city": data["name"],
            "country": data["sys"].get("country", ""),
            "temperature": round(data["main"]["temp"], 1),
            "feels_like": round(data["main"]["feels_like"], 1),
            "temp_min": round(data["main"]["temp_min"], 1),
            "temp_max": round(data["main"]["temp_max"], 1),
            "description": data["weather"][0]["description"],
            "icon": data["weather"][0]["icon"],
            "humidity": data["main"]["humidity"],
            "wind_speed": round(data["wind"]["speed"] * 3.6, 1),  # m/s to km/h
            "pressure": data["main"]["pressure"],
            "visibility": data.get("visibility", 0),
            "cloudiness": data["clouds"]["all"],
            "sunrise": datetime.datetime.fromtimestamp(data["sys"]["sunrise"]).strftime('%H:%M'),
            "sunset": datetime.datetime.fromtimestamp(data["sys"]["sunset"]).strftime('%H:%M'),
            "time": datetime.datetime.now().strftime('%H:%M, %b %d'),
            "aqi": aqi_data,
            "forecast": forecast_data,
            "lat": lat_data,
            "lon": lon_data
        }
    except requests.exceptions.RequestException as e:
        print(f"Weather API error: {str(e)}")
        return {"error": "Could not fetch weather data. Please check the city name."}
    except KeyError as e:
        print(f"Data parsing error: {str(e)}")
        return {"error": "Unexpected weather data format"}

def get_aqi(lat, lon):
    try:
        params = {'lat': lat, 'lon': lon, 'appid': config.API_KEY}
        response = requests.get(config.AQI_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        aqi_index = data["list"][0]["main"]["aqi"]
        aqi_labels = {1: "Good", 2: "Fair", 3: "Moderate", 4: "Poor", 5: "Very Poor"}
        aqi_colors = {1: "success", 2: "info", 3: "warning", 4: "danger", 5: "danger"}
        return {
            "index": aqi_index,
            "label": aqi_labels.get(aqi_index, "Unknown"),
            "color": aqi_colors.get(aqi_index, "secondary"),
            "pm25": round(data["list"][0]["components"].get("pm2_5", 0), 1),
            "pm10": round(data["list"][0]["components"].get("pm10", 0), 1),
        }
    except Exception as e:
        print(f"AQI error: {e}")
        return None

def get_forecast(lat, lon):
    try:
        params = {'lat': lat, 'lon': lon, 'appid': config.API_KEY, 'units': 'metric', 'cnt': 40}
        response = requests.get(config.FORECAST_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()

        # Group by day, pick midday reading
        days = {}
        for item in data["list"]:
            date = datetime.datetime.fromtimestamp(item["dt"]).strftime('%Y-%m-%d')
            hour = datetime.datetime.fromtimestamp(item["dt"]).hour
            if date not in days or abs(hour - 12) < abs(datetime.datetime.fromtimestamp(days[date]["dt"]).hour - 12):
                days[date] = item

        forecast = []
        for date, item in list(sorted(days.items()))[:7]:
            forecast.append({
                "date": datetime.datetime.strptime(date, '%Y-%m-%d').strftime('%a, %b %d'),
                "day": datetime.datetime.strptime(date, '%Y-%m-%d').strftime('%a'),
                "temp_max": round(item["main"]["temp_max"], 1),
                "temp_min": round(item["main"]["temp_min"], 1),
                "description": item["weather"][0]["description"],
                "icon": item["weather"][0]["icon"],
                "humidity": item["main"]["humidity"],
                "wind_speed": round(item["wind"]["speed"] * 3.6, 1),
            })
        return forecast
    except Exception as e:
        print(f"Forecast error: {e}")
        return []

@app.route("/")
def home():
    if current_user.is_authenticated:
        return redirect(url_for("weather"))
    news = get_google_weather_news()
    return render_template("landing.html", news=news)

@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        flash("You are already logged in", "info")
        return redirect(url_for("weather"))
    next_page = request.args.get('next')
    if next_page and not is_safe_url(next_page):
        return abort(400)
    session['next'] = next_page or url_for('weather')
    session.permanent = True  # activate PERMANENT_SESSION_LIFETIME
    redirect_uri = url_for('authorize', _external=True)
    if 'localhost' in redirect_uri and redirect_uri.startswith('https://'):
        redirect_uri = redirect_uri.replace('https://', 'http://')
    return google.authorize_redirect(redirect_uri)

@app.route("/login/callback")
def authorize():
    try:
        token = google.authorize_access_token()
        if not token:
            flash("Failed to get access token", "danger")
            return redirect(url_for("login"))
        # Authlib parses userinfo from the id_token when openid scope is used
        user_info = token.get('userinfo')
        if not user_info:
            # Fallback: fetch userinfo manually
            headers = {"Authorization": f"Bearer {token['access_token']}"}
            resp = requests.get("https://openidconnect.googleapis.com/v1/userinfo", headers=headers)
            if resp.status_code != 200:
                flash("Failed to fetch user information", "danger")
                return redirect(url_for("login"))
            user_info = resp.json()
        if "sub" not in user_info:
            flash("Error: 'sub' key missing in response", "danger")
            return redirect(url_for("login"))
        user_id = user_info["sub"]
        user = User(user_id, user_info.get("name", "Anonymous"), user_info.get("email", ""))
        users[user_id] = user
        login_user(user, remember=True)
        flash(f"Welcome back, {user.name}!", "success")
        login_data = {
            "user_id": user_id,
            "email": user.email,
            "name": user.name,
            "login_time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "ip_address": request.remote_addr
        }
        save_user_login(login_data)
        next_page = session.pop('next', None)
        return redirect(next_page or url_for('weather'))
    except Exception as e:
        print(f"Login error: {str(e)}", flush=True)
        flash("Login failed. Please try again.", "danger")
        return redirect(url_for("login"))

@app.route("/weather", methods=["GET", "POST"])
@login_required
@limiter.limit("30 per minute")
def weather():
    weather_data = None
    city = request.args.get('city') or request.form.get('city')

    # Load user favorites
    all_favorites = load_favorites()
    user_favorites = all_favorites.get(current_user.id, [])

    if city:
        weather_data = get_weather(city=city)
        if weather_data and "error" in weather_data:
            flash(weather_data["error"], "danger")
            weather_data = None

    return render_template("index.html",
                           weather=weather_data,
                           user=current_user,
                           news=get_google_weather_news(),
                           favorites=user_favorites,
                           city=city or "")

@app.route("/weather/location", methods=["POST"])
@login_required
def weather_by_location():
    """Called from browser Geolocation API via JS fetch"""
    data = request.get_json(silent=True)  # silent=True returns None instead of raising on bad Content-Type
    if not data:
        return jsonify({"error": "Invalid or missing JSON body"}), 400
    lat = data.get("lat")
    lon = data.get("lon")
    if lat is None or lon is None:
        return jsonify({"error": "Missing coordinates"}), 400
    weather_data = get_weather(lat=lat, lon=lon)
    if weather_data is None:
        return jsonify({"error": "Could not retrieve weather data"}), 500
    return jsonify(weather_data)

@app.route("/favorites/add", methods=["POST"])
@login_required
def add_favorite():
    city = request.form.get("city", "").strip()
    if not city:
        return redirect(url_for("weather"))
    all_favorites = load_favorites()
    user_favorites = all_favorites.get(current_user.id, [])
    if city not in user_favorites:
        user_favorites.append(city)
    all_favorites[current_user.id] = user_favorites
    save_favorites(all_favorites)
    flash(f"{city} added to favorites!", "success")
    return redirect(url_for("weather", city=city))

@app.route("/favorites/remove", methods=["POST"])
@login_required
def remove_favorite():
    city = request.form.get("city", "").strip()
    if not city:
        return redirect(url_for("weather"))
    all_favorites = load_favorites()
    user_favorites = all_favorites.get(current_user.id, [])
    if city in user_favorites:
        user_favorites.remove(city)
    all_favorites[current_user.id] = user_favorites
    save_favorites(all_favorites)
    flash(f"{city} removed from favorites.", "info")
    return redirect(url_for("weather"))

@app.route("/logout", methods=["POST"])
@login_required
def logout():
    logout_user()
    session.clear()
    flash("You have been logged out successfully", "success")
    return redirect(url_for("home"))

if __name__ == "__main__":
    for f in [USER_LOGINS_FILE, FAVORITES_FILE]:
        if not os.path.exists(f):
            with open(f, "w") as fp:
                json.dump([] if f == USER_LOGINS_FILE else {}, fp)
    app.run(host='0.0.0.0', port=5000, debug=True)