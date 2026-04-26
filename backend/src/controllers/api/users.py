from src.utils.logger import logger as log
from fastapi import APIRouter, Depends, status
from src.db.client import DB, get_db
from src.service.users import UserService
from typing import Annotated

router = APIRouter(
    tags=["users"],
)


def get_user_service(db: Annotated[DB, Depends(get_db)]) -> UserService:
    return UserService(db)


@router.get("/api/me", status_code=status.HTTP_200_OK)
async def get_current_user(user_service: Annotated[UserService, Depends(get_user_service)]) -> dict:
    log.info("Fetching current user...")
    exists = user_service.get_first_id()
    return {"connected": True, "hasProfiles": exists}
