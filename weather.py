from flask import Flask, render_template_string, request
import urllib.request
import json
import datetime
import os

app = Flask(__name__)

I18N = {
    "ko": {
        "title": "날씨 앱",
        "placeholder": "도시 입력",
        "search": "검색",
        "feels": "체감",
        "humidity": "습도",
        "wind": "풍속",
        "forecast": "5일 예보",
        "favorites": "즐겨찾기",
        "add_fav": "★ 추가",
        "today": "오늘",
        "lang_toggle": "EN",
        "no_fav": "즐겨찾기가 없습니다.",
        "hourly": "시간별 예보",
        "sunrise": "일출",
        "sunset": "일몰",
        "rain_chance": "강수확률",
    },
    "en": {
        "title": "Weather App",
        "placeholder": "Enter city",
        "search": "Search",
        "feels": "Feels like",
        "humidity": "Humidity",
        "wind": "Wind",
        "forecast": "5-Day Forecast",
        "favorites": "Favorites",
        "add_fav": "★ Save",
        "today": "Today",
        "lang_toggle": "한국어",
        "no_fav": "No favorites yet.",
        "hourly": "Hourly Forecast",
        "sunrise": "Sunrise",
        "sunset": "Sunset",
        "rain_chance": "Rain",
    },
}

WEEKDAYS = {
    "ko": ["월", "화", "수", "목", "금", "토", "일"],
    "en": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
}

WEATHER_ICONS = {
    "sunny": ["113"],
    "partly_cloudy": ["116"],
    "cloudy": ["119", "122"],
    "fog": ["143", "248", "260"],
    "drizzle": ["266", "281", "284", "293", "296"],
    "rain": ["299", "302", "305", "308", "353", "356", "359"],
    "snow": ["179", "182", "185", "227", "230", "317", "320", "323", "326", "329", "332", "335", "338", "368", "371", "374", "377"],
    "thunder": ["200", "386", "389", "392", "395"],
}

def get_icon(code):
    for icon, codes in WEATHER_ICONS.items():
        if str(code) in codes:
            return {
                "sunny": "☀️",
                "partly_cloudy": "⛅",
                "cloudy": "☁️",
                "fog": "🌫️",
                "drizzle": "🌦️",
                "rain": "🌧️",
                "snow": "❄️",
                "thunder": "⛈️",
            }[icon]
    return "🌡️"

HTML = """
<!DOCTYPE html>
<html lang="{{ lang }}">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ t.title }}</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: 'Segoe UI', sans-serif;
            min-height: 100vh;
            background: linear-gradient(160deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
            display: flex; justify-content: center;
            align-items: flex-start; padding: 40px 16px;
        }
        .container { width: 100%; max-width: 500px; }

        /* 카드 */
        .card {
            background: rgba(255,255,255,0.07);
            backdrop-filter: blur(20px);
            border: 1px solid rgba(255,255,255,0.12);
            border-radius: 24px; padding: 28px;
            margin-bottom: 16px;
            box-shadow: 0 8px 32px rgba(0,0,0,0.3);
        }

        /* 상단바 */
        .topbar { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
        .logo { font-weight: 700; color: #fff; font-size: 1.1rem; letter-spacing: 0.5px; }
        .lang-btn {
            background: rgba(255,255,255,0.1); border: 1px solid rgba(255,255,255,0.2);
            color: #fff; border-radius: 20px; padding: 5px 14px;
            cursor: pointer; font-size: 0.82rem; text-decoration: none;
            transition: background 0.2s;
        }
        .lang-btn:hover { background: rgba(255,255,255,0.2); }

        /* 검색 */
        .search-row { display: flex; gap: 8px; }
        input[type=text] {
            flex: 1; padding: 11px 16px;
            background: rgba(255,255,255,0.1);
            border: 1px solid rgba(255,255,255,0.2);
            border-radius: 12px; font-size: 1rem;
            color: #fff; outline: none;
        }
        input[type=text]::placeholder { color: rgba(255,255,255,0.4); }
        input[type=text]:focus { border-color: rgba(255,255,255,0.5); background: rgba(255,255,255,0.15); }
        .btn {
            padding: 11px 20px;
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white; border: none; border-radius: 12px;
            font-size: 1rem; cursor: pointer; font-weight: 600;
            transition: opacity 0.2s;
        }
        .btn:hover { opacity: 0.85; }
        .btn-fav {
            background: linear-gradient(135deg, #f093fb, #f5576c);
            padding: 6px 14px; font-size: 0.82rem;
            border-radius: 10px; margin-top: 16px;
        }

        /* 현재 날씨 */
        .weather-main { text-align: center; padding: 10px 0; }
        .weather-icon { font-size: 5rem; line-height: 1; margin: 16px 0 8px; }
        .city-name { font-size: 1rem; color: rgba(255,255,255,0.6); margin-bottom: 4px; }
        .temp { font-size: 5.5rem; font-weight: 700; color: #fff; line-height: 1; }
        .temp sup { font-size: 2rem; vertical-align: super; }
        .desc { font-size: 1.1rem; color: rgba(255,255,255,0.8); margin: 10px 0; }
        .meta {
            display: flex; justify-content: center; gap: 10px;
            flex-wrap: wrap; margin-top: 14px;
        }
        .meta span {
            background: rgba(255,255,255,0.1);
            border: 1px solid rgba(255,255,255,0.15);
            color: rgba(255,255,255,0.85);
            padding: 5px 12px; border-radius: 20px; font-size: 0.85rem;
        }

        /* 예보 */
        .section-title {
            font-size: 0.78rem; font-weight: 700;
            color: rgba(255,255,255,0.4);
            text-transform: uppercase; letter-spacing: 1.5px; margin-bottom: 14px;
        }
        .forecast { display: flex; justify-content: space-between; gap: 6px; }
        .fc-day {
            flex: 1; background: rgba(255,255,255,0.07);
            border: 1px solid rgba(255,255,255,0.1);
            border-radius: 14px; padding: 12px 4px; text-align: center;
        }
        .fc-day .day { font-weight: 600; color: rgba(255,255,255,0.6); font-size: 0.78rem; margin-bottom: 4px; }
        .fc-icon { font-size: 1.4rem; margin: 4px 0; }
        .fc-max { color: #fff; font-weight: 700; font-size: 0.95rem; }
        .fc-min { color: rgba(255,255,255,0.35); font-size: 0.78rem; margin-top: 2px; }
        .fc-rain { color: #74b9ff; font-size: 0.72rem; margin-top: 2px; }

        /* 즐겨찾기 */
        .fav-list { display: flex; flex-wrap: wrap; gap: 8px; }
        .fav-item {
            display: flex; align-items: center; gap: 6px;
            background: rgba(255,255,255,0.08);
            border: 1px solid rgba(255,255,255,0.12);
            border-radius: 20px; padding: 5px 12px;
        }
        .fav-link { text-decoration: none; color: rgba(255,255,255,0.85); font-size: 0.88rem; font-weight: 500; }
        .fav-link:hover { color: #fff; }
        .fav-del {
            background: rgba(231,76,60,0.6); border: none; color: white;
            border-radius: 50%; width: 17px; height: 17px;
            font-size: 0.6rem; cursor: pointer; padding: 0;
        }
        .error { color: #ff6b6b; margin-top: 16px; font-size: 0.95rem; }
        .empty { color: rgba(255,255,255,0.3); font-size: 0.9rem; }

        /* 시간별 예보 */
        .hourly { display: flex; gap: 8px; overflow-x: auto; padding-bottom: 4px; }
        .hourly::-webkit-scrollbar { height: 4px; }
        .hourly::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.2); border-radius: 2px; }
        .h-item {
            flex-shrink: 0; background: rgba(255,255,255,0.07);
            border: 1px solid rgba(255,255,255,0.1);
            border-radius: 14px; padding: 10px 12px; text-align: center; min-width: 60px;
        }
        .h-time { font-size: 0.75rem; color: rgba(255,255,255,0.5); margin-bottom: 4px; }
        .h-icon { font-size: 1.3rem; margin: 4px 0; }
        .h-temp { color: #fff; font-weight: 700; font-size: 0.9rem; }
        .h-rain { color: #74b9ff; font-size: 0.75rem; margin-top: 2px; }

        /* 일출/일몰 + 강수확률 */
        .sun-row {
            display: flex; justify-content: center; gap: 20px; margin-top: 14px;
        }
        .sun-item { text-align: center; }
        .sun-label { font-size: 0.75rem; color: rgba(255,255,255,0.4); margin-bottom: 2px; }
        .sun-value { font-size: 0.95rem; color: #fff; font-weight: 600; }
    </style>
</head>
<body>
<div class="container">
    <div class="card">
        <div class="topbar">
            <span class="logo">⛅ {{ t.title }}</span>
            <a class="lang-btn" href="/?city={{ city }}&lang={{ next_lang }}&favs={{ favs_param }}">{{ t.lang_toggle }}</a>
        </div>

        <form method="get">
            <input type="hidden" name="lang" value="{{ lang }}">
            <input type="hidden" name="favs" value="{{ favs_param }}">
            <div class="search-row">
                <input type="text" name="city" value="{{ city }}" placeholder="{{ t.placeholder }}">
                <button class="btn" type="submit">{{ t.search }}</button>
            </div>
        </form>

        {% if error %}
            <p class="error">{{ error }}</p>
        {% else %}
        <div class="weather-main">
            <div class="city-name">📍 {{ city }}</div>
            <div class="weather-icon">{{ icon }}</div>
            <div class="temp">{{ temp }}<sup>°</sup></div>
            <div class="desc">{{ desc }}</div>
            <div class="meta">
                <span>🌡 {{ t.feels }} {{ feels_like }}°C</span>
                <span>💧 {{ t.humidity }} {{ humidity }}%</span>
                <span>💨 {{ t.wind }} {{ wind }} km/h</span>
            </div>
            <div class="sun-row">
                <div class="sun-item">
                    <div class="sun-label">🌅 {{ t.sunrise }}</div>
                    <div class="sun-value">{{ sunrise }}</div>
                </div>
                <div class="sun-item">
                    <div class="sun-label">🌇 {{ t.sunset }}</div>
                    <div class="sun-value">{{ sunset }}</div>
                </div>
            </div>
            <form method="get">
                <input type="hidden" name="city" value="{{ city }}">
                <input type="hidden" name="lang" value="{{ lang }}">
                <input type="hidden" name="favs" value="{{ favs_param }}">
                <input type="hidden" name="add_fav" value="{{ city }}">
                <button class="btn btn-fav" type="submit">{{ t.add_fav }}</button>
            </form>
        </div>
        {% endif %}
    </div>

    {% if not error and hourly %}
    <div class="card">
        <div class="section-title">{{ t.hourly }}</div>
        <div class="hourly">
            {% for h in hourly %}
            <div class="h-item">
                <div class="h-time">{{ h.time }}</div>
                <div class="h-icon">{{ h.icon }}</div>
                <div class="h-temp">{{ h.temp }}°</div>
                <div class="h-rain">💧{{ h.rain }}%</div>
            </div>
            {% endfor %}
        </div>
    </div>
    {% endif %}

    {% if not error and forecast %}
    <div class="card">
        <div class="section-title">{{ t.forecast }}</div>
        <div class="forecast">
            {% for day in forecast %}
            <div class="fc-day">
                <div class="day">{{ day.label }}</div>
                <div class="fc-icon">{{ day.icon }}</div>
                <div class="fc-max">{{ day.max }}°</div>
                <div class="fc-min">{{ day.min }}°</div>
                <div class="fc-rain">💧{{ day.rain }}%</div>
            </div>
            {% endfor %}
        </div>
    </div>
    {% endif %}

    <div class="card">
        <div class="section-title">{{ t.favorites }}</div>
        {% if favorites %}
        <div class="fav-list">
            {% for fav in favorites %}
            <div class="fav-item">
                <a class="fav-link" href="/?city={{ fav }}&lang={{ lang }}&favs={{ favs_param }}">{{ fav }}</a>
                <form method="get" style="margin:0;">
                    <input type="hidden" name="city" value="{{ city }}">
                    <input type="hidden" name="lang" value="{{ lang }}">
                    <input type="hidden" name="favs" value="{{ favs_param }}">
                    <input type="hidden" name="del_fav" value="{{ fav }}">
                    <button class="fav-del" type="submit">✕</button>
                </form>
            </div>
            {% endfor %}
        </div>
        {% else %}
            <div class="empty">{{ t.no_fav }}</div>
        {% endif %}
    </div>
</div>
</body>
</html>


"""

def fetch_weather(city, lang):
    base_url = os.environ.get("WTTR_BASE_URL", "https://wttr.in")
    url = f"{base_url}/{city}?format=j1"
    with urllib.request.urlopen(url, timeout=5) as r:
        raw = r.read().decode()
        
    if not raw or raw.strip() == 'null':
        raise ValueError("날씨 정보를 가져올 수 없습니다. 잠시 후 다시 시도해주세요.")
    
    print(f"[DEBUG] response (first 300): {raw[:300]}", flush=True)

    try:
        resp = json.loads(raw)
    except json.JSONDecodeError as e:
        raise ValueError(f"JSON 파싱 실패: {e} / 응답: {raw[:200]}")

    data = resp.get("data", resp)  # 'data' 키로 감싸진 경우 대응
    c = data["current_condition"][0]
    code = c["weatherCode"]
    current = {
        "temp": c["temp_C"],
        "feels_like": c["FeelsLikeC"],
        "humidity": c["humidity"],
        "desc": c["weatherDesc"][0]["value"],
        "wind": c["windspeedKmph"],
        "icon": get_icon(code),
    }

    wd = WEEKDAYS[lang]
    forecast = []
    for i, day in enumerate(data["weather"]):
        d = datetime.date.today() + datetime.timedelta(days=i)
        label = I18N[lang]["today"] if i == 0 else wd[d.weekday()]
        hourly_codes = [h["weatherCode"] for h in day.get("hourly", [])]
        day_icon = get_icon(hourly_codes[len(hourly_codes)//2]) if hourly_codes else "🌡️"
        # 강수확률 평균
        rain_chances = [int(h.get("chanceofrain", 0)) for h in day.get("hourly", [])]
        avg_rain = max(rain_chances) if rain_chances else 0
        forecast.append({
            "label": label,
            "max": day["maxtempC"],
            "min": day["mintempC"],
            "icon": day_icon,
            "rain": avg_rain,
        })

    # 시간별 예보 (오늘)
    hourly = []
    if data["weather"]:
        for h in data["weather"][0].get("hourly", []):
            time_val = int(h["time"])
            hour = time_val // 100
            hourly.append({
                "time": f"{hour:02d}:00",
                "temp": h["tempC"],
                "icon": get_icon(h["weatherCode"]),
                "rain": h["chanceofrain"],
            })

    # 일출/일몰
    astronomy = data["weather"][0].get("astronomy", [{}])[0]
    sunrise = astronomy.get("sunrise", "-")
    sunset = astronomy.get("sunset", "-")

    return current, forecast, hourly, sunrise, sunset



@app.route("/health")
def health():
    return "ok", 200

@app.route("/")
def index():
    city = request.args.get("city", os.environ.get("DEFAULT_CITY", "Seoul"))
    lang = request.args.get("lang", os.environ.get("DEFAULT_LANG", "ko"))
    if lang not in ("ko", "en"):
        lang = "ko"
    next_lang = "en" if lang == "ko" else "ko"
    t = I18N[lang]

    favs_raw = request.args.get("favs", "")
    favorites = [f for f in favs_raw.split(",") if f.strip()]

    add_fav = request.args.get("add_fav", "")
    if add_fav and add_fav not in favorites:
        favorites.append(add_fav)

    del_fav = request.args.get("del_fav", "")
    if del_fav in favorites:
        favorites.remove(del_fav)

    favs_param = ",".join(favorites)

    try:
        current, forecast, hourly, sunrise, sunset = fetch_weather(city, lang)
        return render_template_string(
            HTML, city=city, lang=lang, next_lang=next_lang, t=t,
            favorites=favorites, favs_param=favs_param,
            forecast=forecast, hourly=hourly,
            sunrise=sunrise, sunset=sunset,
            error=None, **current,
        )
    except Exception as e:
        return render_template_string(
            HTML, city=city, lang=lang, next_lang=next_lang, t=t,
            favorites=favorites, favs_param=favs_param,
            forecast=[], hourly=[], sunrise="-", sunset="-",
            error=str(e),
            temp=None, feels_like=None, humidity=None, desc=None, wind=None,
        )

if __name__ == "__main__":
    port = int(os.environ.get("APP_PORT", 8000))
    app.run(host="0.0.0.0", port=port)