from unittest.mock import MagicMock
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from src.controllers.api.recipes import router, get_recipe_service
from src.db.db import DB
from src.errors import NotFoundException
from src.service.recipes import RecipeService



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
