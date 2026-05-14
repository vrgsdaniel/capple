import json
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import StreamingResponse

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


def _sse(data: str, event: str = "message") -> str:
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


def convert_history_to_dict(history):
    """Convert message history to dict format expected by the service."""
    return [{"role": m.role, "content": m.content} for m in history]


@router.post("/api/chat")
async def chat(
    body: ChatRequest,
    chat_service: Annotated[ChatService, Depends(get_chat_service)],
):
    """Stream chat responses using the LangGraph-powered chat service."""
    user_id = chat_service.user_id
    household_id = chat_service.household_id

    log.info(f"Starting chat for user {user_id} in household {household_id} with message: {body.message}")

    stream_iter = iter(chat_service.stream_response(body.message, convert_history_to_dict(body.history)))
    first_content = None

    # Prime the iterator so failures before the first token can be returned as HTTP 500.
    try:
        first_content = next(stream_iter)
    except StopIteration:
        first_content = None
    except NotFoundException as e:
        log.exception("Chat not found error")
        raise HTTPException(status_code=500, detail=str(e)) from e
    except Exception as e:
        log.exception("Chat stream setup error")
        raise HTTPException(status_code=500, detail="Something went wrong. Please try again.") from e

    async def event_stream():
        try:
            if first_content is not None:
                yield _sse(first_content)

            # Stream response content from the chat service
            for content in stream_iter:
                yield _sse(content)

            yield _sse("[DONE]", event="done")
            log.info(f"Chat stream completed for user {user_id} in household {household_id}")
        except NotFoundException as e:
            log.exception("Chat not found error")
            yield _sse(f"Error: {str(e)}", event="error")
        except Exception:
            log.exception("Chat stream error")
            yield _sse("Something went wrong. Please try again.", event="error")

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
