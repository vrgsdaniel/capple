from langgraph.graph import StateGraph, START, END
from src.agents.state import ChatState
from src.agents.nodes.context import battery_context_node, NODE_NAME as CONTEXT_NODE
from src.agents.nodes.chat import chat_node, system_prompt_node


SYSTEM_PROMPT_NODE = "system_prompt_node"
CHAT_NODE = "chat_node"


def build_graph():
    """Build the chat graph with nodes for context loading, prompt building, and LLM invocation."""
    graph = StateGraph(ChatState)

    # Add nodes in order
    graph.add_node(CONTEXT_NODE, battery_context_node)
    graph.add_node(SYSTEM_PROMPT_NODE, system_prompt_node)
    graph.add_node(CHAT_NODE, chat_node)

    # Build the flow: context -> prompt -> chat -> end
    graph.add_edge(START, CONTEXT_NODE)
    graph.add_edge(CONTEXT_NODE, SYSTEM_PROMPT_NODE)
    graph.add_edge(SYSTEM_PROMPT_NODE, CHAT_NODE)
    graph.add_edge(CHAT_NODE, END)

    return graph.compile()
