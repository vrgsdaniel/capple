from typing import Annotated, Dict

from fastapi import APIRouter, Depends, Query, status

from src.controllers.api.users import get_current_user
from src.repository.repository import Repository, get_repository
from src.errors import NotFoundException
from src.models.task import CreateTaskRequest, TaskListResponse, TaskResponse, UpdateTaskRequest
from src.service.task_service import TaskService
from src.utils.general import http_error_response
from src.utils.logger import logger as log

router = APIRouter(tags=["tasks"])


def get_task_service(repo: Annotated[Repository, Depends(get_repository)]) -> TaskService:
    return TaskService(repo)


@router.get("/api/tasks", status_code=status.HTTP_200_OK)
async def list_tasks(
    current_user: Annotated[Dict, Depends(get_current_user)],
    service: Annotated[TaskService, Depends(get_task_service)],
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    include_history: bool = Query(True),
) -> TaskListResponse:
    try:
        result = await service.list_tasks(current_user.id, page=page, page_size=page_size, include_history=include_history)
        return TaskListResponse(**result)
    except NotFoundException as e:
        log.warning(f"list_tasks failed for user {current_user.id}: {e.message}")
        raise http_error_response(error_message=e.message, error_code=status.HTTP_404_NOT_FOUND)


@router.post("/api/tasks", status_code=status.HTTP_201_CREATED)
async def create_task(
    body: CreateTaskRequest,
    current_user: Annotated[Dict, Depends(get_current_user)],
    service: Annotated[TaskService, Depends(get_task_service)],
) -> TaskResponse:
    try:
        return await service.create_task(
            current_user.id,
            name=body.name,
            assignee_type=body.assignee_type,
            assignee_id=str(body.assignee_id) if body.assignee_id else None,
            due_date=str(body.due_date) if body.due_date else None,
            frequency=body.frequency,
        )
    except NotFoundException as e:
        log.warning(f"create_task failed for user {current_user.id}: {e.message}")
        raise http_error_response(error_message=e.message, error_code=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        log.error(f"Unexpected error in create_task for user {current_user.id}: {e}")
        raise http_error_response(
            error_message="An unexpected error occurred while creating the task.",
            error_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@router.patch("/api/tasks/{task_id}", status_code=status.HTTP_200_OK)
async def update_task(
    task_id: str,
    body: UpdateTaskRequest,
    current_user: Annotated[Dict, Depends(get_current_user)],
    service: Annotated[TaskService, Depends(get_task_service)],
) -> TaskResponse:
    try:
        updates = body.model_dump(exclude_unset=True)
        if "assignee_id" in updates and updates["assignee_id"] is not None:
            updates["assignee_id"] = str(updates["assignee_id"])
        if "due_date" in updates and updates["due_date"] is not None:
            updates["due_date"] = str(updates["due_date"])
        return await service.update_task(current_user.id, task_id, updates)
    except NotFoundException as e:
        log.warning(f"update_task {task_id} failed for user {current_user.id}: {e.message}")
        raise http_error_response(error_message=e.message, error_code=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        log.error(f"Unexpected error in update_task {task_id} for user {current_user.id}: {e}")
        raise http_error_response(
            error_message="An unexpected error occurred while updating the task.",
            error_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@router.post("/api/tasks/{task_id}/complete", status_code=status.HTTP_200_OK)
async def complete_task(
    task_id: str,
    current_user: Annotated[Dict, Depends(get_current_user)],
    service: Annotated[TaskService, Depends(get_task_service)],
) -> TaskResponse:
    try:
        return await service.complete_task(current_user.id, task_id)
    except NotFoundException as e:
        log.warning(f"complete_task {task_id} failed for user {current_user.id}: {e.message}")
        raise http_error_response(error_message=e.message, error_code=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        log.error(f"Unexpected error in complete_task {task_id} for user {current_user.id}: {e}")
        raise http_error_response(
            error_message="An unexpected error occurred while completing the task.",
            error_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@router.delete("/api/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id: str,
    current_user: Annotated[Dict, Depends(get_current_user)],
    service: Annotated[TaskService, Depends(get_task_service)],
) -> None:
    log.info(f"Deleting task {task_id} requested by user {current_user.id}")
    try:
        await service.delete_task(current_user.id, task_id)
    except NotFoundException as e:
        log.warning(f"delete_task {task_id} failed for user {current_user.id}: {e.message}")
        raise http_error_response(error_message=e.message, error_code=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        log.error(f"Unexpected error in delete_task {task_id} for user {current_user.id}: {e}")
        raise http_error_response(
            error_message="An unexpected error occurred while deleting the task.",
            error_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
