from __future__ import annotations

from src.agents.state import ChatState, CityEvent, SuggestedPlan

NODE_NAME = "planner_agent"


def _household_energy_band(state: ChatState) -> str:
    battery = state.get("battery_context")
    if not battery:
        return "medium"

    values = [v for v in [battery.get("your_avg"), battery.get("partner_avg")] if isinstance(v, (int, float))]
    if not values:
        return "medium"

    avg_level = sum(values) / len(values)
    if avg_level < 35:
        return "low"
    if avg_level < 70:
        return "medium"
    return "high"


def _weather_penalty(city: str, state: ChatState, category: str) -> int:
    weather = (state.get("weather_context") or {}).get(city)
    if not weather:
        return 0

    precipitation = weather.get("precipitation_probability")
    if category == "outdoor" and isinstance(precipitation, int) and precipitation >= 50:
        return -20

    return 0


def _energy_fit_bonus(energy_band: str, category: str) -> int:
    if energy_band == "low":
        if category in {"low_energy", "culture"}:
            return 18
        if category == "outdoor":
            return -8
    elif energy_band == "medium":
        if category in {"social_food", "culture", "outdoor"}:
            return 12
    else:
        if category in {"outdoor", "social_food"}:
            return 18
    return 0


def _recommended_for(state: ChatState) -> str:
    battery = state.get("battery_context")
    if not battery:
        return "couple"

    your_avg = battery.get("your_avg")
    partner_avg = battery.get("partner_avg")
    if not isinstance(your_avg, (int, float)) or not isinstance(partner_avg, (int, float)):
        return "couple"

    if abs(your_avg - partner_avg) >= 25:
        return "solo_or_flexible"

    return "couple"


def _build_plan(event: CityEvent, state: ChatState, energy_band: str) -> SuggestedPlan:
    base_score = 55
    category = event.get("category", "")
    city = event.get("city", "")

    score = base_score
    score += _energy_fit_bonus(energy_band, category)
    score += _weather_penalty(city, state, category)

    weather = (state.get("weather_context") or {}).get(city, {})
    weather_label = weather.get("weather_label", "unknown weather")
    rationale = (
        f"Matches {energy_band} social energy, considers {city} weather ({weather_label}), "
        "and aligns with upcoming local city events."
    )

    return {
        "title": event.get("title", "Suggested local activity"),
        "city": city,
        "rationale": rationale,
        "score": score,
        "recommended_for": _recommended_for(state),
        "best_time": event.get("start_iso", ""),
    }


def planner_node(state: ChatState) -> dict:
    """Rank city event plans using battery, weather, and time context."""
    if state.get("router_intent") != "suggest_plan" or not state.get("location_consent", False):
        return {"ranked_plans": []}

    city_events = state.get("city_events") or {}
    energy_band = _household_energy_band(state)

    plans: list[SuggestedPlan] = []
    for events in city_events.values():
        for event in events:
            plans.append(_build_plan(event, state, energy_band))

    ranked = sorted(plans, key=lambda plan: plan["score"], reverse=True)
    return {"ranked_plans": ranked[:3]}
