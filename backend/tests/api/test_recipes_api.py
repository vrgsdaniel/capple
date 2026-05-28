from types import SimpleNamespace
from unittest.mock import MagicMock
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.controllers.api.recipes import router, get_recipe_service
from src.controllers.api.users import get_current_user
from src.db.db import DB
from src.errors import NotFoundException
from src.service.recipes import RecipeService

FAKE_USER = SimpleNamespace(id="user-111")


@pytest.fixture
def mock_db():
    return MagicMock(spec=DB)


@pytest.fixture
def mock_service(mock_db):
    return RecipeService(mock_db)


@pytest.fixture
def client(mock_service):
    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_recipe_service] = lambda: mock_service
    app.dependency_overrides[get_current_user] = lambda: FAKE_USER
    return TestClient(app)


class TestGetRecipeDetails:
    def test_success(self, client, mock_service):
        recipe_id = "recipe-123"
        mock_recipe = {
            "id": recipe_id,
            "name": "Pasta Carbonara",
            "source_name": "Example Source",
            "source_url": "https://example.com/recipe",
            "recipe_type": "pasta",
            "ingredients": ["pasta", "eggs", "bacon"],
            "labels": ["italian", "quick"],
            "instructions": "Mix and cook",
            "prep_time_minutes": 10,
            "cook_time_minutes": 20,
            "servings": 4,
            "rating": 5,
            "image_uri": "https://example.com/image.jpg",
        }
        mock_service.get_recipe_details = MagicMock(return_value=mock_recipe)

        response = client.get(f"/api/recipes/{recipe_id}")

        assert response.status_code == 200
        assert response.json()["name"] == "Pasta Carbonara"
        assert response.json()["rating"] == 5
        mock_service.get_recipe_details.assert_called_once_with(recipe_id)

    def test_not_found(self, client, mock_service):
        recipe_id = "nonexistent"
        mock_service.get_recipe_details = MagicMock(side_effect=NotFoundException("Recipe not found."))

        response = client.get(f"/api/recipes/{recipe_id}")

        assert response.status_code == 404


class TestListRecipes:
    def test_success_no_filters(self, client, mock_service):
        mock_service.list_recipes = MagicMock(
            return_value={
                "items": [
                    {
                        "id": "recipe-1",
                        "name": "Pasta",
                        "recipe_type": "pasta",
                        "labels": ["italian"],
                        "prep_time_minutes": 10,
                        "cook_time_minutes": 20,
                        "rating": 5,
                    }
                ],
                "total": 1,
                "page": 1,
                "limit": 20,
            }
        )

        response = client.get("/api/recipes")

        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 1
        assert len(data["items"]) == 1
        assert data["items"][0]["name"] == "Pasta"

    def test_with_search_filter(self, client, mock_service):
        mock_service.list_recipes = MagicMock(
            return_value={
                "items": [
                    {
                        "id": "recipe-1",
                        "name": "Pasta Carbonara",
                        "recipe_type": "pasta",
                        "labels": ["italian"],
                        "prep_time_minutes": 10,
                        "cook_time_minutes": 20,
                        "rating": 5,
                    }
                ],
                "total": 1,
                "page": 1,
                "limit": 20,
            }
        )

        response = client.get("/api/recipes?search=pasta")

        assert response.status_code == 200
        mock_service.list_recipes.assert_called_once()
        call_kwargs = mock_service.list_recipes.call_args[1]
        assert call_kwargs["search"] == "pasta"

    def test_with_sorting(self, client, mock_service):
        mock_service.list_recipes = MagicMock(return_value={"items": [], "total": 0, "page": 1, "limit": 20})

        response = client.get("/api/recipes?sort_by=rating&sort_order=desc")

        assert response.status_code == 200
        call_kwargs = mock_service.list_recipes.call_args[1]
        assert call_kwargs["sort_by"] == "rating"
        assert call_kwargs["sort_order"] == "desc"

    def test_with_pagination(self, client, mock_service):
        mock_service.list_recipes = MagicMock(return_value={"items": [], "total": 50, "page": 2, "limit": 10})

        response = client.get("/api/recipes?page=2&limit=10")

        assert response.status_code == 200
        call_kwargs = mock_service.list_recipes.call_args[1]
        assert call_kwargs["page"] == 2
        assert call_kwargs["limit"] == 10

    def test_with_labels_filter(self, client, mock_service):
        mock_service.list_recipes = MagicMock(return_value={"items": [], "total": 0, "page": 1, "limit": 20})

        response = client.get("/api/recipes?labels=vegan&labels=quick")

        assert response.status_code == 200
        call_kwargs = mock_service.list_recipes.call_args[1]
        assert call_kwargs["labels"] == ["vegan", "quick"]


class TestToggleInteractions:
    """Test toggle endpoints (like, cooked) - they share the same behavior pattern."""

    @pytest.mark.parametrize(
        "endpoint,service_method,field_name,toggle_value,expected_field_value",
        [
            ("like", "toggle_recipe_like", "liked", True, True),
            ("like", "toggle_recipe_like", "liked", False, False),
            ("cooked", "toggle_recipe_cooked", "cooked", True, True),
            ("cooked", "toggle_recipe_cooked", "cooked", False, False),
        ],
    )
    def test_toggle_success(
        self, client, mock_service, endpoint, service_method, field_name, toggle_value, expected_field_value
    ):
        recipe_id = "recipe-123"
        mock_recipe = {
            "id": recipe_id,
            "name": "Pasta Carbonara",
            "source_name": "Example Source",
            "source_url": "https://example.com/recipe",
            "recipe_type": "pasta",
            "ingredients": ["pasta", "eggs", "bacon"],
            "labels": ["italian", "quick"],
            "instructions": "Mix and cook",
            "prep_time_minutes": 10,
            "cook_time_minutes": 20,
            "servings": 4,
            "rating": 5,
            "image_uri": "https://example.com/image.jpg",
            "liked": expected_field_value if field_name == "liked" else False,
            "cooked": expected_field_value if field_name == "cooked" else False,
            "user_rating": None,
        }
        setattr(mock_service, service_method, MagicMock(return_value=toggle_value))
        mock_service.get_recipe_details = MagicMock(return_value=mock_recipe)

        response = client.post(f"/api/recipes/{recipe_id}/{endpoint}")

        assert response.status_code == 200
        data = response.json()
        assert data[field_name] is expected_field_value
        getattr(mock_service, service_method).assert_called_once_with(recipe_id)
        mock_service.get_recipe_details.assert_called_once_with(recipe_id)

    @pytest.mark.parametrize(
        "endpoint,service_method,exception,expected_status",
        [
            ("like", "toggle_recipe_like", NotFoundException("Recipe not found."), 404),
            ("like", "toggle_recipe_like", ValueError("Invalid input"), 400),
            ("cooked", "toggle_recipe_cooked", NotFoundException("Recipe not found."), 404),
        ],
    )
    def test_toggle_errors(self, client, mock_service, endpoint, service_method, exception, expected_status):
        recipe_id = "recipe-123"
        setattr(mock_service, service_method, MagicMock(side_effect=exception))

        response = client.post(f"/api/recipes/{recipe_id}/{endpoint}")

        assert response.status_code == expected_status


class TestRateRecipe:
    def test_success_rate_recipe(self, client, mock_service):
        recipe_id = "recipe-123"
        rating = 4
        mock_recipe = {
            "id": recipe_id,
            "name": "Pasta Carbonara",
            "source_name": "Example Source",
            "source_url": "https://example.com/recipe",
            "recipe_type": "pasta",
            "ingredients": ["pasta", "eggs", "bacon"],
            "labels": ["italian", "quick"],
            "instructions": "Mix and cook",
            "prep_time_minutes": 10,
            "cook_time_minutes": 20,
            "servings": 4,
            "rating": 5,
            "image_uri": "https://example.com/image.jpg",
            "liked": False,
            "cooked": False,
            "user_rating": 4,
        }
        mock_service.rate_recipe = MagicMock(return_value=rating)
        mock_service.get_recipe_details = MagicMock(return_value=mock_recipe)

        response = client.post(f"/api/recipes/{recipe_id}/rate", json={"rating": rating})

        assert response.status_code == 200
        data = response.json()
        assert data["user_rating"] == 4
        mock_service.rate_recipe.assert_called_once_with(recipe_id, rating)
        mock_service.get_recipe_details.assert_called_once_with(recipe_id)

    @pytest.mark.parametrize("invalid_rating", [0, 6, -1, 10])
    def test_invalid_rating_values(self, client, mock_service, invalid_rating):
        recipe_id = "recipe-123"

        response = client.post(f"/api/recipes/{recipe_id}/rate", json={"rating": invalid_rating})

        assert response.status_code == 422  # Pydantic validation error

    @pytest.mark.parametrize(
        "exception,expected_status",
        [
            (ValueError("Rating must be between 1 and 5"), 400),
            (NotFoundException("Recipe not found."), 404),
        ],
    )
    def test_error_cases(self, client, mock_service, exception, expected_status):
        recipe_id = "recipe-123"
        mock_service.rate_recipe = MagicMock(side_effect=exception)

        response = client.post(f"/api/recipes/{recipe_id}/rate", json={"rating": 3})

        assert response.status_code == expected_status
