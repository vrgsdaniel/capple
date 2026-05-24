from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from src.controllers.api.infrastructure import get_healthcheck_service, router
from src.db.db import DB
from src.service.healthcheck import HealthCheckDataService


@pytest.fixture
def mock_db():
    return MagicMock(spec=DB)


@pytest.fixture
def healthcheck_service(mock_db):
    return HealthCheckDataService(mock_db)


@pytest.fixture
def client(healthcheck_service):
    from fastapi import FastAPI

    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_healthcheck_service] = lambda: healthcheck_service
    return TestClient(app)


class TestLiveness:
    def test_returns_ok(self, client):
        resp = client.get("/api/healthcheck")
        assert resp.status_code == 200
        assert resp.json() == "OK"


class TestReadiness:
    def test_ready_when_db_alive(self, client, mock_db):
        mock_db.is_alive.return_value = True
        resp = client.get("/api/readiness")
        assert resp.status_code == 200
        assert resp.json()["serviceAvailable"] is True

    def test_not_ready_when_db_down(self, client, mock_db):
        mock_db.is_alive.return_value = False
        resp = client.get("/api/readiness")
        assert resp.status_code == 500
