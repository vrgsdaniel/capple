from backend.src.agents.graph import GraphContext
from src.agents.tools import battery_tool


class _FakeDB:
    def __init__(self, logs, expected_household_id="hh-1"):
        self._logs = logs
        self._expected_household_id = expected_household_id

    def find_battery_logs_by_household(self, household_id, since, end):
        assert household_id == self._expected_household_id
        assert since
        assert end
        return self._logs


def test_get_battery_tool_builds_expected_summary():
    logs = [
        {"user_id": "u1", "level": 40, "effective_at": "2026-05-16T09:00:00+00:00"},
        {"user_id": "u1", "level": 60, "effective_at": "2026-05-17T09:00:00+00:00"},
        {"user_id": "u2", "level": 70, "effective_at": "2026-05-16T10:00:00+00:00"},
    ]

    result = battery_tool.build_battery_tool(
        _FakeDB(logs, expected_household_id="hh-1"),
        "hh-1",
        "u1",
    )

    assert result.total_entries == 3
    assert result.your_entries == 2
    assert result.partner_entries == 1
    assert result.your_avg == 50.0
    assert result.partner_avg == 70.0


def test_get_battery_tool_prefers_runtime_context_values():
    logs = [
        {"user_id": "u-runtime", "level": 50, "effective_at": "2026-05-16T09:00:00+00:00"},
        {"user_id": "u-partner", "level": 70, "effective_at": "2026-05-16T10:00:00+00:00"},
    ]

    result = battery_tool.build_battery_tool(
        _FakeDB(logs, expected_household_id="hh-runtime"),
        "hh-runtime",
        "u-runtime",
    )

    assert result.total_entries == 2
    assert result.your_entries == 1
    assert result.partner_entries == 1


def test_create_get_battery_tool_tool_returns_invokable_tool():
    logs = [
        {"user_id": "u1", "level": 40, "effective_at": "2026-05-16T09:00:00+00:00"},
        {"user_id": "u2", "level": 70, "effective_at": "2026-05-16T10:00:00+00:00"},
    ]
    ctx = GraphContext(
        db_client=_FakeDB(logs, expected_household_id="hh-tool"),
        household_id="hh-tool",
        user_id="u1",
    )

    tool = battery_tool.create_battery_context_tool(ctx)

    result = tool.invoke({})

    assert result.total_entries == 2
    assert result.your_entries == 1
    assert result.partner_entries == 1
