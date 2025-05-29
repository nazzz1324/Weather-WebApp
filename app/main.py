from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from app.database import init_db
from app.crud import save_search, get_stats, get_recent_history
import httpx
from datetime import datetime

app = FastAPI()

app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

init_db()

@app.get("/", response_class=HTMLResponse)
async def get_home(request: Request):
    recent = get_recent_history()
    return templates.TemplateResponse("index.html", {
        "request": request,
        "history": recent
    })

@app.get("/weather", response_class=HTMLResponse)
async def get_weather(request: Request, city: str):
    weather_data = await fetch_weather(city)
    if isinstance(weather_data, list):
        save_search(city)
    return templates.TemplateResponse("index.html", {
        "request": request,
        "weather": weather_data,
        "city": city,
        "history": get_recent_history()
    })

@app.get("/stats")
async def stats():
    return get_stats()

def get_icon_filename(code: int):
    mapping = {
        0: "0.png",   # солнечно
        1: "1.png",   # переменная облачность
        2: "2.png",   # облачно
        3: "3.png",   # пасмурно
        45: "4.png",  # туман
        48: "4.png",
        51: "5.png",  # морось
        53: "5.png",
        55: "5.png",
        61: "5.png",  # дождь
        63: "5.png",
        65: "8.png",  # сильный дождь
        66: "5.png",
        67: "8.png",
        71: "7.png",  # снег
        73: "7.png",
        75: "7.png",
        77: "7.png",
        85: "7.png",
        86: "7.png",
        80: "6.png",  # дождь с прояснениями
        81: "5.png",
        82: "8.png",
        95: "9.png",  # гроза
        96: "9.png",
        99: "9.png"
    }
    return mapping.get(code, "2.png")

async def fetch_weather(city: str):
    async with httpx.AsyncClient() as client:
        geo_resp = await client.get(
            f"https://nominatim.openstreetmap.org/search?format=json&q={city}"
        )
        geo_data = geo_resp.json()
        if not geo_data:
            return {"error": "Город не найден"}

        lat = geo_data[0]["lat"]
        lon = geo_data[0]["lon"]

        weather_url = (
            f"https://api.open-meteo.com/v1/forecast"
            f"?latitude={lat}&longitude={lon}&daily=temperature_2m_max,"
            f"temperature_2m_min,precipitation_sum,weathercode&timezone=auto"
        )
        weather_resp = await client.get(weather_url)
        data = weather_resp.json()

        # Обработка
        daily = data.get("daily")
        if not daily:
            return {"error": "Нет данных"}

        forecast = []
        for i in range(7):
            forecast.append({
                "date": daily["time"][i],
                "max": daily["temperature_2m_max"][i],
                "min": daily["temperature_2m_min"][i],
                "precipitation": daily["precipitation_sum"][i],
                "code": daily["weathercode"][i],
                "icon": get_icon_filename(daily["weathercode"][i])  # ← ДОБАВЛЕНО
            })

        return forecast
