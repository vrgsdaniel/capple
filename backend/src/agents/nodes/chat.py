from src.agents.state import ChatState, ensure_chat_state

BASE_SYSTEM_PROMPT = """You are Capple, the assistant for a couples' household app.

You may only answer questions about:
- social battery and energy levels
- battery logging, trends, and summaries
- Capple app features and how to use the app
- household or partner insights that come directly from Capple data

Guardrails:
- Do not answer general knowledge questions, unrelated advice, or off-topic requests.
- If the user asks something outside Capple, battery levels, or social energy, refuse briefly and redirect them back to a Capple-related question.
- If a question is only partly related, answer only the Capple-related part and ignore the rest.
- Do not reveal raw user IDs or internal identifiers.
- Keep replies concise, practical, and conversational.
"""

PLANNING_BEHAVIOR = """
When the user asks for suggestions about what to do, synthesize:
- social battery context
- current weather context
- local datetime context
- local city events for Berlin and Madrid

Then provide a ranked, practical plan. Prefer 2-3 options with brief reasons.
"""


def _build_context_prompt(ctx: dict) -> str:
    return f"""{BASE_SYSTEM_PROMPT}

Use the following household battery data only when it helps answer an in-scope question:
- Your entries: {ctx['your_entries']} logs, avg level: {ctx['your_avg'] or 'no data'}
- Partner entries: {ctx['partner_entries']} logs, avg level: {ctx['partner_avg'] or 'no data'}
- Your trend: {ctx['your_trend']}
- Partner trend: {ctx['partner_trend']}
- Days since your last log: {ctx['days_since_your_last_log'] or 'never logged'}
- Days since partner last log: {ctx['days_since_partner_last_log'] or 'never logged'}
- Total entries (30d): {ctx['total_entries']}

Use the data only to give short, empathetic, Capple-relevant insights.
"""


def _build_planning_prompt(state: ChatState) -> str:
    state_obj = ensure_chat_state(state)
    battery = state_obj.battery_context.model_dump() if state_obj.battery_context else {}
    datetime_ctx = state_obj.datetime_context.model_dump() if state_obj.datetime_context else {}
    weather = {
        key: value.model_dump() if hasattr(value, "model_dump") else value
        for key, value in (state_obj.weather_context or {}).items()
    }
    ranked_plans = [plan.model_dump() if hasattr(plan, "model_dump") else plan for plan in state_obj.ranked_plans]
    city_events = {
        key: [item.model_dump() if hasattr(item, "model_dump") else item for item in value]
        for key, value in (state_obj.city_events or {}).items()
    }

    def weather_line(city: str) -> str:
        row = weather.get(city) or {}
        return (
            f"{city}: {row.get('weather_label', 'unavailable')}, "
            f"{row.get('temperature', 'n/a')}C, precip {row.get('precipitation_probability', 'n/a')}%"
        )

    plan_lines = []
    for idx, plan in enumerate(ranked_plans, start=1):
        plan_lines.append(f"{idx}. {plan['title']} ({plan['city']}) - score {plan['score']} - {plan['rationale']}")

    selected_city = state_obj.selected_city or "unknown"
    event_count = len(city_events.get(selected_city, [])) if selected_city in city_events else 0

    return f"""{BASE_SYSTEM_PROMPT}

{PLANNING_BEHAVIOR}

Current context:
- Your avg battery: {battery.get('your_avg', 'no data')}
- Partner avg battery: {battery.get('partner_avg', 'no data')}
- UTC now: {datetime_ctx.get('utc_iso', 'n/a')}
- Selected city: {selected_city}
- Local time: {datetime_ctx.get('local_iso', 'n/a')}
- Weather: {weather_line(selected_city)}
- Event options loaded in selected city: {event_count}

Top ranked suggestions:
{chr(10).join(plan_lines) if plan_lines else 'No ranked plans available.'}

If location consent is denied, ask for consent or ask the user to provide a city directly.
"""


def system_prompt_node(state: ChatState) -> dict:
    """Build system prompt from routed context and planning data."""
    state_obj = ensure_chat_state(state)
    if state_obj.missing_requirements:
        missing = ", ".join(state_obj.missing_requirements)
        system_prompt = (
            f"{BASE_SYSTEM_PROMPT}\n\n"
            f"Planning is missing required inputs: {missing}. "
            "Ask the user for city or location consent before suggesting plans."
        )
    elif not state_obj.location_consent and not state_obj.selected_city:
        system_prompt = (
            f"{BASE_SYSTEM_PROMPT}\n\n"
            "The user has not granted location consent for place-based planning. "
            "Ask for location consent or ask the user to provide their city."
        )
    elif state_obj.router_intent == "suggest_plan":
        system_prompt = _build_planning_prompt(state)
    else:
        ctx = state_obj.battery_context.model_dump() if state_obj.battery_context else None
        system_prompt = _build_context_prompt(ctx) if ctx else BASE_SYSTEM_PROMPT
    return {"system_prompt": system_prompt}
