from typing import Annotated, Dict

from fastapi import APIRouter, Depends, status

from src.controllers.api.users import get_current_user
from src.db.db import DB, get_db
from src.errors import NotFoundException
from src.models.grocery_item import (
    AddFromRecipeRequest,
    AddGroceryItemRequest,
    GroceryItemResponse,
    GroceryListResponse,
    PatchGroceryItemRequest,
)
from src.service.grocery_service import GroceryService
from src.utils.general import http_error_response
from src.utils.logger import logger as log

router = APIRouter(tags=["groceries"])


def get_grocery_service(db: Annotated[DB, Depends(get_db)]) -> GroceryService:
    return GroceryService(db)


@router.get("/api/grocery-items", status_code=status.HTTP_200_OK)
async def list_grocery_items(
    current_user: Annotated[Dict, Depends(get_current_user)],
    service: Annotated[GroceryService, Depends(get_grocery_service)],
) -> GroceryListResponse:
    try:
        result = service.list_items(current_user.id)
        return GroceryListResponse(**result)
    except NotFoundException as e:
        raise http_error_response(error_message=e.message, error_code=status.HTTP_404_NOT_FOUND)


@router.post("/api/grocery-items", status_code=status.HTTP_201_CREATED)
async def add_grocery_item(
    body: AddGroceryItemRequest,
    current_user: Annotated[Dict, Depends(get_current_user)],
    service: Annotated[GroceryService, Depends(get_grocery_service)],
) -> GroceryItemResponse:
    try:
        return service.add_item(current_user.id, body.name, body.qty)
    except NotFoundException as e:
        raise http_error_response(error_message=e.message, error_code=status.HTTP_404_NOT_FOUND)


@router.post("/api/grocery-items/from-recipe", status_code=status.HTTP_201_CREATED)
async def add_from_recipe(
    body: AddFromRecipeRequest,
    current_user: Annotated[Dict, Depends(get_current_user)],
    service: Annotated[GroceryService, Depends(get_grocery_service)],
) -> list[GroceryItemResponse]:
    try:
        return service.add_from_recipe(current_user.id, body.recipe_id, body.ingredients)
    except NotFoundException as e:
        raise http_error_response(error_message=e.message, error_code=status.HTTP_404_NOT_FOUND)


@router.patch("/api/grocery-items/{item_id}", status_code=status.HTTP_200_OK)
async def patch_grocery_item(
    item_id: str,
    body: PatchGroceryItemRequest,
    current_user: Annotated[Dict, Depends(get_current_user)],
    service: Annotated[GroceryService, Depends(get_grocery_service)],
) -> GroceryItemResponse:
    log.info(f"Patching grocery item {item_id} (bought={body.bought})")
    try:
        if body.bought:
            return service.mark_bought(current_user.id, item_id)
        else:
            return service.restore_item(current_user.id, item_id)
    except NotFoundException as e:
        raise http_error_response(error_message=e.message, error_code=status.HTTP_404_NOT_FOUND)


@router.delete("/api/grocery-items/history", status_code=status.HTTP_204_NO_CONTENT)
async def clear_history(
    current_user: Annotated[Dict, Depends(get_current_user)],
    service: Annotated[GroceryService, Depends(get_grocery_service)],
) -> None:
    try:
        service.clear_history(current_user.id)
    except NotFoundException as e:
        raise http_error_response(error_message=e.message, error_code=status.HTTP_404_NOT_FOUND)


@router.delete("/api/grocery-items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_grocery_item(
    item_id: str,
    current_user: Annotated[Dict, Depends(get_current_user)],
    service: Annotated[GroceryService, Depends(get_grocery_service)],
) -> None:
    log.info(f"Deleting grocery item {item_id}")
    try:
        service.remove_item(current_user.id, item_id)
    except NotFoundException as e:
        raise http_error_response(error_message=e.message, error_code=status.HTTP_404_NOT_FOUND)
