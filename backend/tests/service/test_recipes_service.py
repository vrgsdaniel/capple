from unittest.mock import MagicMock
import pytest

from src.repository.repository import Repository
from src.errors import NotFoundException
from src.service.recipes import RecipeService


@pytest.fixture
def mock_db():
    return MagicMock(spec=Repository)


@pytest.fixture
def service(mock_db):
    return RecipeService(mock_db)


class TestGetRecipeDetails:
    async def test_success_without_user(self, service, mock_db):
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

        result = await service.get_recipe_details(recipe_id)

        assert result["name"] == "Pasta Carbonara"
        assert result["rating"] == 5
        assert "liked" not in result
        mock_db.get_recipe_by_id.assert_called_once_with(recipe_id)
        mock_db.get_recipe_interactions.assert_not_called()

    async def test_success_with_user(self, service, mock_db):
        recipe_id = "recipe-123"
        user_id = "user-456"
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
        mock_interactions = {"liked": True, "cooked": False, "user_rating": 4}
        mock_db.get_recipe_by_id.return_value = mock_recipe
        mock_db.get_recipe_interactions.return_value = mock_interactions

        result = await service.get_recipe_details(recipe_id, user_id)

        assert result["name"] == "Pasta Carbonara"
        assert result["liked"] is True
        assert result["cooked"] is False
        assert result["user_rating"] == 4
        mock_db.get_recipe_by_id.assert_called_once_with(recipe_id)
        mock_db.get_recipe_interactions.assert_called_once_with(recipe_id, user_id)

    async def test_not_found(self, service, mock_db):
        recipe_id = "nonexistent"
        mock_db.get_recipe_by_id.return_value = None

        with pytest.raises(NotFoundException):
            await service.get_recipe_details(recipe_id)

        mock_db.get_recipe_by_id.assert_called_once_with(recipe_id)


class TestListRecipes:
    async def test_success_no_filters_without_user(self, service, mock_db):
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
        mock_db.find_recipes_with_count.return_value = (mock_recipes, 1)

        result = await service.list_recipes()

        assert result["total"] == 1
        assert len(result["items"]) == 1
        assert result["items"][0]["name"] == "Pasta"
        assert "liked" not in result["items"][0]
        assert result["page"] == 1
        assert result["limit"] == 20
        mock_db.get_recipes_interactions_bulk.assert_not_called()

    async def test_success_with_user(self, service, mock_db):
        user_id = "user-456"
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
        mock_interactions = {"recipe-1": {"liked": True, "cooked": False, "user_rating": 4}}
        mock_db.find_recipes_with_count.return_value = (mock_recipes, 1)
        mock_db.get_recipes_interactions_bulk.return_value = mock_interactions

        result = await service.list_recipes(user_id=user_id)

        assert result["total"] == 1
        assert result["items"][0]["liked"] is True
        assert result["items"][0]["user_rating"] == 4
        mock_db.get_recipes_interactions_bulk.assert_called_once_with(["recipe-1"], user_id)

    async def test_pagination_defaults(self, service, mock_db):
        mock_db.find_recipes_with_count.return_value = ([], 0)

        result = await service.list_recipes()

        assert result["page"] == 1
        assert result["limit"] == 20
        call_kwargs = mock_db.find_recipes_with_count.call_args[1]
        assert call_kwargs["page"] == 1
        assert call_kwargs["limit"] == 20

    async def test_pagination_validation(self, service, mock_db):
        mock_db.find_recipes_with_count.return_value = ([], 0)

        result = await service.list_recipes(page=0)
        assert result["page"] == 1

        result = await service.list_recipes(limit=200)
        call_kwargs = mock_db.find_recipes_with_count.call_args[1]
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
    async def test_forwards_optional_filters_and_sorting(self, service, mock_db, call_kwargs, expected_forwarded):
        mock_db.find_recipes_with_count.return_value = ([], 0)

        result = await service.list_recipes(**call_kwargs)

        assert result["total"] == 0
        actual_kwargs = mock_db.find_recipes_with_count.call_args[1]
        for key, value in expected_forwarded.items():
            assert actual_kwargs[key] == value


class TestToggleInteractions:
    """Test toggle interactions (like, cooked) - they share identical behavior."""

    @pytest.mark.parametrize(
        "interaction_type,service_method",
        [
            ("liked", "toggle_recipe_like"),
            ("cooked", "toggle_recipe_cooked"),
        ],
    )
    async def test_add_interaction_when_not_present(self, service, mock_db, interaction_type, service_method):
        recipe_id = "recipe-123"
        user_id = "user-456"
        mock_db.has_interaction.return_value = False
        mock_db.add_interaction.return_value = {"id": "interaction-1"}

        result = await getattr(service, service_method)(recipe_id, user_id)

        assert result is True
        mock_db.has_interaction.assert_called_once_with(recipe_id, user_id, interaction_type)
        mock_db.add_interaction.assert_called_once_with(recipe_id, user_id, interaction_type)

    @pytest.mark.parametrize(
        "interaction_type,service_method",
        [
            ("liked", "toggle_recipe_like"),
            ("cooked", "toggle_recipe_cooked"),
        ],
    )
    async def test_remove_interaction_when_present(self, service, mock_db, interaction_type, service_method):
        recipe_id = "recipe-123"
        user_id = "user-456"
        mock_db.has_interaction.return_value = True
        mock_db.remove_interaction.return_value = True

        result = await getattr(service, service_method)(recipe_id, user_id)

        assert result is False
        mock_db.has_interaction.assert_called_once_with(recipe_id, user_id, interaction_type)
        mock_db.remove_interaction.assert_called_once_with(recipe_id, user_id, interaction_type)

    @pytest.mark.parametrize(
        "service_method",
        ["toggle_recipe_like", "toggle_recipe_cooked"],
    )
    async def test_recipe_not_found_on_fk_violation(self, service, mock_db, service_method):
        recipe_id = "nonexistent"
        user_id = "user-456"
        mock_db.has_interaction.return_value = False
        mock_db.add_interaction.side_effect = NotFoundException("Referenced entity not found")

        with pytest.raises(NotFoundException):
            await getattr(service, service_method)(recipe_id, user_id)


class TestRateRecipe:
    async def test_rate_recipe_calls_upsert(self, service, mock_db):
        recipe_id = "recipe-123"
        user_id = "user-456"
        mock_db.upsert_interaction.return_value = {"id": "interaction-1"}

        result = await service.rate_recipe(recipe_id, user_id, 4)

        assert result == 4
        mock_db.upsert_interaction.assert_called_once_with(recipe_id, user_id, "rated", value=4)

    @pytest.mark.parametrize("invalid_rating", [0, 6, -1, 100])
    async def test_invalid_rating_out_of_range(self, service, mock_db, invalid_rating):
        with pytest.raises(ValueError, match="Rating must be between 1 and 5"):
            await service.rate_recipe("recipe-123", "user-456", invalid_rating)

    async def test_recipe_not_found_on_fk_violation(self, service, mock_db):
        mock_db.upsert_interaction.side_effect = NotFoundException("Referenced entity not found")

        with pytest.raises(NotFoundException):
            await service.rate_recipe("nonexistent", "user-456", 4)


class TestListRecipesWithInteractions:
    async def test_includes_interactions_for_all_recipes(self, service, mock_db):
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
        mock_interactions = {
            "recipe-1": {"liked": True, "cooked": False, "user_rating": None},
            "recipe-2": {"liked": False, "cooked": True, "user_rating": 5},
        }
        mock_db.find_recipes_with_count.return_value = (mock_recipes, 2)
        mock_db.get_recipes_interactions_bulk.return_value = mock_interactions

        result = await service.list_recipes(user_id=user_id)

        assert result["items"][0]["liked"] is True
        assert result["items"][0]["cooked"] is False
        assert result["items"][0]["user_rating"] is None

        assert result["items"][1]["liked"] is False
        assert result["items"][1]["cooked"] is True
        assert result["items"][1]["user_rating"] == 5
