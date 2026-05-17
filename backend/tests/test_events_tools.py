from datetime import datetime
from zoneinfo import ZoneInfo

from src.agents.tools.events_tools import get_city_events


def test_get_city_events_returns_supported_and_empty_for_unknown_city():
    fixed_now = datetime(2026, 5, 17, 12, 0, tzinfo=ZoneInfo("UTC"))

    result = get_city_events(["Berlin", "Madrid", "Paris"], now_utc=fixed_now)

    assert len(result["Berlin"]) == 3
    assert len(result["Madrid"]) == 3
    assert result["Paris"] == []
    assert all(event["city"] == "Berlin" for event in result["Berlin"])
    assert all(event["city"] == "Madrid" for event in result["Madrid"])
