from json import JSONDecodeError
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.messages import SystemMessage
from src.agents.graph import GraphContext
from src.agents.llm.chatbot import Chatbot
from src.agents.state import ChatState, build_default_chat_state_model, ensure_chat_state
from src.repository.repository import Repository
from src.utils.logger import logger as log


class ChatService:
    """Service for managing chat-related operations using LangGraph."""

    def __init__(self, user_id: str, household_id: str, db: Repository, chatbot: Chatbot, graph):
        self.user_id = user_id
        self.household_id = household_id
        self.db = db
        self.chatbot = chatbot
        self.graph = graph

    def _build_initial_state(self, message: str, history: list[dict]) -> ChatState:
        """Build the initial state for the graph from message and history."""
        lc_history = []
        for h in history:
            if h["role"] == "user":
                lc_history.append(HumanMessage(content=h["content"]))
            elif h["role"] == "assistant":
                lc_history.append(AIMessage(content=h["content"]))

        messages = lc_history + [HumanMessage(content=message)]

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

    async def _prepare_state_with_graph(self, initial_state: ChatState) -> ChatState:
        """Run graph nodes that enrich state (context + system prompt)."""
        prepared_state = dict(initial_state)
        run_ctx = GraphContext(
            db_client=self.db,
            household_id=self.household_id,
            user_id=self.user_id,
        )

        if hasattr(self.graph, "astream"):
            async for output in self.graph.astream(prepared_state, context=run_ctx):
                for _, node_output in output.items():
                    if isinstance(node_output, dict):
                        prepared_state.update(node_output)
            ensure_chat_state(prepared_state)
            return prepared_state

        if hasattr(self.graph, "ainvoke"):
            invoked = await self.graph.ainvoke(prepared_state, context=run_ctx)
            if not invoked:
                return initial_state
            ensure_chat_state(invoked)
            return invoked

        # Sync fallback for graphs that don't support async
        if hasattr(self.graph, "stream"):
            for output in self.graph.stream(prepared_state, context=run_ctx):
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

    @staticmethod
    def _graph_assistant_text(messages: list) -> str:
        """Return assistant text generated after the latest user message, if present."""
        if not isinstance(messages, list) or not messages:
            return ""

        def is_human(msg) -> bool:
            return getattr(msg, "type", "") == "human" or getattr(msg, "role", "") == "user"

        def is_assistant(msg) -> bool:
            return getattr(msg, "type", "") == "ai" or getattr(msg, "role", "") == "assistant"

        latest_user = next((msg for msg in reversed(messages) if is_human(msg)), None)
        if latest_user is None:
            return ""

        after_user = messages[messages.index(latest_user) + 1 :]
        assistant_msg = next((msg for msg in reversed(after_user) if is_assistant(msg)), None)

        return ChatService._extract_chunk_text(assistant_msg) if assistant_msg else ""

    async def stream_response(self, message: str, history: list[dict]):
        """Stream chat responses as an async generator of content chunks."""
        initial_state = self._build_initial_state(message, history)
        prepared_state = await self._prepare_state_with_graph(initial_state)

        graph_text = self._graph_assistant_text(prepared_state.get("messages", []))
        if graph_text:
            yield graph_text
            return

        system_prompt = prepared_state.get("system_prompt") or "You are a helpful assistant."
        messages = [SystemMessage(content=system_prompt)] + prepared_state.get("messages", initial_state["messages"])

        emitted_any_chunk = False
        try:
            if hasattr(self.chatbot, "astream"):
                async for chunk in self.chatbot.astream(messages):
                    chunk_text = self._extract_chunk_text(chunk)
                    if chunk_text:
                        emitted_any_chunk = True
                        yield chunk_text
            else:
                for chunk in self.chatbot.stream(messages):
                    chunk_text = self._extract_chunk_text(chunk)
                    if chunk_text:
                        emitted_any_chunk = True
                        yield chunk_text
        except JSONDecodeError:
            if emitted_any_chunk:
                log.warning("Ignoring terminal JSON decode error after streaming response chunks")
                return
            raise
