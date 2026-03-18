from flask import Flask, render_template_string, request
import urllib.request
import json
import datetime

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
    },
}

WEEKDAYS = {
    "ko": ["월", "화", "수", "목", "금", "토", "일"],
    "en": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
}

HTML = """
<!DOCTYPE html>
<html lang="{{ lang }}">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ t.title }}</title>
    <style>
        * { box-sizing: border-box; }
        body { font-family: 'Segoe UI', sans-serif; margin: 0; min-height: 100vh;
               background: linear-gradient(135deg, #74b9ff, #0984e3);
               display: flex; justify-content: center;
               align-items: flex-start; padding: 40px 16px; }
        .container { width: 100%; max-width: 480px; }
        .card { background: rgba(255,255,255,0.95); border-radius: 20px; padding: 28px;
                box-shadow: 0 8px 32px rgba(0,0,0,0.15); margin-bottom: 16px; }
        .topbar { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
        .logo { font-weight: 700; color: #2196F3; font-size: 1.1rem; }
        .lang-btn { background: rgba(33,150,243,0.1); border: 1px solid #2196F3;
                    color: #2196F3; border-radius: 20px; padding: 4px 14px;
                    cursor: pointer; font-size: 0.85rem; text-decoration: none; }
        .search-row { display: flex; gap: 8px; }
        input[type=text] { flex: 1; padding: 10px 14px; border: 1px solid #ddd;
                           border-radius: 10px; font-size: 1rem; outline: none; }
        input[type=text]:focus { border-color: #2196F3; }
        .btn { padding: 10px 18px; background: #2196F3; color: white; border: none;
               border-radius: 10px; font-size: 1rem; cursor: pointer; }
        .btn:hover { background: #1976D2; }
        .btn-fav { background: #f39c12; padding: 5px 12px; font-size: 0.82rem;
                   border-radius: 8px; margin-top: 14px; }
        .btn-fav:hover { background: #e67e22; }
        .city-name { font-size: 1rem; color: #666; margin: 22px 0 2px; }
        .temp { font-size: 5rem; font-weight: 700; color: #2196F3; line-height: 1; }
        .desc { font-size: 1.1rem; color: #444; margin: 8px 0; }
        .meta { color: #777; font-size: 0.88rem; margin-top: 10px;
                display: flex; justify-content: center; gap: 10px; flex-wrap: wrap; }
        .meta span { background: #f0f4ff; padding: 4px 10px; border-radius: 20px; }
        .section-title { font-size: 0.82rem; font-weight: 700; color: #999;
                         text-transform: uppercase; letter-spacing: 1px; margin-bottom: 14px; }
        .forecast { display: flex; justify-content: space-between; gap: 6px; }
        .fc-day { flex: 1; background: #f4f8ff; border-radius: 12px; padding: 10px 4px; text-align: center; }
        .fc-day .day { font-weight: 600; color: #555; font-size: 0.82rem; margin-bottom: 4px; }
        .fc-max { color: #2196F3; font-weight: 700; font-size: 1rem; }
        .fc-min { color: #bbb; font-size: 0.8rem; }
        .fav-list { display: flex; flex-wrap: wrap; gap: 8px; }
        .fav-item { display: flex; align-items: center; gap: 6px;
                    background: #f0f4ff; border-radius: 20px; padding: 5px 12px; }
        .fav-link { text-decoration: none; color: #2196F3; font-size: 0.9rem; font-weight: 500; }
        .fav-link:hover { text-decoration: underline; }
        .fav-del { background: #e74c3c; border: none; color: white; border-radius: 50%;
                   width: 17px; height: 17px; font-size: 0.65rem; cursor: pointer; padding: 0; }
        .error { color: #e74c3c; margin-top: 16px; font-size: 0.95rem; }
        .empty { color: #ccc; font-size: 0.9rem; }
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
            <div class="city-name">📍 {{ city }}</div>
            <div class="temp">{{ temp }}°</div>
            <div class="desc">{{ desc }}</div>
            <div class="meta">
                <span>{{ t.feels }} {{ feels_like }}°C</span>
                <span>{{ t.humidity }} {{ humidity }}%</span>
                <span>{{ t.wind }} {{ wind }} km/h</span>
            </div>
            <form method="get">
                <input type="hidden" name="city" value="{{ city }}">
                <input type="hidden" name="lang" value="{{ lang }}">
                <input type="hidden" name="favs" value="{{ favs_param }}">
                <input type="hidden" name="add_fav" value="{{ city }}">
                <button class="btn btn-fav" type="submit">{{ t.add_fav }}</button>
            </form>
        {% endif %}
    </div>

    {% if not error and forecast %}
    <div class="card">
        <div class="section-title">{{ t.forecast }}</div>
        <div class="forecast">
            {% for day in forecast %}
            <div class="fc-day">
                <div class="day">{{ day.label }}</div>
                <div class="fc-max">{{ day.max }}°</div>
                <div class="fc-min">{{ day.min }}°</div>
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
    url = f"https://wttr.in/{city}?format=j1"
    with urllib.request.urlopen(url, timeout=5) as r:
        raw = r.read().decode()

    print(f"[DEBUG] response (first 300): {raw[:300]}", flush=True)

    try:
        resp = json.loads(raw)
    except json.JSONDecodeError as e:
        raise ValueError(f"JSON 파싱 실패: {e} / 응답: {raw[:200]}")

    data = resp.get("data", resp)  # 'data' 키로 감싸진 경우 대응
    c = data["current_condition"][0]
    current = {
        "temp": c["temp_C"],
        "feels_like": c["FeelsLikeC"],
        "humidity": c["humidity"],
        "desc": c["weatherDesc"][0]["value"],
        "wind": c["windspeedKmph"],
    }

    wd = WEEKDAYS[lang]
    forecast = []
    for i, day in enumerate(data["weather"][:5]):
        d = datetime.date.today() + datetime.timedelta(days=i)
        label = I18N[lang]["today"] if i == 0 else wd[d.weekday()]
        forecast.append({"label": label, "max": day["maxtempC"], "min": day["mintempC"]})

    return current, forecast


@app.route("/")
def index():
    city = request.args.get("city", "Seoul")
    lang = request.args.get("lang", "ko")
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
        current, forecast = fetch_weather(city, lang)
        return render_template_string(
            HTML, city=city, lang=lang, next_lang=next_lang, t=t,
            favorites=favorites, favs_param=favs_param,
            forecast=forecast, error=None, **current,
        )
    except Exception as e:
        return render_template_string(
            HTML, city=city, lang=lang, next_lang=next_lang, t=t,
            favorites=favorites, favs_param=favs_param,
            forecast=[], error=str(e),
            temp=None, feels_like=None, humidity=None, desc=None, wind=None,
        )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)