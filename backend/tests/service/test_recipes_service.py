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


class TestSetContext:
    def test_set_context_loads_interactions(self, service, mock_db):
        user_id = "user-123"
        mock_interactions = [
            {"recipe_id": "recipe-1", "interaction_type": "liked", "value": None},
            {"recipe_id": "recipe-2", "interaction_type": "cooked", "value": None},
            {"recipe_id": "recipe-3", "interaction_type": "rated", "value": 4},
        ]
        mock_db.get_all_user_interactions.return_value = mock_interactions

        service.set_context({"user_id": user_id})

        assert service._user_id == user_id
        assert "recipe-1" in service._liked_recipes
        assert "recipe-2" in service._cooked_recipes
        assert service._rated_recipes["recipe-3"] == 4
        mock_db.get_all_user_interactions.assert_called_once_with(user_id)

    def test_set_context_resets_on_new_user(self, service, mock_db):
        # First set context with user-1
        mock_db.get_all_user_interactions.return_value = [
            {"recipe_id": "recipe-1", "interaction_type": "liked", "value": None},
        ]
        service.set_context({"user_id": "user-1"})
        assert "recipe-1" in service._liked_recipes

        # Now set context with user-2 (different interactions)
        mock_db.get_all_user_interactions.return_value = [
            {"recipe_id": "recipe-2", "interaction_type": "liked", "value": None},
        ]
        service.set_context({"user_id": "user-2"})

        # Old interactions should be cleared
        assert "recipe-1" not in service._liked_recipes
        assert "recipe-2" in service._liked_recipes

    def test_set_context_none_clears_user_id(self, service, mock_db):
        mock_db.get_all_user_interactions.return_value = []
        service.set_context({"user_id": "user-123"})
        assert service._user_id == "user-123"

        service.set_context(None)
        assert service._user_id is None


class TestGetRecipeDetailsWithInteractions:
    def test_includes_interactions_when_context_set(self, service, mock_db):
        recipe_id = "recipe-123"
        user_id = "user-456"
        mock_recipe = {
            "id": recipe_id,
            "name": "Pasta",
            "recipe_type": "pasta",
            "ingredients": ["pasta"],
            "labels": ["italian"],
            "prep_time_minutes": 10,
            "cook_time_minutes": 20,
            "rating": 5,
        }
        mock_db.get_recipe_by_id.return_value = mock_recipe
        mock_db.get_all_user_interactions.return_value = [
            {"recipe_id": recipe_id, "interaction_type": "liked", "value": None},
            {"recipe_id": recipe_id, "interaction_type": "rated", "value": 4},
        ]

        service.set_context({"user_id": user_id})
        result = service.get_recipe_details(recipe_id)

        assert result["liked"] is True
        assert result["cooked"] is False
        assert result["user_rating"] == 4

    def test_no_interactions_when_context_not_set(self, service, mock_db):
        recipe_id = "recipe-123"
        mock_recipe = {
            "id": recipe_id,
            "name": "Pasta",
            "recipe_type": "pasta",
            "ingredients": ["pasta"],
            "labels": ["italian"],
            "prep_time_minutes": 10,
            "cook_time_minutes": 20,
            "rating": 5,
        }
        mock_db.get_recipe_by_id.return_value = mock_recipe

        result = service.get_recipe_details(recipe_id)

        # Interactions should not be added when context not set
        assert "liked" not in result
        assert "cooked" not in result
        assert "user_rating" not in result


class TestToggleInteractions:
    """Test toggle interactions (like, cooked) - they share identical behavior."""

    @pytest.mark.parametrize(
        "interaction_type,service_method,cache_attr",
        [
            ("liked", "toggle_recipe_like", "_liked_recipes"),
            ("cooked", "toggle_recipe_cooked", "_cooked_recipes"),
        ],
    )
    def test_add_interaction_when_not_present(self, service, mock_db, interaction_type, service_method, cache_attr):
        recipe_id = "recipe-123"
        user_id = "user-456"
        mock_db.get_all_user_interactions.return_value = []
        mock_db.has_interaction.return_value = False
        mock_db.add_interaction.return_value = {"id": "interaction-1"}

        service.set_context({"user_id": user_id})
        result = getattr(service, service_method)(recipe_id)

        assert result is True
        assert recipe_id in getattr(service, cache_attr)
        mock_db.has_interaction.assert_called_once_with(recipe_id, user_id, interaction_type)
        mock_db.add_interaction.assert_called_once_with(recipe_id, user_id, interaction_type)

    @pytest.mark.parametrize(
        "interaction_type,service_method,cache_attr",
        [
            ("liked", "toggle_recipe_like", "_liked_recipes"),
            ("cooked", "toggle_recipe_cooked", "_cooked_recipes"),
        ],
    )
    def test_remove_interaction_when_present(self, service, mock_db, interaction_type, service_method, cache_attr):
        recipe_id = "recipe-123"
        user_id = "user-456"
        mock_db.get_all_user_interactions.return_value = [
            {"recipe_id": recipe_id, "interaction_type": interaction_type, "value": None}
        ]
        mock_db.has_interaction.return_value = True
        mock_db.remove_interaction.return_value = True

        service.set_context({"user_id": user_id})
        result = getattr(service, service_method)(recipe_id)

        assert result is False
        assert recipe_id not in getattr(service, cache_attr)
        mock_db.has_interaction.assert_called_once_with(recipe_id, user_id, interaction_type)
        mock_db.remove_interaction.assert_called_once_with(recipe_id, user_id, interaction_type)

    @pytest.mark.parametrize(
        "service_method",
        ["toggle_recipe_like", "toggle_recipe_cooked"],
    )
    def test_requires_context(self, service, mock_db, service_method):
        recipe_id = "recipe-123"

        with pytest.raises(ValueError, match="User context not available"):
            getattr(service, service_method)(recipe_id)


class TestRateRecipe:
    def test_rate_recipe_new_rating(self, service, mock_db):
        recipe_id = "recipe-123"
        user_id = "user-456"
        rating = 4
        mock_db.get_all_user_interactions.return_value = []
        mock_db.has_interaction.return_value = False
        mock_db.add_interaction.return_value = {"id": "interaction-1"}

        service.set_context({"user_id": user_id})
        result = service.rate_recipe(recipe_id, rating)

        assert result == 4
        assert service._rated_recipes[recipe_id] == 4
        mock_db.has_interaction.assert_called_once_with(recipe_id, user_id, "rated")
        mock_db.add_interaction.assert_called_once_with(recipe_id, user_id, "rated", value=rating)

    def test_update_existing_rating(self, service, mock_db):
        recipe_id = "recipe-123"
        user_id = "user-456"
        new_rating = 5
        mock_db.get_all_user_interactions.return_value = [
            {"recipe_id": recipe_id, "interaction_type": "rated", "value": 3}
        ]
        mock_db.has_interaction.return_value = True
        mock_db.update_interaction.return_value = {"id": "interaction-1", "value": new_rating}

        service.set_context({"user_id": user_id})
        result = service.rate_recipe(recipe_id, new_rating)

        assert result == 5
        assert service._rated_recipes[recipe_id] == 5
        mock_db.has_interaction.assert_called_once_with(recipe_id, user_id, "rated")
        mock_db.update_interaction.assert_called_once_with(recipe_id, user_id, "rated", value=new_rating)

    @pytest.mark.parametrize("invalid_rating", [0, 6, -1, 100])
    def test_invalid_rating_out_of_range(self, service, mock_db, invalid_rating):
        recipe_id = "recipe-123"
        user_id = "user-456"
        mock_db.get_all_user_interactions.return_value = []

        service.set_context({"user_id": user_id})

        with pytest.raises(ValueError, match="Rating must be between 1 and 5"):
            service.rate_recipe(recipe_id, invalid_rating)

    def test_requires_context(self, service, mock_db):
        recipe_id = "recipe-123"

        with pytest.raises(ValueError, match="User context not available"):
            service.rate_recipe(recipe_id, 4)


class TestListRecipesWithInteractions:
    def test_includes_interactions_for_all_recipes(self, service, mock_db):
        user_id = "user-456"
        mock_recipes = [
            {
                "id": "recipe-1",
                "name": "Pasta",
                "recipe_type": "pasta",
                "labels": [],
                "prep_time_minutes": 10,
                "cook_time_minutes": 20,
            },
            {
                "id": "recipe-2",
                "name": "Pizza",
                "recipe_type": "italian",
                "labels": [],
                "prep_time_minutes": 15,
                "cook_time_minutes": 25,
            },
        ]
        mock_db.get_all_user_interactions.return_value = [
            {"recipe_id": "recipe-1", "interaction_type": "liked", "value": None},
            {"recipe_id": "recipe-2", "interaction_type": "cooked", "value": None},
            {"recipe_id": "recipe-2", "interaction_type": "rated", "value": 5},
        ]
        mock_db.find_recipes.return_value = mock_recipes
        mock_db.count_recipes.return_value = 2

        service.set_context({"user_id": user_id})
        result = service.list_recipes()

        assert result["items"][0]["liked"] is True
        assert result["items"][0]["cooked"] is False
        assert result["items"][0]["user_rating"] is None

        assert result["items"][1]["liked"] is False
        assert result["items"][1]["cooked"] is True
        assert result["items"][1]["user_rating"] == 5
