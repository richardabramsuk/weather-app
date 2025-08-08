# Weather App (Open‑Meteo, no API key)

A small Flask app that fetches current conditions and a daily forecast from Open‑Meteo (free, no key). You can run it locally with a double‑click, or deploy it to a web host to access from your phone.

## Run locally (Windows/Mac)
1. Install Python 3.10+.
2. Double‑click `run.bat` (Windows) or `run.command` (Mac: first run `chmod +x run.command`).
3. When it says "Running on http://127.0.0.1:5050", open that address in your browser.
4. Use "Use My Location" or type a city (e.g., Glasgow).

## Package as a one‑file app (optional)
You can create a single double‑clickable file using PyInstaller:

```bash
pip install pyinstaller
pyinstaller --onefile --add-data "templates:templates" --add-data "static:static" app.py
# The executable will appear in dist/app (Windows: app.exe, macOS: app)
```

## Docker (for easy hosting)
```bash
docker build -t weather-app-open-meteo .
docker run -p 5050:5050 weather-app-open-meteo
```

## Deploy to Render (example)
- Connect this folder to a new Render Web Service using the Dockerfile.
- Set the port to 5050 (Render will use it automatically from the Dockerfile).
- Use the free plan to start. URL will look like: `https://your-service.onrender.com/`.

## Notes
- No API keys required (Open‑Meteo).
- Location is client‑side via browser geolocation or by city name using Open‑Meteo geocoding.
- If you prefer a specific UK provider later (e.g., Met Office DataHub), the code can be adapted.