from src.settings import get_llm_settings
from src.agents.state import ChatState, ensure_chat_state

INTENT_CONFIDENCE_THRESHOLD = get_llm_settings().intent_confidence_threshold

SYSTEM_PROMPT_NODE = "system_prompt"

BASE_SYSTEM_PROMPT = """
    You are Capple, the assistant for a couples' household app.
    You may only answer questions about:
    - social battery and energy levels
    - battery logging, trends, and summaries
    - Capple app features and how to use the app
    - household or partner insights that come directly from Capple data
    - planning suggestions based on Capple data, weather, datetime, and local events

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

BATTERY_BEHAVIOR = """
    When the user asks about battery levels, trends, or energy:
    - Use the battery context tool before answering.
    - Ground the response in available battery metrics and trends.
    - If data is missing or insufficient, say so clearly and suggest logging new entries.
    - Keep the response short, empathetic, and practical.
"""

APP_HELP_BEHAVIOR = """
    The user is asking about app usage or troubleshooting.
    Explain Capple features and steps clearly.
    If details are missing, ask one concise follow-up question.
"""


def _build_context_prompt(ctx: dict) -> str:
    return f"""
    {BASE_SYSTEM_PROMPT}
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


def _build_battery_prompt() -> str:
    return f"""
    {BATTERY_BEHAVIOR}
    """


def _build_app_help_prompt() -> str:
    return f"""
    {BASE_SYSTEM_PROMPT}
    {APP_HELP_BEHAVIOR}
    """


def _build_planning_prompt() -> str:
    return f"""
    {PLANNING_BEHAVIOR}
    """


def system_prompt_node(state: ChatState) -> dict:
    """Build system prompt from routed context and planning data."""
    # TODO: set a flag that might bypass the planning agent if confidence is low or requirements are missing, to avoid unnecessary agent calls until we have a better retry mechanism in place
    state_obj = ensure_chat_state(state)
    if state_obj.parser_retry_needed:
        system_prompt = (
            "We could not safely interpret the request right now."
            "Apologize briefly and ask the user to retry their last message."
        )
    elif state_obj.intent_confidence < INTENT_CONFIDENCE_THRESHOLD:
        system_prompt = (
            "The user intent is ambiguous. Ask one concise clarifying question "
            "to determine whether they want battery insights, app help, or plan suggestions."
        )
    elif state_obj.missing_requirements:
        missing = ", ".join(state_obj.missing_requirements)
        system_prompt = (
            f"Planning is missing required inputs: {missing}. Ask the user for their city before suggesting plans."
        )
    elif state_obj.router_intent == "suggest_plan":
        system_prompt = _build_planning_prompt()
    elif state_obj.router_intent == "battery_levels":
        system_prompt = _build_battery_prompt()
    elif state_obj.router_intent == "app_help":
        system_prompt = _build_app_help_prompt()
    elif state_obj.router_intent == "general_chat":
        ctx = (
            state_obj.battery_context.model_dump()
            if hasattr(state_obj.battery_context, "model_dump")
            else state_obj.battery_context
        )
        system_prompt = _build_context_prompt(ctx) if ctx else BASE_SYSTEM_PROMPT
    else:
        system_prompt = BASE_SYSTEM_PROMPT
    return {"system_prompt": system_prompt}
