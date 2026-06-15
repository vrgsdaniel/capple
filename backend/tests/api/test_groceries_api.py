from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.controllers.api.groceries import get_grocery_service, router
from src.controllers.api.users import get_current_user
from src.errors import NotFoundException
from src.service.grocery_service import GroceryService

FAKE_USER_ID = "00000000-0000-0000-0000-000000000001"
FAKE_USER = SimpleNamespace(id=FAKE_USER_ID)
FAKE_HOUSEHOLD_ID = "00000000-0000-0000-0000-000000000002"
FAKE_ITEM_ID = "00000000-0000-0000-0000-000000000003"
FAKE_RECIPE_ID = "00000000-0000-0000-0000-000000000004"

FAKE_ITEM = {
    "id": FAKE_ITEM_ID,
    "household_id": FAKE_HOUSEHOLD_ID,
    "name": "Milk",
    "qty": "2 L",
    "bought": False,
    "bought_at": None,
    "source_recipe_title": None,
    "added_by": FAKE_USER_ID,
    "created_at": "2026-06-14T10:00:00+00:00",
    "updated_at": "2026-06-14T10:00:00+00:00",
}

FAKE_BOUGHT_ITEM = {
    **FAKE_ITEM,
    "id": "00000000-0000-0000-0000-000000000005",
    "name": "Eggs",
    "bought": True,
    "bought_at": "2026-06-13T08:00:00+00:00",
}


@pytest.fixture
def mock_service():
    return MagicMock(spec=GroceryService)


@pytest.fixture
def client(mock_service):
    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_grocery_service] = lambda: mock_service
    app.dependency_overrides[get_current_user] = lambda: FAKE_USER
    return TestClient(app)


class TestListGroceryItems:
    def test_returns_200_with_active_and_history(self, client, mock_service):
        mock_service.list_items.return_value = {
            "active": [FAKE_ITEM],
            "history": [FAKE_BOUGHT_ITEM],
        }

        resp = client.get("/api/grocery-items")

        assert resp.status_code == 200
        body = resp.json()
        assert len(body["active"]) == 1
        assert len(body["history"]) == 1

    def test_returns_404_when_no_household(self, client, mock_service):
        mock_service.list_items.side_effect = NotFoundException("No household.")

        resp = client.get("/api/grocery-items")

        assert resp.status_code == 404


class TestAddGroceryItem:
    def test_returns_201_with_created_item(self, client, mock_service):
        mock_service.add_item.return_value = FAKE_ITEM

        resp = client.post("/api/grocery-items", json={"name": "Milk", "qty": "2 L"})

        assert resp.status_code == 201
        assert resp.json()["name"] == "Milk"

    def test_returns_201_without_qty(self, client, mock_service):
        mock_service.add_item.return_value = {**FAKE_ITEM, "qty": None}

        resp = client.post("/api/grocery-items", json={"name": "Milk"})

        assert resp.status_code == 201

    def test_returns_422_when_name_missing(self, client, mock_service):
        resp = client.post("/api/grocery-items", json={"qty": "2 L"})

        assert resp.status_code == 422
        mock_service.add_item.assert_not_called()

    def test_returns_422_when_name_empty(self, client, mock_service):
        resp = client.post("/api/grocery-items", json={"name": ""})

        assert resp.status_code == 422
        mock_service.add_item.assert_not_called()


class TestAddFromRecipe:
    def test_returns_201_with_created_items(self, client, mock_service):
        mock_service.add_from_recipe.return_value = [FAKE_ITEM]
        payload = {
            "recipe_id": FAKE_RECIPE_ID,
            "ingredients": [{"name": "Milk", "qty": "200 ml"}],
        }

        resp = client.post("/api/grocery-items/from-recipe", json=payload)

        assert resp.status_code == 201
        assert len(resp.json()) == 1
        mock_service.add_from_recipe.assert_called_once_with(
            FAKE_USER_ID, FAKE_RECIPE_ID, payload["ingredients"]
        )

    def test_returns_404_when_no_household(self, client, mock_service):
        mock_service.add_from_recipe.side_effect = NotFoundException("No household.")

        resp = client.post(
            "/api/grocery-items/from-recipe",
            json={"recipe_id": FAKE_RECIPE_ID, "ingredients": []},
        )

        assert resp.status_code == 404


class TestPatchGroceryItem:
    def test_mark_bought_returns_200(self, client, mock_service):
        mock_service.mark_bought.return_value = {**FAKE_ITEM, "bought": True}

        resp = client.patch(f"/api/grocery-items/{FAKE_ITEM_ID}", json={"bought": True})

        assert resp.status_code == 200
        assert resp.json()["bought"] is True
        mock_service.mark_bought.assert_called_once_with(FAKE_USER_ID, FAKE_ITEM_ID)

    def test_restore_returns_200(self, client, mock_service):
        mock_service.restore_item.return_value = FAKE_ITEM

        resp = client.patch(f"/api/grocery-items/{FAKE_ITEM_ID}", json={"bought": False})

        assert resp.status_code == 200
        mock_service.restore_item.assert_called_once_with(FAKE_USER_ID, FAKE_ITEM_ID)

    def test_returns_404_when_item_not_found(self, client, mock_service):
        mock_service.mark_bought.side_effect = NotFoundException("Not found.")

        resp = client.patch(f"/api/grocery-items/{FAKE_ITEM_ID}", json={"bought": True})

        assert resp.status_code == 404


class TestDeleteGroceryItem:
    def test_returns_204(self, client, mock_service):
        resp = client.delete(f"/api/grocery-items/{FAKE_ITEM_ID}")

        assert resp.status_code == 204
        mock_service.remove_item.assert_called_once_with(FAKE_USER_ID, FAKE_ITEM_ID)

    def test_returns_404_when_item_not_found(self, client, mock_service):
        mock_service.remove_item.side_effect = NotFoundException("Not found.")

        resp = client.delete(f"/api/grocery-items/{FAKE_ITEM_ID}")

        assert resp.status_code == 404


class TestClearHistory:
    def test_returns_204(self, client, mock_service):
        resp = client.delete("/api/grocery-items/history")

        assert resp.status_code == 204
        mock_service.clear_history.assert_called_once_with(FAKE_USER_ID)

    def test_returns_404_when_no_household(self, client, mock_service):
        mock_service.clear_history.side_effect = NotFoundException("No household.")

        resp = client.delete("/api/grocery-items/history")

        assert resp.status_code == 404
