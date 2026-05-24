from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.controllers.api.battery_logs import get_battery_log_service, router
from src.controllers.api.users import get_current_user
from src.db.db import DB
from src.service.battery_logs import BatteryLogService

FAKE_USER = SimpleNamespace(id="00000000-0000-0000-0000-000000000001")
FAKE_HOUSEHOLD = {"id": "00000000-0000-0000-0000-000000000010", "name": "Home", "role": "owner"}
FAKE_LOG = {
    "id": "00000000-0000-0000-0000-000000000100",
    "user_id": "00000000-0000-0000-0000-000000000001",
    "household_id": "00000000-0000-0000-0000-000000000010",
    "level": 75,
    "note": "Feeling good",
    "effective_at": "2026-05-01T10:00:00+00:00",
    "logged_at": "2026-05-01T10:00:00+00:00",
}


@pytest.fixture
def mock_db():
    return MagicMock(spec=DB)


@pytest.fixture
def mock_service(mock_db):
    return BatteryLogService(mock_db)


@pytest.fixture
def client(mock_service):
    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_battery_log_service] = lambda: mock_service
    app.dependency_overrides[get_current_user] = lambda: FAKE_USER
    return TestClient(app)


class TestCreateBatteryLog:
    def test_creates_log(self, client, mock_db):
        mock_db.get_household_by_user.return_value = FAKE_HOUSEHOLD
        mock_db.create_battery_log.return_value = FAKE_LOG

        resp = client.post("/api/battery-logs", json={
            "level": 75,
            "note": "Feeling good",
            "effective_at": "2026-05-01T10:00:00Z",
        })
        assert resp.status_code == 201
        assert resp.json()["id"] == "00000000-0000-0000-0000-000000000100"

    def test_returns_404_when_no_household(self, client, mock_db):
        mock_db.get_household_by_user.return_value = None

        resp = client.post("/api/battery-logs", json={
            "level": 75,
            "effective_at": "2026-05-01T10:00:00Z",
        })
        assert resp.status_code == 404

    def test_validates_level_range(self, client):
        resp = client.post("/api/battery-logs", json={
            "level": 150,
            "effective_at": "2026-05-01T10:00:00Z",
        })
        assert resp.status_code == 422


class TestGetBatteryLogs:
    def test_returns_logs_in_time_window(self, client, mock_db):
        mock_db.get_household_by_user.return_value = FAKE_HOUSEHOLD
        mock_db.find_battery_logs_by_household.return_value = [FAKE_LOG]

        resp = client.get("/api/battery-logs", params={
            "start": "2026-05-01T00:00:00Z",
            "end": "2026-05-02T00:00:00Z",
        })
        assert resp.status_code == 200
        assert len(resp.json()) == 1

    def test_returns_404_when_no_household(self, client, mock_db):
        mock_db.get_household_by_user.return_value = None

        resp = client.get("/api/battery-logs", params={
            "start": "2026-05-01T00:00:00Z",
            "end": "2026-05-02T00:00:00Z",
        })
        assert resp.status_code == 404


class TestUpdateBatteryLog:
    def test_updates_log(self, client, mock_db):
        mock_db.update_battery_log.return_value = {**FAKE_LOG, "level": 50}

        resp = client.put("/api/battery-logs/00000000-0000-0000-0000-000000000100", json={"level": 50})
        assert resp.status_code == 200
        assert resp.json()["level"] == 50

    def test_returns_404_when_no_rows_affected(self, client, mock_db):
        mock_db.update_battery_log.return_value = None

        resp = client.put("/api/battery-logs/00000000-0000-0000-0000-000000000100", json={"level": 50})
        assert resp.status_code == 404


class TestDeleteBatteryLog:
    def test_deletes_log(self, client, mock_db):
        mock_db.delete_battery_log.return_value = True

        resp = client.delete("/api/battery-logs/00000000-0000-0000-0000-000000000100")
        assert resp.status_code == 204
        mock_db.delete_battery_log.assert_called_once_with("00000000-0000-0000-0000-000000000100", "00000000-0000-0000-0000-000000000001")

    def test_returns_404_when_no_rows_affected(self, client, mock_db):
        mock_db.delete_battery_log.return_value = False

        resp = client.delete("/api/battery-logs/00000000-0000-0000-0000-000000000100")
        assert resp.status_code == 404
