from src.agents.nodes.chat import system_prompt_node


def test_system_prompt_includes_ranked_plans_for_planning():
    state = {
        "router_intent": "suggest_plan",
        "location_consent": True,
        "battery_context": {"your_avg": 60, "partner_avg": 55},
        "datetime_context": {
            "utc_iso": "2026-05-16T12:00:00+00:00",
            "berlin_local_iso": "2026-05-16T14:00:00+02:00",
            "madrid_local_iso": "2026-05-16T14:00:00+02:00",
        },
        "weather_context": {
            "Berlin": {
                "weather_label": "clear",
                "temperature": 22,
                "precipitation_probability": 10,
            },
            "Madrid": {
                "weather_label": "clear",
                "temperature": 24,
                "precipitation_probability": 0,
            },
        },
        "city_events": {
            "Berlin": [{"title": "A"}],
            "Madrid": [{"title": "B"}],
        },
        "ranked_plans": [
            {
                "title": "Tempelhofer Feld sunset walk",
                "city": "Berlin",
                "score": 82,
                "rationale": "Good weather and social battery alignment.",
                "recommended_for": "couple",
                "best_time": "2026-05-16T19:00:00+02:00",
            }
        ],
    }

    result = system_prompt_node(state)

    assert "Top ranked suggestions" in result["system_prompt"]
    assert "Tempelhofer Feld sunset walk" in result["system_prompt"]
