from langchain_core.messages import HumanMessage, AIMessage
from src.agents.llm.chatbot import Chatbot
from src.agents.state import ChatState
from src.db.db import DB


class ChatService:
    """Service for managing chat-related operations using LangGraph."""

    def __init__(self, user_id: str, household_id: str, db: DB, chatbot: Chatbot, graph):
        self.user_id = user_id
        self.household_id = household_id
        self.db = db
        self.chatbot = chatbot
        self.graph = graph

    def _build_initial_state(self, message: str, history: list[dict]) -> ChatState:
        """Build the initial state for the graph from message and history.

        Args:
            message: The user's latest message
            history: List of dicts with 'role' and 'content' keys

        Returns:
            ChatState with all required fields initialized
        """
        # Convert history to LangChain message objects
        lc_history = []
        for h in history:
            if h["role"] == "user":
                lc_history.append(HumanMessage(content=h["content"]))
            elif h["role"] == "assistant":
                lc_history.append(AIMessage(content=h["content"]))

        # Add the new user message
        messages = lc_history + [HumanMessage(content=message)]

        # Initialize state with all required fields
        state: ChatState = {
            "messages": messages,
            "household_id": str(self.household_id),
            "user_id": self.user_id,
            "battery_context": None,
            "chatbot": self.chatbot,
            "system_prompt": "",  # Will be set by system_prompt_node
        }

        return state

    def stream_response(self, message: str, history: list[dict]):
        """Stream chat responses as clean message content.

        Handles all graph execution details internally and yields only
        the AI response content string.

        Args:
            message: The user's message
            history: Conversation history as list of dicts with 'role' and 'content'

        Yields:
            str: Content chunks from the AI response
        """
        initial_state = self._build_initial_state(message, history)

        # Stream the graph execution and extract responses
        for output in self.graph.stream(initial_state):
            # output is a dict with node_name as key and node output as value
            for node_name, node_output in output.items():
                # Only yield content from the chat_node (final AI response)
                if node_name == "chat_node" and "messages" in node_output:
                    messages = node_output["messages"]
                    if messages:
                        response = messages[-1]
                        if hasattr(response, "content") and response.content:
                            yield response.content
