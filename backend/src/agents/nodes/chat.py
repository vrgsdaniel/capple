from langchain_core.messages import SystemMessage
from src.agents.state import ChatState


def system_prompt_node(state: ChatState) -> dict:
    """Build system prompt based on battery context."""
    ctx = state.get("battery_context")
    if not ctx:
        system_prompt = "You are Capple, a helpful assistant for a couple's household app."
    else:
        system_prompt = f"""You are Capple, a warm and insightful assistant for a couple's household app.

You have access to social battery data for this household over the last 30 days.

BATTERY DATA:
- Your entries: {ctx['your_entries']} logs, avg level: {ctx['your_avg'] or 'no data'}
- Partner entries: {ctx['partner_entries']} logs, avg level: {ctx['partner_avg'] or 'no data'}
- Your trend: {ctx['your_trend']}
- Partner trend: {ctx['partner_trend']}
- Days since your last log: {ctx['days_since_your_last_log'] or 'never logged'}
- Days since partner last log: {ctx['days_since_partner_last_log'] or 'never logged'}
- Total entries (30d): {ctx['total_entries']}

Use this data to give personalised, empathetic insights about how both people are doing.
If data is sparse (fewer than 5 entries each), encourage more consistent logging.
Keep responses concise and conversational — you are a companion, not a report generator.
Never reveal raw user IDs. Refer to the users as "you" and "your partner".
"""
    return {"system_prompt": system_prompt}


def chat_node(state: ChatState) -> dict:
    """LLM node that calls the chatbot with system prompt and messages.

    The state must contain:
    - chatbot: Chatbot instance
    - system_prompt: System prompt string
    - messages: List of messages from LangChain
    """
    chatbot = state.get("chatbot")
    system_prompt = state.get("system_prompt", "You are a helpful assistant.")

    if not chatbot:
        raise ValueError("Chatbot not found in state")

    messages = [SystemMessage(content=system_prompt)] + state["messages"]

    # Call the LLM
    response = chatbot.invoke(messages)

    return {"messages": [response]}
