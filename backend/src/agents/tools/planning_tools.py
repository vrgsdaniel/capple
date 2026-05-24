from __future__ import annotations

from langchain_core.tools import tool

from src.agents.graph import GraphContext
from src.agents.state import BatteryContext, CityEvent, SuggestedPlan, WeatherContext
from src.agents.tools.logging_decorator import log_tool_call


def _energy_band(battery_context: BatteryContext) -> str:
    values = [v for v in [battery_context.your_avg, battery_context.partner_avg] if isinstance(v, (int, float))]
    if not values:
        return "medium"
    avg_level = sum(values) / len(values)
    if avg_level < 35:
        return "low"
    if avg_level < 70:
        return "medium"
    return "high"


def create_city_plans_tool(
    battery_context: BatteryContext | None,
    weather_context: WeatherContext | None,
    city_events: dict[str, list[CityEvent]] | None,
) -> list[SuggestedPlan]:
    """Rank city plans deterministically using battery, weather and events context."""
    band = _energy_band(battery_context or BatteryContext(your_avg=0, partner_avg=0))
    plans: list[SuggestedPlan] = []

    for _, events in (city_events or {}).items():
        for event in events:
            city = event.city or ""
            category = event.category or ""
            weather = weather_context or WeatherContext()
            precipitation = weather.precipitation_probability
            weather_label = weather.weather_label or "unknown"

            score = 55
            if band == "low" and category in {"low_energy", "culture"}:
                score += 18
            if band == "high" and category in {"outdoor", "social_food"}:
                score += 18
            if band == "medium" and category in {"social_food", "culture", "outdoor"}:
                score += 12
            if category == "outdoor" and isinstance(precipitation, int) and precipitation >= 50:
                score -= 20

            plans.append(
                SuggestedPlan(
                    title=event.title or "Suggested local activity",
                    city=city,
                    rationale=(
                        f"Matches {band} social energy, considers {city} weather ({weather_label}), "
                        "and aligns with local event availability."
                    ),
                    score=score,
                    recommended_for="couple",
                    best_time=event.start_iso or "",
                )
            )

    return sorted(plans, key=lambda item: item.score, reverse=True)[:3]


def create_plan_ranker_tool(context: GraphContext) -> tool:
    @tool("get_rank_city_plans_tool")
    @log_tool_call("get_rank_city_plans_tool")
    def get_rank_city_plans_tool(
        battery_context: BatteryContext | None = None,
        weather_context: WeatherContext | None = None,
        city_events: dict[str, list[CityEvent]] | None = None,
    ) -> list[SuggestedPlan]:
        """Rank city plans deterministically using battery, weather and events context."""
        return create_city_plans_tool(
            battery_context,
            weather_context,
            city_events,
        )

    return get_rank_city_plans_tool
