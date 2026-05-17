from __future__ import annotations

from datetime import datetime, timezone, timedelta
from typing import Any

from pydantic import BaseModel, Field
from langchain.tools import ToolRuntime
from langchain_core.tools import tool

from src.agents.state import BatteryContext


class AgentContext(BaseModel):
    db_client: Any = Field(exclude=True)
    household_id: str = ""
    user_id: str = ""


def _compute_trend(daily_avgs: list[float]) -> str:
    if len(daily_avgs) < 3:
        return "insufficient_data"
    first_half = sum(daily_avgs[: len(daily_avgs) // 2]) / (len(daily_avgs) // 2)
    second_half = sum(daily_avgs[len(daily_avgs) // 2 :]) / (len(daily_avgs) - len(daily_avgs) // 2)
    diff = second_half - first_half
    if diff > 5.0:
        return "improving"
    if diff < -5.0:
        return "declining"
    return "stable"


@tool("get_battery_context")
def get_battery_context(
    runtime: ToolRuntime[AgentContext] | None = None,
) -> BatteryContext:
    """Get household social battery context for the last 30 days."""
    if runtime is None or runtime.context is None:
        raise ValueError("runtime context is required for get_battery_context")

    ctx = runtime.context
    db = ctx.db_client
    household_id = ctx.household_id
    user_id = ctx.user_id

    if not household_id or not user_id:
        raise ValueError("runtime context must include household_id and user_id")

    now = datetime.now(timezone.utc)
    since = (now - timedelta(days=30)).isoformat()
    end = now.isoformat()
    logs = db.find_battery_logs_by_household(household_id, since, end)

    your_logs = [log for log in logs if log["user_id"] == user_id]
    partner_logs = [log for log in logs if log["user_id"] != user_id]

    def avg(entries: list[dict]) -> float | None:
        if not entries:
            return None
        return round(sum(e["level"] for e in entries) / len(entries), 1)

    def days_since_last(entries: list[dict]) -> int | None:
        if not entries:
            return None
        last = max(entries, key=lambda e: e["effective_at"])
        last_dt = datetime.fromisoformat(last["effective_at"].replace("Z", "+00:00"))
        return (datetime.now(timezone.utc) - last_dt).days

    def daily_avgs(entries: list[dict]) -> list[float]:
        by_day: dict[str, list[float]] = {}
        for entry in entries:
            day = entry["effective_at"][:10]
            by_day.setdefault(day, []).append(entry["level"])
        return [sum(values) / len(values) for values in by_day.values()]

    return BatteryContext(
        total_entries=len(logs),
        your_entries=len(your_logs),
        partner_entries=len(partner_logs),
        your_avg=avg(your_logs),
        partner_avg=avg(partner_logs),
        your_trend=_compute_trend(daily_avgs(your_logs)),
        partner_trend=_compute_trend(daily_avgs(partner_logs)),
        days_since_your_last_log=days_since_last(your_logs),
        days_since_partner_last_log=days_since_last(partner_logs),
    )
