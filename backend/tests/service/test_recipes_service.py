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
    @staticmethod
    def recipe(recipe_id: str, **overrides):
        recipe = {
            "id": recipe_id,
            "name": recipe_id,
            "recipe_type": "dinner",
            "labels": [],
            "ingredients": [],
            "prep_time_minutes": 10,
            "cook_time_minutes": 20,
            "rating": None,
            "num_ratings": 0,
            "image_uri": None,
            "relevance": 0.0,
        }
        return {**recipe, **overrides}

    @staticmethod
    def search_spec(**overrides):
        spec = {
            "text": None,
            "meal_types": [],
            "labels": [],
            "ingredients": [],
            "max_total_minutes": None,
            "liked": None,
            "cooked": None,
            "sort": "relevance",
            "page": 1,
            "limit": 24,
        }
        return {**spec, **overrides}

    @pytest.mark.parametrize(
        ("spec_patch", "recipe_patch", "interaction_patch"),
        [
            pytest.param({"meal_types": ["lunch"]}, {"recipe_type": "dinner"}, {}, id="meal-type"),
            pytest.param({"labels": ["quick"]}, {"labels": ["slow"]}, {}, id="label"),
            pytest.param({"ingredients": ["tomato"]}, {"ingredients": ["oats"]}, {}, id="ingredient"),
            pytest.param(
                {"max_total_minutes": 20},
                {"prep_time_minutes": 10, "cook_time_minutes": 20},
                {},
                id="total-time",
            ),
            pytest.param({"liked": True}, {}, {"liked": False}, id="liked"),
            pytest.param({"cooked": True}, {}, {"cooked": False}, id="cooked"),
        ],
    )
    async def test_each_filter_rejects_independently(
        self,
        service,
        mock_db,
        spec_patch,
        recipe_patch,
        interaction_patch,
    ):
        mock_db.find_recipe_candidates.return_value = [self.recipe("candidate", **recipe_patch)]
        mock_db.get_recipes_interactions_bulk.return_value = {
            "candidate": {
                "liked": True,
                "cooked": True,
                "user_rating": None,
                **interaction_patch,
            }
        }

        result = await service.list_recipes("user-456", self.search_spec(**spec_patch))

        assert result["items"] == []
        assert result["total"] == 0

    @pytest.mark.parametrize(
        ("spec_patch", "recipe_patch"),
        [
            pytest.param(
                {"meal_types": ["breakfast", "dinner"]},
                {"recipe_type": "dinner"},
                id="meal-types",
            ),
            pytest.param(
                {"labels": ["slow", "quick"]},
                {"labels": ["Quick"]},
                id="labels",
            ),
            pytest.param(
                {"ingredients": ["potato", "tomato"]},
                {"ingredients": [{"name": "Cherry Tomato"}]},
                id="ingredients",
            ),
        ],
    )
    async def test_multi_value_filters_use_any_semantics(
        self,
        service,
        mock_db,
        spec_patch,
        recipe_patch,
    ):
        mock_db.find_recipe_candidates.return_value = [self.recipe("matching", **recipe_patch)]
        mock_db.get_recipes_interactions_bulk.return_value = {
            "matching": {"liked": False, "cooked": False, "user_rating": 4}
        }

        result = await service.list_recipes("user-456", self.search_spec(**spec_patch))

        assert result["total"] == 1
        assert [item["id"] for item in result["items"]] == ["matching"]
        assert result["items"][0]["user_rating"] == 4
        assert result["items"][0]["image_uri"] == ""

    async def test_sorts_relevance_then_rating_then_name(self, service, mock_db):
        mock_db.find_recipe_candidates.return_value = [
            self.recipe("beta", name="Beta", relevance=0.5, rating=5, num_ratings=100),
            self.recipe("alpha", name="Alpha", relevance=0.5, rating=5, num_ratings=1),
            self.recipe("top", name="Top", relevance=0.8, rating=1, num_ratings=1),
            self.recipe("lower-rating", name="A", relevance=0.5, rating=4, num_ratings=99),
        ]
        mock_db.get_recipes_interactions_bulk.return_value = {}
        spec = {"text": "dinner", "sort": "relevance", "page": 1, "limit": 24}

        result = await service.list_recipes("user-456", spec)

        assert [item["id"] for item in result["items"]] == [
            "top",
            "alpha",
            "beta",
            "lower-rating",
        ]
        mock_db.find_recipe_candidates.assert_called_once_with("dinner")

    async def test_no_text_relevance_defaults_to_highest_rated_and_paginates(self, service, mock_db):
        mock_db.find_recipe_candidates.return_value = [
            self.recipe("unrated", name="A", rating=None),
            self.recipe("lower", name="B", rating=4, num_ratings=10),
            self.recipe("top-b", name="Beta", rating=5, num_ratings=3),
            self.recipe("top-a", name="Alpha", rating=5, num_ratings=3),
        ]
        mock_db.get_recipes_interactions_bulk.return_value = {}
        spec = {"text": None, "sort": "relevance", "page": 2, "limit": 2}

        result = await service.list_recipes("user-456", spec)

        assert result["total"] == 4
        assert [item["id"] for item in result["items"]] == ["lower", "unrated"]
        assert (result["page"], result["limit"]) == (2, 2)
        assert spec["sort"] == "relevance"

    @pytest.mark.parametrize(
        ("sort", "expected"),
        [
            ("fastest", ["fast", "slow"]),
            ("name", ["slow", "fast"]),
        ],
    )
    async def test_explicit_sorts(self, service, mock_db, sort, expected):
        mock_db.find_recipe_candidates.return_value = [
            self.recipe("fast", name="Zulu", prep_time_minutes=5, cook_time_minutes=5),
            self.recipe("slow", name="Alpha", prep_time_minutes=20, cook_time_minutes=20),
        ]
        mock_db.get_recipes_interactions_bulk.return_value = {}

        result = await service.list_recipes(
            "user-456",
            {"text": None, "sort": sort, "page": 1, "limit": 24},
        )

        assert [item["id"] for item in result["items"]] == expected


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
