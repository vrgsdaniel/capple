from typing import Annotated, Dict

from fastapi import APIRouter, Depends, status

from src.controllers.api.users import get_current_user
from src.repository.repository import Repository, get_repository
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


def get_grocery_service(repo: Annotated[Repository, Depends(get_repository)]) -> GroceryService:
    return GroceryService(repo)


@router.get("/api/grocery-items", status_code=status.HTTP_200_OK)
async def list_grocery_items(
    current_user: Annotated[Dict, Depends(get_current_user)],
    service: Annotated[GroceryService, Depends(get_grocery_service)],
) -> GroceryListResponse:
    try:
        result = await service.list_items(current_user.id)
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
        return await service.add_item(current_user.id, body.name, body.qty)
    except NotFoundException as e:
        raise http_error_response(error_message=e.message, error_code=status.HTTP_404_NOT_FOUND)


@router.post("/api/grocery-items/from-recipe", status_code=status.HTTP_201_CREATED)
async def add_from_recipe(
    body: AddFromRecipeRequest,
    current_user: Annotated[Dict, Depends(get_current_user)],
    service: Annotated[GroceryService, Depends(get_grocery_service)],
) -> list[GroceryItemResponse]:
    try:
        ingredients = [{"name": ingredient.name, "qty": ingredient.qty} for ingredient in body.ingredients]
        return await service.add_from_recipe(current_user.id, body.recipe_id, ingredients)
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
            return await service.mark_bought(current_user.id, item_id)
        else:
            return await service.restore_item(current_user.id, item_id)
    except NotFoundException as e:
        raise http_error_response(error_message=e.message, error_code=status.HTTP_404_NOT_FOUND)


@router.delete("/api/grocery-items/history", status_code=status.HTTP_204_NO_CONTENT)
async def clear_history(
    current_user: Annotated[Dict, Depends(get_current_user)],
    service: Annotated[GroceryService, Depends(get_grocery_service)],
) -> None:
    try:
        await service.clear_history(current_user.id)
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
        await service.remove_item(current_user.id, item_id)
    except NotFoundException as e:
        raise http_error_response(error_message=e.message, error_code=status.HTTP_404_NOT_FOUND)
