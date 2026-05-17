from __future__ import annotations

from json import JSONDecodeError
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import urlopen

from langchain_core.tools import tool

from src.agents.state import WeatherContext

_WEATHER_CODE_LABELS = {
    0: "clear",
    1: "mainly clear",
    2: "partly cloudy",
    3: "overcast",
    45: "fog",
    48: "rime fog",
    51: "light drizzle",
    53: "moderate drizzle",
    55: "dense drizzle",
    61: "light rain",
    63: "moderate rain",
    65: "heavy rain",
    71: "light snow",
    73: "moderate snow",
    75: "heavy snow",
    80: "rain showers",
    81: "rain showers",
    82: "violent rain showers",
    95: "thunderstorm",
}


def _build_fallback(city: str) -> WeatherContext:
    return WeatherContext(
        city=city,
        temperature=None,
        precipitation_probability=None,
        weather_label="unavailable",
    )


def fetch_weather_context_for_city(city: str, latitude: float, longitude: float) -> WeatherContext:
    """Fetch current weather for a city using Open-Meteo.

    Returns a fallback payload when the API is unavailable to keep chat resilient.
    """
    query = urlencode(
        {
            "latitude": latitude,
            "longitude": longitude,
            "current": "temperature_2m,weather_code,precipitation_probability",
            "timezone": "auto",
        }
    )
    url = f"https://api.open-meteo.com/v1/forecast?{query}"

    try:
        with urlopen(url, timeout=4) as response:
            payload = response.read().decode("utf-8")
    except (TimeoutError, HTTPError, URLError):
        return _build_fallback(city)

    try:
        import json

        data = json.loads(payload)
    except (JSONDecodeError, ValueError):
        return _build_fallback(city)

    current = data.get("current")
    if not isinstance(current, dict):
        return _build_fallback(city)

    weather_code = current.get("weather_code")
    weather_label = _WEATHER_CODE_LABELS.get(weather_code, "unknown")

    temperature = current.get("temperature_2m")
    precipitation_probability = current.get("precipitation_probability")

    return WeatherContext(
        city=city,
        temperature=float(temperature) if isinstance(temperature, (int, float)) else None,
        precipitation_probability=(
            int(precipitation_probability) if isinstance(precipitation_probability, (int, float)) else None
        ),
        weather_label=weather_label,
    )


@tool("fetch_weather_context")
def fetch_weather_context(city: str, latitude: float, longitude: float) -> WeatherContext:
    """Fetch weather context for a city and coordinates."""
    return fetch_weather_context_for_city(city, latitude, longitude)
