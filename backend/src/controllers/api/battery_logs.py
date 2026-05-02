from datetime import datetime
from typing import Annotated, Dict

from fastapi import APIRouter, Depends, Query, status

from src.controllers.api.users import get_current_user
from src.db.db import DB, get_db
from src.errors import NotFoundException
from src.models.battery_log import BatteryLogResponse, CreateBatteryLogRequest, UpdateBatteryLogRequest
from src.service.battery_logs import BatteryLogService
from src.utils.general import http_error_response
from src.utils.logger import logger as log

router = APIRouter(tags=["battery-logs"])


def get_battery_log_service(db: Annotated[DB, Depends(get_db)]) -> BatteryLogService:
    return BatteryLogService(db)


@router.post("/api/battery-logs", status_code=status.HTTP_201_CREATED)
async def create_battery_log(
    body: CreateBatteryLogRequest,
    current_user: Annotated[Dict, Depends(get_current_user)],
    service: Annotated[BatteryLogService, Depends(get_battery_log_service)],
) -> BatteryLogResponse:
    log.info(f"Creating battery log for user {current_user.id}")
    try:
        return service.create_battery_log(
            user_id=current_user.id,
            level=body.level,
            note=body.note,
            effective_at=body.effective_at.isoformat(),
        )
    except NotFoundException as e:
        raise http_error_response(error_message=e.message, error_code=status.HTTP_404_NOT_FOUND)


@router.get("/api/battery-logs", status_code=status.HTTP_200_OK)
async def get_battery_logs(
    start: Annotated[datetime, Query()],
    end: Annotated[datetime, Query()],
    current_user: Annotated[Dict, Depends(get_current_user)],
    service: Annotated[BatteryLogService, Depends(get_battery_log_service)],
) -> list[BatteryLogResponse]:
    log.info(f"Fetching battery logs for user {current_user.id} from {start} to {end}")
    try:
        return service.get_household_battery_logs(current_user.id, start.isoformat(), end.isoformat())
    except NotFoundException as e:
        raise http_error_response(error_message=e.message, error_code=status.HTTP_404_NOT_FOUND)


@router.put("/api/battery-logs/{log_id}", status_code=status.HTTP_200_OK)
async def update_battery_log(
    log_id: str,
    body: UpdateBatteryLogRequest,
    current_user: Annotated[Dict, Depends(get_current_user)],
    service: Annotated[BatteryLogService, Depends(get_battery_log_service)],
) -> BatteryLogResponse:
    log.info(f"Updating battery log {log_id} for user {current_user.id}")
    try:
        updates = body.model_dump(exclude_unset=True)
        if "effective_at" in updates and updates["effective_at"] is not None:
            updates["effective_at"] = updates["effective_at"].isoformat()
        return service.update_battery_log(current_user.id, log_id, updates)
    except NotFoundException as e:
        raise http_error_response(error_message=e.message, error_code=status.HTTP_404_NOT_FOUND)


@router.delete("/api/battery-logs/{log_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_battery_log(
    log_id: str,
    current_user: Annotated[Dict, Depends(get_current_user)],
    service: Annotated[BatteryLogService, Depends(get_battery_log_service)],
) -> None:
    log.info(f"Deleting battery log {log_id} for user {current_user.id}")
    try:
        service.delete_battery_log(current_user.id, log_id)
    except NotFoundException as e:
        raise http_error_response(error_message=e.message, error_code=status.HTTP_404_NOT_FOUND)
