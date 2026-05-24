from json import JSONDecodeError
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.messages import SystemMessage
from src.agents.graph import GraphContext
from src.agents.llm.chatbot import Chatbot
from src.agents.state import ChatState, build_default_chat_state_model, ensure_chat_state
from src.db.db import DB
from src.utils.logger import logger as log


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

        # Initialize state with defaults, then override request-specific fields.
        base_state = build_default_chat_state_model()
        base_state.messages = messages
        base_state.household_id = str(self.household_id)
        base_state.user_id = self.user_id
        base_state.chatbot = self.chatbot
        state = base_state.model_dump()
        state["messages"] = messages
        state["chatbot"] = self.chatbot

        ensure_chat_state(state)
        return state

    def _prepare_state_with_graph(self, initial_state: ChatState) -> ChatState:
        """Run graph nodes that enrich state (context + system prompt)."""
        prepared_state = dict(initial_state)
        run_ctx = GraphContext(
            db_client=self.db,
            household_id=self.household_id,
            user_id=self.user_id,
        )

        if hasattr(self.graph, "stream"):
            stream_iter = self.graph.stream(prepared_state, context=run_ctx)
            for output in stream_iter:
                for _, node_output in output.items():
                    if isinstance(node_output, dict):
                        prepared_state.update(node_output)
            ensure_chat_state(prepared_state)
            return prepared_state

        if hasattr(self.graph, "invoke"):
            invoked = self.graph.invoke(prepared_state, context=run_ctx)
            if not invoked:
                return initial_state
            ensure_chat_state(invoked)
            return invoked

        raise RuntimeError("Chat graph must expose stream() or invoke()")

    @staticmethod
    def _extract_chunk_text(chunk) -> str:
        """Extract text from LangChain chunk/message shapes."""
        if chunk is None:
            return ""

        content = getattr(chunk, "content", chunk)
        if isinstance(content, str):
            return content

        if isinstance(content, list):
            parts: list[str] = []
            for item in content:
                if isinstance(item, str):
                    parts.append(item)
                elif isinstance(item, dict):
                    text = item.get("text")
                    if isinstance(text, str):
                        parts.append(text)
            return "".join(parts)

        return ""

    def stream_response(self, message: str, history: list[dict]):
        """Stream chat responses as clean message content.

        Runs the graph to enrich state with context and system prompt, then
        streams model chunks directly from the configured chatbot.

        Args:
            message: The user's message
            history: Conversation history as list of dicts with 'role' and 'content'

        Yields:
            str: Content chunks from the AI response
        """
        initial_state = self._build_initial_state(message, history)
        prepared_state = self._prepare_state_with_graph(initial_state)

        system_prompt = prepared_state.get("system_prompt") or "You are a helpful assistant."
        messages = [SystemMessage(content=system_prompt)] + initial_state["messages"]

        emitted_any_chunk = False
        try:
            for chunk in self.chatbot.stream(messages):
                chunk_text = self._extract_chunk_text(chunk)
                if chunk_text:
                    emitted_any_chunk = True
                    yield chunk_text
        except JSONDecodeError:
            if emitted_any_chunk:
                # Some providers can emit a terminal malformed frame after valid chunks.
                # Treat it as end-of-stream so clients still receive a clean done event.
                log.warning("Ignoring terminal JSON decode error after streaming response chunks")
                return
            raise
