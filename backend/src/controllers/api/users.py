from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer


from src.auth.auth import Auth
from src.errors import NotFoundException
from src.utils.general import http_error_response
from src.utils.logger import logger as log
from fastapi import APIRouter, Depends, HTTPException, status
from src.db.db import DB, get_db
from src.models.household import CreateHouseholdRequest, JoinHouseholdRequest
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
    return {"id": user_id, "name": user["user_name"], "avatar_url": user["avatar_url"]}


@router.post("/api/households", status_code=status.HTTP_201_CREATED)
async def create_household(
    body: CreateHouseholdRequest,
    current_user: Annotated[Dict, Depends(get_current_user)],
    user_service: Annotated[UserService, Depends(get_user_service)],
) -> Dict:
    log.info("Creating household...")
    try:
        return user_service.create_household(current_user.id, body.name)
    except Exception:
        log.error("Failed to create household.")
        raise http_error_response(
            error_message="Failed to create household.",
            error_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@router.post("/api/households/join", status_code=status.HTTP_200_OK)
async def join_household(
    body: JoinHouseholdRequest,
    current_user: Annotated[Dict, Depends(get_current_user)],
    user_service: Annotated[UserService, Depends(get_user_service)],
) -> Dict:
    log.info("Joining household...")
    try:
        return user_service.join_household(current_user.id, body.invite_code)
    except NotFoundException:
        raise http_error_response(
            error_message="Invalid invite code.",
            error_code=status.HTTP_404_NOT_FOUND,
        )
    except Exception:
        log.error("Failed to join household.")
        raise http_error_response(
            error_message="Failed to join household.",
            error_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@router.get("/api/households/me", status_code=status.HTTP_200_OK)
async def get_my_household(
    current_user: Annotated[Dict, Depends(get_current_user)],
    user_service: Annotated[UserService, Depends(get_user_service)],
) -> Dict:
    log.info("Fetching household for current user...")
    household = user_service.get_user_household(current_user.id)
    if not household:
        raise http_error_response(
            error_message="No household found for this user.",
            error_code=status.HTTP_404_NOT_FOUND,
        )
    return household
