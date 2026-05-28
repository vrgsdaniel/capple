from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from src.controllers.api.users import get_current_user
from src.db.db import DB, get_db
from src.errors import NotFoundException
from src.models.recipes import RecipeDetailsResponse, RecipeListItemResponse, RecipeListResponse
from src.service.recipes import RecipeService
from src.utils.general import http_error_response
from src.utils.logger import logger as log

router = APIRouter(tags=["recipes"])


def get_recipe_service(db: Annotated[DB, Depends(get_db)]) -> RecipeService:
    return RecipeService(db)


def _to_recipe_details_response(recipe: dict) -> RecipeDetailsResponse:
    return RecipeDetailsResponse(**recipe)


def _to_recipe_list_item_response(recipe: dict) -> RecipeListItemResponse:
    return RecipeListItemResponse(**recipe)


def _to_recipe_list_response(payload: dict) -> RecipeListResponse:
    return RecipeListResponse(
        items=[_to_recipe_list_item_response(item) for item in payload["items"]],
        total=payload["total"],
        page=payload["page"],
        limit=payload["limit"],
    )


@router.get("/api/recipes/{recipe_id}", status_code=status.HTTP_200_OK, response_model=RecipeDetailsResponse)
async def get_recipe_details(
    recipe_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
    recipe_service: Annotated[RecipeService, Depends(get_recipe_service)],
) -> RecipeDetailsResponse:
    log.info(f"Fetching recipe details for {recipe_id}")
    try:
        recipe_service.set_context({"user_id": current_user.id})
        recipe = recipe_service.get_recipe_details(recipe_id)
        response = _to_recipe_details_response(recipe)
        log.info(f"Successfully fetched recipe details for {recipe_id}")
        return response
    except NotFoundException as e:
        log.exception(f"Recipe not found: {recipe_id}")
        raise http_error_response(error_message=e.message, error_code=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        log.exception(f"Error fetching recipe details for {recipe_id}: {e}")
        raise http_error_response(
            error_message="Internal server error", error_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@router.get("/api/recipes", status_code=status.HTTP_200_OK, response_model=RecipeListResponse)
async def list_recipes(
    current_user: Annotated[dict, Depends(get_current_user)],
    recipe_service: Annotated[RecipeService, Depends(get_recipe_service)],
    search: Annotated[str | None, Query()] = None,
    recipe_type: Annotated[str | None, Query()] = None,
    labels: Annotated[list[str] | None, Query()] = None,
    ingredients: Annotated[list[str] | None, Query()] = None,
    sort_by: Annotated[str, Query()] = "cook_time_minutes",
    sort_order: Annotated[str, Query()] = "asc",
    page: Annotated[int, Query(ge=1)] = 1,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
) -> RecipeListResponse:
    log.info(f"Listing recipes with filters: search={search}, recipe_type={recipe_type}, page={page}")
    try:
        recipe_service.set_context({"user_id": current_user.id})
        result = recipe_service.list_recipes(
            search=search,
            recipe_type=recipe_type,
            labels=labels,
            ingredients=ingredients,
            sort_by=sort_by,
            sort_order=sort_order,
            page=page,
            limit=limit,
        )
        response = _to_recipe_list_response(result)
        log.info(f"Successfully listed recipes with filters: search={search}, recipe_type={recipe_type}, page={page}")
        return response
    except Exception as e:
        log.exception(f"Error listing recipes: {e}")
        raise http_error_response(
            error_message="Internal server error", error_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@router.post("/api/recipes/{recipe_id}/like", status_code=status.HTTP_200_OK, response_model=RecipeDetailsResponse)
async def toggle_recipe_like(
    recipe_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
    recipe_service: Annotated[RecipeService, Depends(get_recipe_service)],
) -> RecipeDetailsResponse:
    log.info(f"Toggling like for recipe {recipe_id} by user {current_user.id}")
    try:
        recipe_service.set_context({"user_id": current_user.id})
        recipe_service.toggle_recipe_like(recipe_id)
        recipe = recipe_service.get_recipe_details(recipe_id)
        response = _to_recipe_details_response(recipe)
        log.info(f"Successfully toggled like for recipe {recipe_id}")
        return response
    except NotFoundException as e:
        log.exception(f"Recipe not found: {recipe_id}")
        raise http_error_response(error_message=e.message, error_code=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        log.exception(f"Error toggling like for recipe {recipe_id}: {e}")
        raise http_error_response(
            error_message="Internal server error", error_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@router.post("/api/recipes/{recipe_id}/cooked", status_code=status.HTTP_200_OK, response_model=RecipeDetailsResponse)
async def toggle_recipe_cooked(
    recipe_id: str,
    current_user: Annotated[dict, Depends(get_current_user)],
    recipe_service: Annotated[RecipeService, Depends(get_recipe_service)],
) -> RecipeDetailsResponse:
    log.info(f"Toggling cooked for recipe {recipe_id} by user {current_user.id}")
    try:
        recipe_service.set_context({"user_id": current_user.id})
        recipe_service.toggle_recipe_cooked(recipe_id)
        recipe = recipe_service.get_recipe_details(recipe_id)
        response = _to_recipe_details_response(recipe)
        log.info(f"Successfully toggled cooked for recipe {recipe_id}")
        return response
    except NotFoundException as e:
        log.exception(f"Recipe not found: {recipe_id}")
        raise http_error_response(error_message=e.message, error_code=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        log.exception(f"Error toggling cooked for recipe {recipe_id}: {e}")
        raise http_error_response(
            error_message="Internal server error", error_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
