from flask import Flask, render_template, request, jsonify
import requests
from datetime import datetime
from functools import lru_cache

app = Flask(__name__)


def celsius_to_f(c):
    return c * 9/5 + 32


@lru_cache(maxsize=256)
def geocode_city(city: str):
    # Use Open-Meteo's free geocoding API
    url = "https://geocoding-api.open-meteo.com/v1/search"
    params = {"name": city, "count": 1, "language": "en", "format": "json"}
    r = requests.get(url, params=params, timeout=10)
    r.raise_for_status()
    data = r.json()
    results = data.get("results") or []
    if not results:
        return None
    top = results[0]
    return {
        "name": top.get("name"),
        "country": top.get("country"),
        "lat": top.get("latitude"),
        "lon": top.get("longitude"),
        "admin1": top.get("admin1")
    }


def fetch_weather(lat: float, lon: float):
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "current_weather": True,
        "hourly": "temperature_2m,relative_humidity_2m,precipitation,wind_speed_10m",
        "daily": "weathercode,temperature_2m_max,temperature_2m_min,precipitation_sum,wind_speed_10m_max",
        "timezone": "auto"
    }
    r = requests.get(url, params=params, timeout=10)
    r.raise_for_status()
    return r.json()


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/weather")
def api_weather():
    city = request.args.get("city", "").strip()
    lat = request.args.get("lat", type=float)
    lon = request.args.get("lon", type=float)

    place = None
    if city:
        place = geocode_city(city)
        if not place:
            return jsonify({"error": "City not found"}), 404
        lat = place["lat"]
        lon = place["lon"]

    if lat is None or lon is None:
        return jsonify({"error": "Missing coordinates or city"}), 400

    data = fetch_weather(lat, lon)

    # Normalise a minimal payload
    current = data.get("current_weather", {})
    daily = data.get("daily", {})
    tz = data.get("timezone", "local")

    resp = {
        "location": place or {"lat": lat, "lon": lon},
        "timezone": tz,
        "current": {
            "time": current.get("time"),
            "temperature_c": current.get("temperature"),
            "temperature_f": round(celsius_to_f(current.get("temperature", 0.0)), 1) if current.get("temperature") is not None else None,
            "windspeed": current.get("windspeed"),
            "winddirection": current.get("winddirection"),
            "weathercode": current.get("weathercode")
        },
        "daily": {
            "time": daily.get("time", []),
            "tmax_c": daily.get("temperature_2m_max", []),
            "tmin_c": daily.get("temperature_2m_min", []),
            "precip_sum_mm": daily.get("precipitation_sum", []),
            "wind_max": daily.get("wind_speed_10m_max", []),
            "weathercode": daily.get("weathercode", [])
        }
    }
    return jsonify(resp)

import os

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5050))
    app.run(host="0.0.0.0", port=port, debug=False)