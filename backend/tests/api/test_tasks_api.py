from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.controllers.api.tasks import get_task_service, router
from src.controllers.api.users import get_current_user
from src.errors import NotFoundException
from src.service.task_service import TaskService

FAKE_USER_ID = "00000000-0000-0000-0000-000000000001"
FAKE_USER = SimpleNamespace(id=FAKE_USER_ID)
FAKE_HOUSEHOLD_ID = "00000000-0000-0000-0000-000000000002"
FAKE_TASK_ID = "00000000-0000-0000-0000-000000000003"
FAKE_ASSIGNEE_ID = "00000000-0000-0000-0000-000000000004"

FAKE_TASK = {
    "id": FAKE_TASK_ID,
    "household_id": FAKE_HOUSEHOLD_ID,
    "name": "Vacuum living room",
    "assignee_type": "none",
    "assignee_id": None,
    "due_date": None,
    "frequency": None,
    "created_by": FAKE_USER_ID,
    "created_at": "2026-06-18T10:00:00+00:00",
    "updated_at": "2026-06-18T10:00:00+00:00",
    "completed_at": None,
}

FAKE_COMPLETED_TASK = {
    **FAKE_TASK,
    "id": "00000000-0000-0000-0000-000000000005",
    "name": "Take out trash",
    "completed_at": "2026-06-17T08:00:00+00:00",
}

FAKE_LIST = {
    "active": [FAKE_TASK],
    "history": [FAKE_COMPLETED_TASK],
    "active_total": 1,
    "history_total": 1,
    "page": 1,
    "page_size": 20,
}


@pytest.fixture
def mock_service():
    return MagicMock(spec=TaskService)


@pytest.fixture
def client(mock_service):
    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_task_service] = lambda: mock_service
    app.dependency_overrides[get_current_user] = lambda: FAKE_USER
    return TestClient(app)


class TestListTasks:
    def test_returns_200_with_active_and_history(self, client, mock_service):
        mock_service.list_tasks.return_value = FAKE_LIST

        resp = client.get("/api/tasks")

        assert resp.status_code == 200
        body = resp.json()
        assert len(body["active"]) == 1
        assert len(body["history"]) == 1
        assert body["active_total"] == 1

    def test_passes_pagination_params(self, client, mock_service):
        mock_service.list_tasks.return_value = {**FAKE_LIST, "page": 2, "page_size": 10}

        client.get("/api/tasks?page=2&page_size=10")

        mock_service.list_tasks.assert_called_once_with(FAKE_USER_ID, page=2, page_size=10, include_history=True)

    def test_returns_404_when_no_household(self, client, mock_service):
        mock_service.list_tasks.side_effect = NotFoundException("No household.")

        resp = client.get("/api/tasks")

        assert resp.status_code == 404


class TestCreateTask:
    def test_returns_201_with_minimal_task(self, client, mock_service):
        mock_service.create_task.return_value = FAKE_TASK

        resp = client.post("/api/tasks", json={"name": "Vacuum living room"})

        assert resp.status_code == 201
        assert resp.json()["name"] == "Vacuum living room"

    def test_returns_201_with_all_fields(self, client, mock_service):
        task = {**FAKE_TASK, "assignee_type": "specific", "assignee_id": FAKE_ASSIGNEE_ID, "due_date": "2026-06-30", "frequency": "weekly"}
        mock_service.create_task.return_value = task

        resp = client.post("/api/tasks", json={
            "name": "Vacuum",
            "assignee_type": "specific",
            "assignee_id": FAKE_ASSIGNEE_ID,
            "due_date": "2026-06-30",
            "frequency": "weekly",
        })

        assert resp.status_code == 201

    def test_returns_422_when_name_missing(self, client, mock_service):
        resp = client.post("/api/tasks", json={"assignee_type": "none"})

        assert resp.status_code == 422
        mock_service.create_task.assert_not_called()

    def test_returns_422_when_name_empty(self, client, mock_service):
        resp = client.post("/api/tasks", json={"name": ""})

        assert resp.status_code == 422
        mock_service.create_task.assert_not_called()

    def test_returns_422_when_specific_without_assignee_id(self, client, mock_service):
        resp = client.post("/api/tasks", json={"name": "Task", "assignee_type": "specific"})

        assert resp.status_code == 422
        mock_service.create_task.assert_not_called()

    def test_returns_404_when_no_household(self, client, mock_service):
        mock_service.create_task.side_effect = NotFoundException("No household.")

        resp = client.post("/api/tasks", json={"name": "Task"})

        assert resp.status_code == 404


class TestUpdateTask:
    def test_returns_200_with_updated_task(self, client, mock_service):
        updated = {**FAKE_TASK, "name": "Vacuum bedroom"}
        mock_service.update_task.return_value = updated

        resp = client.patch(f"/api/tasks/{FAKE_TASK_ID}", json={"name": "Vacuum bedroom"})

        assert resp.status_code == 200
        assert resp.json()["name"] == "Vacuum bedroom"

    def test_returns_404_when_task_not_found(self, client, mock_service):
        mock_service.update_task.side_effect = NotFoundException("Task not found.")

        resp = client.patch(f"/api/tasks/{FAKE_TASK_ID}", json={"name": "New name"})

        assert resp.status_code == 404

    def test_passes_only_set_fields(self, client, mock_service):
        mock_service.update_task.return_value = FAKE_TASK

        client.patch(f"/api/tasks/{FAKE_TASK_ID}", json={"name": "New name"})

        mock_service.update_task.assert_called_once_with(FAKE_USER_ID, FAKE_TASK_ID, {"name": "New name"})


class TestCompleteTask:
    def test_returns_200_with_completed_task(self, client, mock_service):
        mock_service.complete_task.return_value = FAKE_COMPLETED_TASK

        resp = client.post(f"/api/tasks/{FAKE_TASK_ID}/complete")

        assert resp.status_code == 200
        assert resp.json()["completed_at"] is not None

    def test_returns_404_when_not_found_or_already_completed(self, client, mock_service):
        mock_service.complete_task.side_effect = NotFoundException("Task not found or already completed.")

        resp = client.post(f"/api/tasks/{FAKE_TASK_ID}/complete")

        assert resp.status_code == 404


class TestDeleteTask:
    def test_returns_204_on_success(self, client, mock_service):
        mock_service.delete_task.return_value = None

        resp = client.delete(f"/api/tasks/{FAKE_TASK_ID}")

        assert resp.status_code == 204

    def test_returns_404_when_not_found_or_completed(self, client, mock_service):
        mock_service.delete_task.side_effect = NotFoundException("Task not found or already completed.")

        resp = client.delete(f"/api/tasks/{FAKE_TASK_ID}")

        assert resp.status_code == 404
