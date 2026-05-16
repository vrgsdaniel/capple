from langgraph.graph import StateGraph, START, END
from src.agents.state import ChatState, ensure_chat_state
from src.agents.nodes.chat import system_prompt_node
from src.agents.nodes.router import router_node, NODE_NAME as ROUTER_NODE
from src.agents.nodes.workers import (
    context_worker_node,
    planner_worker_node,
    CONTEXT_WORKER_NODE,
    PLANNER_WORKER_NODE,
)

SYSTEM_PROMPT_NODE = "system_prompt_node"


def _route_after_router(state: ChatState) -> str:
    state_obj = ensure_chat_state(state)
    plan = state_obj.workflow_plan
    if CONTEXT_WORKER_NODE in plan:
        return CONTEXT_WORKER_NODE
    if PLANNER_WORKER_NODE in plan:
        return PLANNER_WORKER_NODE
    return SYSTEM_PROMPT_NODE


def _route_after_context_worker(state: ChatState) -> str:
    state_obj = ensure_chat_state(state)
    if PLANNER_WORKER_NODE in state_obj.workflow_plan:
        return PLANNER_WORKER_NODE
    return SYSTEM_PROMPT_NODE


def build_graph():
    """Build dynamic workflow graph with hybrid router and ReAct workers."""
    graph = StateGraph(ChatState)

    # Core nodes
    graph.add_node(ROUTER_NODE, router_node)
    graph.add_node(CONTEXT_WORKER_NODE, context_worker_node)
    graph.add_node(PLANNER_WORKER_NODE, planner_worker_node)
    graph.add_node(SYSTEM_PROMPT_NODE, system_prompt_node)

    # Dynamic workflow edges
    graph.add_edge(START, ROUTER_NODE)
    graph.add_conditional_edges(
        ROUTER_NODE,
        _route_after_router,
        {
            CONTEXT_WORKER_NODE: CONTEXT_WORKER_NODE,
            PLANNER_WORKER_NODE: PLANNER_WORKER_NODE,
            SYSTEM_PROMPT_NODE: SYSTEM_PROMPT_NODE,
        },
    )

    graph.add_conditional_edges(
        CONTEXT_WORKER_NODE,
        _route_after_context_worker,
        {
            PLANNER_WORKER_NODE: PLANNER_WORKER_NODE,
            SYSTEM_PROMPT_NODE: SYSTEM_PROMPT_NODE,
        },
    )

    graph.add_edge(PLANNER_WORKER_NODE, SYSTEM_PROMPT_NODE)
    graph.add_edge(SYSTEM_PROMPT_NODE, END)

    return graph.compile()
