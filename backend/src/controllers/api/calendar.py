from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from src.controllers.api.users import get_current_user
from src.errors import NotFoundException, ValidationException
from src.models.calendar import (
    BirthdayResponse,
    CalendarFeedQuery,
    CalendarFeedResponse,
    CreateBirthdayRequest,
    CreateEventRequest,
    EventResponse,
    UpdateBirthdayRequest,
    UpdateEventRequest,
)
from src.models.user import CurrentUser
from src.repository.repository import Repository, get_repository
from src.service.calendar_service import CalendarService
from src.utils.general import http_error_response
from src.utils.logger import logger as log

router = APIRouter(tags=["calendar"])


def get_calendar_service(repo: Annotated[Repository, Depends(get_repository)]) -> CalendarService:
    return CalendarService(repo)


# --- feed ---


@router.get("/api/calendar/events", status_code=status.HTTP_200_OK)
async def get_calendar_feed(
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    service: Annotated[CalendarService, Depends(get_calendar_service)],
    query: Annotated[CalendarFeedQuery, Query()],
) -> CalendarFeedResponse:
    try:
        result = await service.get_feed(current_user.id, query.range_from, query.range_to)
        return CalendarFeedResponse(**result)
    except NotFoundException as e:
        log.warning(f"get_calendar_feed failed for user {current_user.id}: {e.message}")
        raise http_error_response(error_message=e.message, error_code=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        log.error(f"Unexpected error in get_calendar_feed for user {current_user.id}: {e}")
        raise http_error_response(
            error_message="An unexpected error occurred while loading the calendar.",
            error_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


# --- events ---


@router.post("/api/calendar/events", status_code=status.HTTP_201_CREATED)
async def create_event(
    body: CreateEventRequest,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    service: Annotated[CalendarService, Depends(get_calendar_service)],
) -> EventResponse:
    try:
        return await service.create_event(
            current_user.id,
            title=body.title,
            event_date=str(body.event_date),
            start_time=str(body.start_time) if body.start_time else None,
            end_time=str(body.end_time) if body.end_time else None,
            location=body.location,
            description=body.description,
        )
    except NotFoundException as e:
        log.warning(f"create_event failed for user {current_user.id}: {e.message}")
        raise http_error_response(error_message=e.message, error_code=status.HTTP_404_NOT_FOUND)
    except ValidationException as e:
        log.warning(f"create_event invalid data for user {current_user.id}: {e.message}")
        raise http_error_response(error_message=e.message, error_code=status.HTTP_422_UNPROCESSABLE_ENTITY)
    except Exception as e:
        log.error(f"Unexpected error in create_event for user {current_user.id}: {e}")
        raise http_error_response(
            error_message="An unexpected error occurred while creating the event.",
            error_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@router.patch("/api/calendar/events/{event_id}", status_code=status.HTTP_200_OK)
async def update_event(
    event_id: str,
    body: UpdateEventRequest,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    service: Annotated[CalendarService, Depends(get_calendar_service)],
) -> EventResponse:
    try:
        updates = body.model_dump(exclude_unset=True)
        for key in ("event_date", "start_time", "end_time"):
            if key in updates and updates[key] is not None:
                updates[key] = str(updates[key])
        return await service.update_event(current_user.id, event_id, updates)
    except NotFoundException as e:
        log.warning(f"update_event {event_id} failed for user {current_user.id}: {e.message}")
        raise http_error_response(error_message=e.message, error_code=status.HTTP_404_NOT_FOUND)
    except ValidationException as e:
        log.warning(f"update_event {event_id} invalid data for user {current_user.id}: {e.message}")
        raise http_error_response(error_message=e.message, error_code=status.HTTP_422_UNPROCESSABLE_ENTITY)
    except Exception as e:
        log.error(f"Unexpected error in update_event {event_id} for user {current_user.id}: {e}")
        raise http_error_response(
            error_message="An unexpected error occurred while updating the event.",
            error_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@router.delete("/api/calendar/events/{event_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_event(
    event_id: str,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    service: Annotated[CalendarService, Depends(get_calendar_service)],
) -> None:
    log.info(f"Deleting event {event_id} requested by user {current_user.id}")
    try:
        await service.delete_event(current_user.id, event_id)
    except NotFoundException as e:
        log.warning(f"delete_event {event_id} failed for user {current_user.id}: {e.message}")
        raise http_error_response(error_message=e.message, error_code=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        log.error(f"Unexpected error in delete_event {event_id} for user {current_user.id}: {e}")
        raise http_error_response(
            error_message="An unexpected error occurred while deleting the event.",
            error_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


# --- birthdays ---


@router.post("/api/calendar/birthdays", status_code=status.HTTP_201_CREATED)
async def create_birthday(
    body: CreateBirthdayRequest,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    service: Annotated[CalendarService, Depends(get_calendar_service)],
) -> BirthdayResponse:
    try:
        return await service.create_birthday(
            current_user.id,
            person_name=body.person_name,
            birth_month=body.birth_month,
            birth_day=body.birth_day,
            birth_year=body.birth_year,
            # Always a concrete bool by this point — CreateBirthdayRequest's validator infers it
            # from birth_year when the caller doesn't set it explicitly.
            show_year=bool(body.show_year),
        )
    except NotFoundException as e:
        log.warning(f"create_birthday failed for user {current_user.id}: {e.message}")
        raise http_error_response(error_message=e.message, error_code=status.HTTP_404_NOT_FOUND)
    except ValidationException as e:
        log.warning(f"create_birthday invalid data for user {current_user.id}: {e.message}")
        raise http_error_response(error_message=e.message, error_code=status.HTTP_422_UNPROCESSABLE_ENTITY)
    except Exception as e:
        log.error(f"Unexpected error in create_birthday for user {current_user.id}: {e}")
        raise http_error_response(
            error_message="An unexpected error occurred while creating the birthday.",
            error_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@router.patch("/api/calendar/birthdays/{birthday_id}", status_code=status.HTTP_200_OK)
async def update_birthday(
    birthday_id: str,
    body: UpdateBirthdayRequest,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    service: Annotated[CalendarService, Depends(get_calendar_service)],
) -> BirthdayResponse:
    try:
        updates = body.model_dump(exclude_unset=True)
        return await service.update_birthday(current_user.id, birthday_id, updates)
    except NotFoundException as e:
        log.warning(f"update_birthday {birthday_id} failed for user {current_user.id}: {e.message}")
        raise http_error_response(error_message=e.message, error_code=status.HTTP_404_NOT_FOUND)
    except ValidationException as e:
        log.warning(f"update_birthday {birthday_id} invalid data for user {current_user.id}: {e.message}")
        raise http_error_response(error_message=e.message, error_code=status.HTTP_422_UNPROCESSABLE_ENTITY)
    except Exception as e:
        log.error(f"Unexpected error in update_birthday {birthday_id} for user {current_user.id}: {e}")
        raise http_error_response(
            error_message="An unexpected error occurred while updating the birthday.",
            error_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@router.delete("/api/calendar/birthdays/{birthday_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_birthday(
    birthday_id: str,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    service: Annotated[CalendarService, Depends(get_calendar_service)],
) -> None:
    log.info(f"Deleting birthday {birthday_id} requested by user {current_user.id}")
    try:
        await service.delete_birthday(current_user.id, birthday_id)
    except NotFoundException as e:
        log.warning(f"delete_birthday {birthday_id} failed for user {current_user.id}: {e.message}")
        raise http_error_response(error_message=e.message, error_code=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        log.error(f"Unexpected error in delete_birthday {birthday_id} for user {current_user.id}: {e}")
        raise http_error_response(
            error_message="An unexpected error occurred while deleting the birthday.",
            error_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
