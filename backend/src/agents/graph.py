from langgraph.graph import StateGraph, START, END
from src.agents.state import ChatState
from src.agents.nodes.context import battery_context_node, NODE_NAME as CONTEXT_NODE
from src.agents.nodes.chat import system_prompt_node

SYSTEM_PROMPT_NODE = "system_prompt_node"


def build_graph():
    """Build the chat graph for context loading and prompt building."""
    graph = StateGraph(ChatState)

    # Add nodes in order.
    graph.add_node(CONTEXT_NODE, battery_context_node)
    graph.add_node(SYSTEM_PROMPT_NODE, system_prompt_node)

    # Build the flow: context -> prompt -> end.
    graph.add_edge(START, CONTEXT_NODE)
    graph.add_edge(CONTEXT_NODE, SYSTEM_PROMPT_NODE)
    graph.add_edge(SYSTEM_PROMPT_NODE, END)

    return graph.compile()
