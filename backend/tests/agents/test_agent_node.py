from langchain_core.messages import HumanMessage
from unittest.mock import MagicMock, patch

from src.agents.nodes.workers import planning_agent_node

# Light test to verify that the planning agent node correctly builds the GraphContext from the state and invokes the agent.


def test_planning_agent_node_builds_context_from_state():
    """GraphContext is constructed from the right state fields."""
    mock_chatbot = MagicMock()
    mock_chatbot.llm = MagicMock()
    mock_agent = MagicMock()
    mock_agent.invoke.return_value = {"messages": []}

    state = {
        "household_id": "hh-99",
        "user_id": "usr-42",
        "messages": [HumanMessage(content="What's the weather like?")],
        "chatbot": mock_chatbot,
        "system_prompt": "Custom prompt",
    }

    with patch("src.agents.nodes.workers.GraphContext") as MockCtx, patch(
        "src.agents.nodes.workers.create_agent", return_value=mock_agent
    ) as mock_build:

        mock_agent = MagicMock()
        mock_build.return_value = mock_agent
        runtime = MagicMock()

        planning_agent_node(state, runtime)

        MockCtx.assert_called_once_with(
            db_client=runtime.context.db_client,
            household_id="hh-99",
            user_id="usr-42",
        )
        mock_build.assert_called_once()
        mock_agent.invoke.assert_called_once()
