from langgraph.graph import StateGraph, START, END
from src.agents.state import ChatState
from src.agents.nodes.chat import system_prompt_node
from src.agents.nodes.workers import (
    planning_agent_node,
    PLANNING_AGENT_NODE,
)

SYSTEM_PROMPT_NODE = "system_prompt_node"


def build_graph():
    """Build a minimal graph: system prompt, then planning agent, then end."""
    graph = StateGraph(ChatState)

    # Core nodes
    graph.add_node(SYSTEM_PROMPT_NODE, system_prompt_node)
    graph.add_node(PLANNING_AGENT_NODE, planning_agent_node)

    # Static workflow edges
    graph.add_edge(START, SYSTEM_PROMPT_NODE)
    graph.add_edge(SYSTEM_PROMPT_NODE, PLANNING_AGENT_NODE)
    graph.add_edge(PLANNING_AGENT_NODE, END)

    return graph.compile()
