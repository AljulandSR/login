from fastapi import APIRouter, HTTPException
import httpx
import os
from dotenv import load_dotenv

load_dotenv()

router = APIRouter(prefix="/weather", tags=["weather"])

OPENWEATHER_KEY = os.getenv("OPENWEATHER_KEY", "")

@router.get("/")
async def get_weather(city: str = "Muscat"):
    """Get current weather for Oman locations"""
    try:
        if not OPENWEATHER_KEY:
            # Return mock data if no API key
            return {
                "city": city,
                "temp": 28,
                "temp_min": 22,
                "temp_max": 32,
                "condition": "Clear",
                "description": "Clear sky",
                "humidity": 45,
                "wind_speed": 12,
                "icon": "01d"
            }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.openweathermap.org/data/2.5/weather",
                params={
                    "q": f"{city},OM",
                    "appid": OPENWEATHER_KEY,
                    "units": "metric"
                },
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            
            return {
                "city": data["name"],
                "temp": round(data["main"]["temp"]),
                "temp_min": round(data["main"]["temp_min"]),
                "temp_max": round(data["main"]["temp_max"]),
                "condition": data["weather"][0]["main"],
                "description": data["weather"][0]["description"],
                "humidity": data["main"]["humidity"],
                "wind_speed": round(data["wind"]["speed"] * 3.6),  # Convert m/s to km/h
                "icon": data["weather"][0]["icon"]
            }
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=502, detail=f"Weather API error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))