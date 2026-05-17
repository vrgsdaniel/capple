from __future__ import annotations

from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from langchain_core.tools import tool

from src.agents.state import DateTimeContext


@tool("get_datetime_context")
def get_datetime_context(city: str) -> DateTimeContext:
    """Get UTC and city-local datetime context for planning."""
    timezone_by_city = {
        "Berlin": "Europe/Berlin",
        "Madrid": "Europe/Madrid",
    }
    tz = timezone_by_city.get(city, "UTC")
    now_utc = datetime.now(timezone.utc)
    local_dt = now_utc.astimezone(ZoneInfo(tz))
    return DateTimeContext(
        utc_iso=now_utc.isoformat(),
        local_iso=local_dt.isoformat(),
        city=city,
    )
