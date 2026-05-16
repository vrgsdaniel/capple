from __future__ import annotations

from langchain_core.tools import tool


def _energy_band(battery_context: dict) -> str:
    values = [v for v in [battery_context.get("your_avg"), battery_context.get("partner_avg")] if isinstance(v, (int, float))]
    if not values:
        return "medium"
    avg_level = sum(values) / len(values)
    if avg_level < 35:
        return "low"
    if avg_level < 70:
        return "medium"
    return "high"


@tool("rank_city_plans")
def rank_city_plans(
    battery_context: dict,
    weather_context: dict,
    city_events: dict,
) -> list[dict]:
    """Rank city plans deterministically using battery, weather and events context."""
    band = _energy_band(battery_context or {})
    plans: list[dict] = []

    for _, events in (city_events or {}).items():
        for event in events:
            city = event.get("city", "")
            category = event.get("category", "")
            weather = (weather_context or {}).get(city, {})
            precipitation = weather.get("precipitation_probability")
            weather_label = weather.get("weather_label", "unknown")

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
                {
                    "title": event.get("title", "Suggested local activity"),
                    "city": city,
                    "rationale": (
                        f"Matches {band} social energy, considers {city} weather ({weather_label}), "
                        "and aligns with local event availability."
                    ),
                    "score": score,
                    "recommended_for": "couple",
                    "best_time": event.get("start_iso", ""),
                }
            )

    return sorted(plans, key=lambda item: item["score"], reverse=True)[:3]
