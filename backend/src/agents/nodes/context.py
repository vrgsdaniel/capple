from datetime import datetime, timezone, timedelta
from src.agents.state import ChatState, BatteryContext
from src.db.db import get_db

# For a future iteration:
# def trend_detector(list_of_index, array_of_data, order=1):
#     result = np.polyfit(list_of_index, list(array_of_data), order)
#     slope = result[-2]
#     return float(slope)

NODE_NAME = "context_assembler"


def compute_trend(daily_avgs: list[float]) -> str:
    min_entries_for_trend = 3
    upper_threshold = 5.0
    if len(daily_avgs) < min_entries_for_trend:
        return "insufficient_data"
    first_half = sum(daily_avgs[: len(daily_avgs) // 2]) / (len(daily_avgs) // 2)
    second_half = sum(daily_avgs[len(daily_avgs) // 2 :]) / (len(daily_avgs) - len(daily_avgs) // 2)
    diff = second_half - first_half
    if diff > upper_threshold:
        return "improving"
    if diff < -upper_threshold:
        return "declining"
    return "stable"


def battery_context_node(state: ChatState) -> dict:
    """Load battery log context for the household into state."""
    db = get_db()
    household_id = state["household_id"]
    user_id = state["user_id"]

    now = datetime.now(timezone.utc)
    since = (now - timedelta(days=30)).isoformat()
    end = now.isoformat()

    logs = db.find_battery_logs_by_household(household_id, since, end)

    your_logs = [log for log in logs if log["user_id"] == user_id]
    partner_logs = [log for log in logs if log["user_id"] != user_id]

    def avg(entries: list) -> float | None:
        if not entries:
            return None
        return round(sum(e["level"] for e in entries) / len(entries), 1)

    def days_since_last(entries: list) -> int | None:
        if not entries:
            return None
        last = max(entries, key=lambda e: e["effective_at"])
        last_dt = datetime.fromisoformat(last["effective_at"].replace("Z", "+00:00"))
        return (datetime.now(timezone.utc) - last_dt).days

    def daily_avgs(entries: list) -> list[float]:
        by_day: dict[str, list[float]] = {}
        for e in entries:
            day = e["effective_at"][:10]
            by_day.setdefault(day, []).append(e["level"])
        return [sum(v) / len(v) for v in by_day.values()]

    context: BatteryContext = {
        "total_entries": len(logs),
        "your_entries": len(your_logs),
        "partner_entries": len(partner_logs),
        "your_avg": avg(your_logs),
        "partner_avg": avg(partner_logs),
        "your_trend": compute_trend(daily_avgs(your_logs)),
        "partner_trend": compute_trend(daily_avgs(partner_logs)),
        "days_since_your_last_log": days_since_last(your_logs),
        "days_since_partner_last_log": days_since_last(partner_logs),
    }

    return {"battery_context": context}
