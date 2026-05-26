from unittest.mock import MagicMock
import pytest

from src.db.db import DB
from src.errors import NotFoundException
from src.service.recipes import RecipeService


@pytest.fixture
def mock_db():
    return MagicMock(spec=DB)


@pytest.fixture
def service(mock_db):
    return RecipeService(mock_db)


class TestGetRecipeDetails:
    def test_success(self, service, mock_db):
        recipe_id = "recipe-123"
        mock_recipe = {
            "id": recipe_id,
            "name": "Pasta Carbonara",
            "recipe_type": "pasta",
            "ingredients": ["pasta", "eggs", "bacon"],
            "labels": ["italian"],
            "prep_time_minutes": 10,
            "cook_time_minutes": 20,
            "rating": 5,
        }
        mock_db.get_recipe_by_id.return_value = mock_recipe

        result = service.get_recipe_details(recipe_id)

        assert result["name"] == "Pasta Carbonara"
        assert result["rating"] == 5
        mock_db.get_recipe_by_id.assert_called_once_with(recipe_id)

    def test_not_found(self, service, mock_db):
        recipe_id = "nonexistent"
        mock_db.get_recipe_by_id.return_value = None

        with pytest.raises(NotFoundException):
            service.get_recipe_details(recipe_id)

        mock_db.get_recipe_by_id.assert_called_once_with(recipe_id)


class TestListRecipes:
    def test_success_no_filters(self, service, mock_db):
        mock_recipes = [
            {
                "id": "recipe-1",
                "name": "Pasta",
                "recipe_type": "pasta",
                "labels": ["italian"],
                "prep_time_minutes": 10,
                "cook_time_minutes": 20,
                "rating": 5,
            }
        ]
        mock_db.find_recipes.return_value = mock_recipes
        mock_db.count_recipes.return_value = 1

        result = service.list_recipes()

        assert result["total"] == 1
        assert len(result["items"]) == 1
        assert result["items"][0]["name"] == "Pasta"
        assert result["page"] == 1
        assert result["limit"] == 20

    def test_pagination_defaults(self, service, mock_db):
        mock_recipes = []
        mock_db.find_recipes.return_value = mock_recipes
        mock_db.count_recipes.return_value = 0

        result = service.list_recipes()

        assert result["page"] == 1
        assert result["limit"] == 20
        call_kwargs = mock_db.find_recipes.call_args[1]
        assert call_kwargs["page"] == 1
        assert call_kwargs["limit"] == 20

    def test_pagination_validation(self, service, mock_db):
        mock_recipes = []
        mock_db.find_recipes.return_value = mock_recipes
        mock_db.count_recipes.return_value = 0

        # Test invalid page (should default to 1)
        result = service.list_recipes(page=0)
        assert result["page"] == 1

        # Test limit capped at 100
        result = service.list_recipes(limit=200)
        call_kwargs = mock_db.find_recipes.call_args[1]
        assert call_kwargs["limit"] == 100

    @pytest.mark.parametrize(
        "call_kwargs, expected_forwarded",
        [
            ({"search": "pasta"}, {"search": "pasta"}),
            (
                {"sort_by": "rating", "sort_order": "desc"},
                {"sort_by": "rating", "sort_order": "desc"},
            ),
            (
                {"labels": ["vegan"], "ingredients": ["tomato"]},
                {"labels": ["vegan"], "ingredients": ["tomato"]},
            ),
        ],
    )
    def test_forwards_optional_filters_and_sorting(self, service, mock_db, call_kwargs, expected_forwarded):
        mock_recipes = []
        mock_db.find_recipes.return_value = mock_recipes
        mock_db.count_recipes.return_value = 0

        result = service.list_recipes(**call_kwargs)

        assert result["total"] == 0
        call_kwargs = mock_db.find_recipes.call_args[1]
        for key, value in expected_forwarded.items():
            assert call_kwargs[key] == value
