from __future__ import annotations

import requests

from langchain_core.tools import tool

from src.agents.graph import GraphContext
from src.agents.state import WeatherContext
from src.agents.tools.logging_decorator import log_tool_call

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


def _geocode_city(city: str) -> tuple[float, float] | None:
    try:
        response = requests.get(
            "https://geocoding-api.open-meteo.com/v1/search",
            params={"name": city, "count": 1, "language": "en", "format": "json"},
            timeout=4,
        )
        response.raise_for_status()
        data = response.json()
    except (requests.RequestException, ValueError):
        return None

    results = data.get("results")
    if not isinstance(results, list) or not results:
        return None

    first = results[0]
    if not isinstance(first, dict):
        return None

    latitude = first.get("latitude")
    longitude = first.get("longitude")
    if not isinstance(latitude, (int, float)) or not isinstance(longitude, (int, float)):
        return None

    return float(latitude), float(longitude)


def get_weather_context_for_city(city: str) -> WeatherContext:
    """Fetch current weather for a city using Open-Meteo.

    Returns a fallback payload when the API is unavailable to keep chat resilient.
    """
    coords = _geocode_city(city)
    if not coords:
        return _build_fallback(city)
    latitude, longitude = coords

    try:
        response = requests.get(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude": latitude,
                "longitude": longitude,
                "current": "temperature_2m,weather_code,precipitation_probability",
                "timezone": "auto",
            },
            timeout=4,
        )
        response.raise_for_status()
        data = response.json()
    except (requests.RequestException, ValueError):
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


def create_weather_tool(context: GraphContext) -> tool:
    @tool("get_weather_context")
    @log_tool_call("get_weather_context")
    def get_weather_context(city: str) -> WeatherContext:
        """Fetch weather context for a city name."""
        return get_weather_context_for_city(city)

    return get_weather_context
