from src.agents.tools import context_tools as context_module


class _FakeDB:
    def __init__(self, logs):
        self._logs = logs

    def find_battery_logs_by_household(self, household_id, since, end):
        assert household_id == "hh-1"
        assert since
        assert end
        return self._logs


def test_get_battery_context_builds_expected_summary(monkeypatch):
    logs = [
        {"user_id": "u1", "level": 40, "effective_at": "2026-05-16T09:00:00+00:00"},
        {"user_id": "u1", "level": 60, "effective_at": "2026-05-17T09:00:00+00:00"},
        {"user_id": "u2", "level": 70, "effective_at": "2026-05-16T10:00:00+00:00"},
    ]

    monkeypatch.setattr(context_module, "get_db", lambda: _FakeDB(logs))

    result = context_module.get_battery_context.invoke({"household_id": "hh-1", "user_id": "u1"})

    assert result["total_entries"] == 3
    assert result["your_entries"] == 2
    assert result["partner_entries"] == 1
    assert result["your_avg"] == 50.0
    assert result["partner_avg"] == 70.0


def test_get_datetime_context_includes_city_and_iso_timestamps():
    result = context_module.get_datetime_context.invoke({"city": "Berlin"})

    assert result["city"] == "Berlin"
    assert "T" in result["utc_iso"]
    assert "T" in result["local_iso"]
