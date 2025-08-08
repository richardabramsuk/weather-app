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
        "hourly": "temperature_2m,relative_humidity_2m,precipitation,precipitation_probability,wind_speed_10m,wind_direction_10m,apparent_temperature",
        "daily": "weathercode,temperature_2m_max,temperature_2m_min,precipitation_sum,wind_speed_10m_max",
        "timezone": "auto"
    }
    r = requests.get(url, params=params, timeout=10)
    r.raise_for_status()
    return r.json()


def get_satellite_image_url(lat: float, lon: float):
    """Get satellite imagery URL for precipitation radar"""
    # Using Windy's precipitation radar service which is more reliable
    # This provides real-time precipitation radar imagery
    return f"https://embed.windy.com/embed2.html?lat={lat}&lon={lon}&zoom=8&level=surface&overlay=rain&product=ecmwf&menu=&message=&marker=&calendar=&pressure=&type=map&location=coordinates&detail=&metricWind=default&metricTemp=%C2%B0C&radarRange=-1"


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
    satellite_url = get_satellite_image_url(lat, lon)

    # Normalise a minimal payload
    current = data.get("current_weather", {})
    daily = data.get("daily", {})
    tz = data.get("timezone", "local")

    # Get hourly data for next 24 hours
    hourly = data.get("hourly", {})
    hourly_times = hourly.get("time", [])
    
    # Safe fallback for current time
    try:
        current_time = datetime.now().isoformat()
    except:
        current_time = hourly_times[0] if hourly_times else ""
    
    # Find current hour index and get next 24 hours
    current_hour_index = 0
    if hourly_times:
        for i, time_str in enumerate(hourly_times):
            if time_str > current_time:
                current_hour_index = i
                break
    
    next_24_hours = []
    if hourly_times:
        for i in range(current_hour_index, min(current_hour_index + 24, len(hourly_times))):
            next_24_hours.append({
                "time": hourly_times[i],
                "temperature_c": hourly.get("temperature_2m", [])[i] if i < len(hourly.get("temperature_2m", [])) else None,
                "temperature_f": round(celsius_to_f(hourly.get("temperature_2m", [])[i]), 1) if i < len(hourly.get("temperature_2m", [])) and hourly.get("temperature_2m", [])[i] is not None else None,
                "apparent_temperature_c": hourly.get("apparent_temperature", [])[i] if i < len(hourly.get("apparent_temperature", [])) else None,
                "apparent_temperature_f": round(celsius_to_f(hourly.get("apparent_temperature", [])[i]), 1) if i < len(hourly.get("apparent_temperature", [])) and hourly.get("apparent_temperature", [])[i] is not None else None,
                "wind_speed": hourly.get("wind_speed_10m", [])[i] if i < len(hourly.get("wind_speed_10m", [])) else None,
                "wind_direction": hourly.get("wind_direction_10m", [])[i] if i < len(hourly.get("wind_direction_10m", [])) else None,
                "precipitation": hourly.get("precipitation", [])[i] if i < len(hourly.get("precipitation", [])) else None,
                "precipitation_probability": hourly.get("precipitation_probability", [])[i] if i < len(hourly.get("precipitation_probability", [])) else None
            })

    resp = {
        "location": place or {"lat": lat, "lon": lon},
        "timezone": tz,
        "satellite_url": satellite_url,
        "current": {
            "time": current.get("time"),
            "temperature_c": current.get("temperature"),
            "temperature_f": round(celsius_to_f(current.get("temperature", 0.0)), 1) if current.get("temperature") is not None else None,
            "apparent_temperature_c": hourly.get("apparent_temperature", [None])[0] if hourly.get("apparent_temperature") and len(hourly.get("apparent_temperature", [])) > 0 else None,
            "apparent_temperature_f": round(celsius_to_f(hourly.get("apparent_temperature", [None])[0]), 1) if hourly.get("apparent_temperature") and len(hourly.get("apparent_temperature", [])) > 0 and hourly.get("apparent_temperature")[0] is not None else None,
            "windspeed": current.get("windspeed"),
            "winddirection": current.get("winddirection"),
            "weathercode": current.get("weathercode"),
            "relative_humidity": hourly.get("relative_humidity_2m", [None])[0] if hourly.get("relative_humidity_2m") and len(hourly.get("relative_humidity_2m", [])) > 0 else None,
            "precipitation": hourly.get("precipitation", [None])[0] if hourly.get("precipitation") and len(hourly.get("precipitation", [])) > 0 else None
        },
        "hourly_24h": next_24_hours,
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


@app.route("/api/travel")
def api_travel():
    from_address = request.args.get("from", "").strip()
    to_address = request.args.get("to", "").strip()
    
    if not from_address or not to_address:
        return jsonify({"error": "Missing from or to address"}), 400
    
    # For now, return mock data since we don't have Google Maps API key
    # In a real implementation, you would call Google Maps Directions API
    mock_routes = {
        "outbound": {
            "duration": "25 min",
            "distance": "12.3 km",
            "traffic_status": "Moderate traffic",
            "traffic_level": "moderate",
            "alerts": [
                {
                    "severity": "medium",
                    "description": "Slow traffic on M77 near junction 3"
                },
                {
                    "severity": "low",
                    "description": "Minor delays on A77"
                }
            ]
        },
        "return": {
            "duration": "28 min",
            "distance": "12.3 km",
            "traffic_status": "Heavy traffic",
            "traffic_level": "heavy",
            "alerts": [
                {
                    "severity": "high",
                    "description": "Major delays on M77 southbound"
                }
            ]
        }
    }
    
    return jsonify({
        "from": from_address,
        "to": to_address,
        "routes": mock_routes
    })

import os

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5050))
    app.run(host="0.0.0.0", port=port, debug=False)