from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from src.auth.auth import Auth
from src.errors import NotFoundException
from src.utils.general import http_error_response
from src.utils.logger import logger as log
from fastapi import APIRouter, Depends, HTTPException, status
from src.db.db import DB, get_db
from src.service.users import UserService
from typing import Annotated, Dict

router = APIRouter(
    tags=["users"],
)

security = HTTPBearer()


def get_user_service(db: Annotated[DB, Depends(get_db)]) -> UserService:
    return UserService(db)


def get_auth_service(credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)]) -> Auth:
    return Auth(credentials.credentials)


async def get_current_user(
    auth_service: Annotated[Auth, Depends(get_auth_service)],
):
    try:
        user = await auth_service.get_current_user()
        if not user:
            log.error("No user found for the provided token.")
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
        return user
    except NotFoundException:
        raise http_error_response(
            error_message="No user found for the provided token.",
            error_code=status.HTTP_401_UNAUTHORIZED,
        )
    except Exception:
        log.error("Failed to fetch user information.")
        raise http_error_response(
            error_message="Failed to fetch user information.",
            error_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@router.get("/api/me", status_code=status.HTTP_200_OK)
async def get_current_user_name(
    current_user: Annotated[Dict, Depends(get_current_user)],
    user_service: Annotated[UserService, Depends(get_user_service)],
) -> Dict:
    log.info("Fetching current user...")
    user_id = current_user.id
    user = user_service.get_user_name_by_id(user_id)
    if not user:
        raise http_error_response(
            error_message="User profile not found.",
            error_code=status.HTTP_404_NOT_FOUND,
        )
    return {"id": user_id, "name": user["user_name"]}
