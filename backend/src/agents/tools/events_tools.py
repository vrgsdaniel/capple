from __future__ import annotations

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from langchain_core.tools import tool

from src.agents.state import CityEvent


def _next_day_at(now: datetime, day_offset: int, hour: int) -> str:
    dt = (now + timedelta(days=day_offset)).replace(hour=hour, minute=0, second=0, microsecond=0)
    return dt.isoformat()


def _berlin_events(now_utc: datetime) -> list[CityEvent]:
    berlin_now = now_utc.astimezone(ZoneInfo("Europe/Berlin"))
    return [
        {
            "city": "Berlin",
            "title": "Tempelhofer Feld sunset walk",
            "category": "outdoor",
            "start_iso": _next_day_at(berlin_now, 0, 19),
            "source": "local_adapter_berlin",
        },
        {
            "city": "Berlin",
            "title": "Museum Island late opening",
            "category": "culture",
            "start_iso": _next_day_at(berlin_now, 1, 18),
            "source": "local_adapter_berlin",
        },
        {
            "city": "Berlin",
            "title": "Neighborhood coffee and board games",
            "category": "low_energy",
            "start_iso": _next_day_at(berlin_now, 1, 16),
            "source": "local_adapter_berlin",
        },
    ]


def _madrid_events(now_utc: datetime) -> list[CityEvent]:
    madrid_now = now_utc.astimezone(ZoneInfo("Europe/Madrid"))
    return [
        {
            "city": "Madrid",
            "title": "Retiro Park morning stroll",
            "category": "outdoor",
            "start_iso": _next_day_at(madrid_now, 0, 10),
            "source": "local_adapter_madrid",
        },
        {
            "city": "Madrid",
            "title": "La Latina tapas route",
            "category": "social_food",
            "start_iso": _next_day_at(madrid_now, 0, 20),
            "source": "local_adapter_madrid",
        },
        {
            "city": "Madrid",
            "title": "Matinee cinema session",
            "category": "low_energy",
            "start_iso": _next_day_at(madrid_now, 1, 17),
            "source": "local_adapter_madrid",
        },
    ]


_ADAPTER_REGISTRY = {
    "Berlin": _berlin_events,
    "Madrid": _madrid_events,
}


def get_city_events(cities: list[str], now_utc: datetime | None = None) -> dict[str, list[CityEvent]]:
    """Return local city events from a registry of city adapters."""
    current = now_utc or datetime.now(tz=ZoneInfo("UTC"))
    result: dict[str, list[CityEvent]] = {}

    for city in cities:
        adapter = _ADAPTER_REGISTRY.get(city)
        if not adapter:
            result[city] = []
            continue
        result[city] = adapter(current)

    return result


@tool("get_city_events")
def get_city_events_tool(cities: list[str]) -> dict:
    """Get event candidates for supported cities from the city adapter registry."""
    return get_city_events(cities)
