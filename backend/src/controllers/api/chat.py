from typing import Annotated, AsyncIterable
from fastapi import APIRouter, Depends, Request
from fastapi.sse import EventSourceResponse, ServerSentEvent

from src.controllers.api.users import get_current_user
from src.db.db import DB, get_db
from src.models.chat import ChatRequest
from src.service.chat import ChatService
from src.service.users import UserService
from src.agents.llm.chatbot import Chatbot, ChatbotFactory
from src.settings import get_llm_settings
from src.errors import NotFoundException
from src.utils.logger import logger as log

router = APIRouter(tags=["chat"])


def get_chatbot() -> Chatbot:
    """Provide the chatbot instance for the chat service."""
    return ChatbotFactory.create_chatbot(get_llm_settings().provider)


def get_chat_graph(request: Request):
    """Get compiled chat graph from FastAPI app state."""
    return request.app.state.chat_graph


def get_chat_service(
    current_user: Annotated[dict, Depends(get_current_user)],
    db: Annotated[DB, Depends(get_db)],
    chatbot: Annotated[Chatbot, Depends(get_chatbot)],
    graph=Depends(get_chat_graph),
) -> ChatService:
    """Create a ChatService with all dependencies injected.

    Retrieves the user's household and raises NotFoundException if user
    doesn't belong to a household.
    """
    user_id = str(current_user.id)
    user_service = UserService(db)
    household = user_service.get_user_household(user_id)

    if not household:
        raise NotFoundException("User must belong to a household to use chat")

    return ChatService(user_id, household["id"], db, chatbot, graph)


def convert_history_to_dict(history):
    """Convert message history to dict format expected by the service."""
    return [{"role": m.role, "content": m.content} for m in history]


@router.post("/api/chat", response_class=EventSourceResponse)
async def chat(
    body: ChatRequest,
    chat_service: Annotated[ChatService, Depends(get_chat_service)],
) -> AsyncIterable[ServerSentEvent]:
    """Stream chat responses using the LangGraph-powered chat service."""
    user_id = chat_service.user_id
    household_id = chat_service.household_id

    log.info(f"Starting chat for user {user_id} in household {household_id} with message: {body.message}")

    stream_iter = iter(chat_service.stream_response(body.message, convert_history_to_dict(body.history)))
    first_content = None

    yield ServerSentEvent(comment="stream of chat updates")

    # In response_class-based SSE handlers, setup executes during streaming.
    # Emit an error event instead of raising HTTPException to keep stream semantics.
    try:
        first_content = next(stream_iter)
    except StopIteration:
        first_content = None
    except NotFoundException as e:
        log.exception("Chat not found error")
        yield ServerSentEvent(data=f"Error: {str(e)}", event="error")
        return
    except Exception:
        log.exception("Chat stream setup error")
        yield ServerSentEvent(data="Something went wrong. Please try again.", event="error")
        return

    try:
        event_id = 1
        if first_content is not None:
            yield ServerSentEvent(data=first_content, event="message", id=str(event_id), retry=5000)
            event_id += 1

        # Stream response content from the chat service
        for content in stream_iter:
            yield ServerSentEvent(data=content, event="message", id=str(event_id), retry=5000)
            event_id += 1

        yield ServerSentEvent(data="[DONE]", event="done")
        log.info(f"Chat stream completed for user {user_id} in household {household_id}")
    except NotFoundException as e:
        log.exception("Chat not found error")
        yield ServerSentEvent(data=f"Error: {str(e)}", event="error")
    except Exception:
        log.exception("Chat stream error")
        yield ServerSentEvent(data="Something went wrong. Please try again.", event="error")
