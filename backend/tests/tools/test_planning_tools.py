from src.agents.state import BatteryContext, CityEvent, WeatherContext
from src.agents.tools.planning_tools import create_city_plans_tool


def test_rank_city_plans_orders_highest_scores_first_and_limits_to_three():
    battery_context = BatteryContext(your_avg=80, partner_avg=75)
    weather_context = WeatherContext(city="Berlin", weather_label="clear", precipitation_probability=10)
    city_events = {
        "Berlin": [
            CityEvent(title="Walk", city="Berlin", category="outdoor", start_iso="2026-05-17T19:00:00+02:00"),
            CityEvent(title="Food", city="Berlin", category="social_food", start_iso="2026-05-17T20:00:00+02:00"),
        ],
        "Madrid": [
            CityEvent(title="Rain walk", city="Madrid", category="outdoor", start_iso="2026-05-17T19:00:00+02:00"),
            CityEvent(title="Cinema", city="Madrid", category="low_energy", start_iso="2026-05-17T18:00:00+02:00"),
        ],
    }

    ranked = create_city_plans_tool(
        battery_context,
        weather_context,
        city_events,
    )

    assert len(ranked) == 3
    assert ranked[0].score >= ranked[1].score >= ranked[2].score
    assert ranked[0].city == "Berlin"
