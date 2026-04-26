from src.utils.logger import logger as log
from fastapi import APIRouter, Depends, status
from src.utils.general import http_error_response
from src.db.client import DB, get_db
from src.service.healthcheck import HealthCheckDataService
from src.models.error_response import HttpErrorResponse
from src.models.infra import ReadinessResponse
from typing import Annotated

router = APIRouter(
    tags=["infrastructure"],
)


def get_healthcheck_service(db: Annotated[DB, Depends(get_db)]) -> HealthCheckDataService:
    return HealthCheckDataService(db)


@router.get("/api/healthcheck", status_code=status.HTTP_200_OK)
async def liveness() -> str:
    return "OK"


@router.get(
    "/api/readiness",
    response_model=ReadinessResponse,
    status_code=status.HTTP_200_OK,
    responses={status.HTTP_500_INTERNAL_SERVER_ERROR: {"model": HttpErrorResponse}},
)
async def readiness(
    readiness_service: Annotated[HealthCheckDataService, Depends(get_healthcheck_service)],
) -> ReadinessResponse:
    log.info("Running readiness probe...")
    availability = readiness_service.availability()
    is_ready = all(value for value in availability.values())
    if not is_ready:
        raise http_error_response(
            error_message=f"Readiness probe checks failed. service:{availability.get('service')}",
            error_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
    return ReadinessResponse(serviceAvailable=availability.get("service", False))
