from src.agents.state import ChatState
from src.agents.tools.events import get_city_events_tool

NODE_NAME = "city_events_agent"
SUPPORTED_CITIES = ["Berlin", "Madrid"]


def city_events_node(state: ChatState) -> dict:
    """Load local event options for supported cities using the adapter registry."""
    city_events = get_city_events_tool.invoke({"cities": SUPPORTED_CITIES})
    return {"city_events": city_events}
