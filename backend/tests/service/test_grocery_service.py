from unittest.mock import MagicMock

import pytest

from src.db.db import DB
from src.errors import NotFoundException
from src.service.grocery_service import GroceryService

FAKE_USER_ID = "user-111"
FAKE_HOUSEHOLD_ID = "hh-222"
FAKE_HOUSEHOLD = {"id": FAKE_HOUSEHOLD_ID, "name": "Test Home"}
FAKE_RECIPE_ID = "recipe-333"

FAKE_ITEM = {
    "id": "item-aaa",
    "household_id": FAKE_HOUSEHOLD_ID,
    "name": "Milk",
    "qty": "2 L",
    "bought": False,
    "bought_at": None,
    "source_recipe_id": None,
    "added_by": FAKE_USER_ID,
    "created_at": "2026-06-14T10:00:00+00:00",
    "updated_at": "2026-06-14T10:00:00+00:00",
}

FAKE_BOUGHT_ITEM = {
    **FAKE_ITEM,
    "id": "item-bbb",
    "name": "Eggs",
    "qty": "12",
    "bought": True,
    "bought_at": "2026-06-13T08:00:00+00:00",
    "source_recipe_id": FAKE_RECIPE_ID,
}


@pytest.fixture
def mock_db():
    db = MagicMock(spec=DB)
    db.get_household_by_user.return_value = FAKE_HOUSEHOLD
    return db


@pytest.fixture
def service(mock_db):
    return GroceryService(mock_db)


class TestListItems:
    def test_returns_active_and_history(self, service, mock_db):
        mock_db.find_grocery_items.side_effect = [
            [dict(FAKE_ITEM)],
            [dict(FAKE_BOUGHT_ITEM)],
        ]
        mock_db.get_recipe_titles_by_ids.return_value = {FAKE_RECIPE_ID: "Omelette"}

        result = service.list_items(FAKE_USER_ID)

        assert len(result["active"]) == 1
        assert len(result["history"]) == 1

    def test_enriches_source_recipe_title(self, service, mock_db):
        mock_db.find_grocery_items.side_effect = [
            [],
            [dict(FAKE_BOUGHT_ITEM)],
        ]
        mock_db.get_recipe_titles_by_ids.return_value = {FAKE_RECIPE_ID: "Omelette"}

        result = service.list_items(FAKE_USER_ID)

        assert result["history"][0]["source_recipe_title"] == "Omelette"

    def test_source_recipe_title_is_none_when_no_recipe(self, service, mock_db):
        item = dict(FAKE_ITEM)
        mock_db.find_grocery_items.side_effect = [[item], []]
        mock_db.get_recipe_titles_by_ids.return_value = {}

        result = service.list_items(FAKE_USER_ID)

        assert result["active"][0]["source_recipe_title"] is None

    def test_raises_when_no_household(self, service, mock_db):
        mock_db.get_household_by_user.return_value = None

        with pytest.raises(NotFoundException):
            service.list_items(FAKE_USER_ID)


class TestAddItem:
    def test_creates_new_item(self, service, mock_db):
        mock_db.find_active_grocery_item.return_value = None
        mock_db.create_grocery_item.return_value = dict(FAKE_ITEM)

        service.add_item(FAKE_USER_ID, "Milk", "2 L")

        mock_db.create_grocery_item.assert_called_once_with(
            household_id=FAKE_HOUSEHOLD_ID,
            name="Milk",
            qty="2 L",
            added_by=FAKE_USER_ID,
        )

    def test_merges_qty_when_item_already_active(self, service, mock_db):
        existing = dict(FAKE_ITEM)  # has qty "2 L"
        mock_db.find_active_grocery_item.return_value = existing
        mock_db.update_grocery_item.return_value = {**existing, "qty": "3 L"}

        service.add_item(FAKE_USER_ID, "Milk", "1 L")

        mock_db.update_grocery_item.assert_called_once()
        merged_qty = mock_db.update_grocery_item.call_args.args[1]["qty"]
        assert merged_qty.lower() == "3 l"

    def test_merge_appends_with_plus_for_different_units(self, service, mock_db):
        existing = {**FAKE_ITEM, "qty": "200 g"}
        mock_db.find_active_grocery_item.return_value = existing
        mock_db.update_grocery_item.return_value = existing

        service.add_item(FAKE_USER_ID, "Flour", "1 cup")

        call_data = mock_db.update_grocery_item.call_args[0][1]
        assert call_data["qty"] == "200 g + 1 cup"

    def test_normalises_name_for_duplicate_check(self, service, mock_db):
        mock_db.find_active_grocery_item.return_value = None
        mock_db.create_grocery_item.return_value = dict(FAKE_ITEM)

        service.add_item(FAKE_USER_ID, "  MILK  ", None)

        mock_db.find_active_grocery_item.assert_called_once_with(FAKE_HOUSEHOLD_ID, "milk")

    def test_raises_when_no_household(self, service, mock_db):
        mock_db.get_household_by_user.return_value = None

        with pytest.raises(NotFoundException):
            service.add_item(FAKE_USER_ID, "Milk", None)


class TestAddFromRecipe:
    def test_creates_items_with_source_recipe_id(self, service, mock_db):
        mock_db.find_active_grocery_item.return_value = None
        mock_db.create_grocery_item.return_value = dict(FAKE_ITEM)
        ingredients = [{"name": "Milk", "qty": "200 ml"}, {"name": "Eggs", "qty": "2"}]

        service.add_from_recipe(FAKE_USER_ID, FAKE_RECIPE_ID, ingredients)

        assert mock_db.create_grocery_item.call_count == 2
        for call in mock_db.create_grocery_item.call_args_list:
            assert call.kwargs["source_recipe_id"] == FAKE_RECIPE_ID

    def test_merges_ingredient_into_existing_active_item(self, service, mock_db):
        existing = dict(FAKE_ITEM)  # Milk, 2 L
        mock_db.find_active_grocery_item.return_value = existing
        mock_db.update_grocery_item.return_value = existing

        service.add_from_recipe(FAKE_USER_ID, FAKE_RECIPE_ID, [{"name": "Milk", "qty": "1 L"}])

        mock_db.update_grocery_item.assert_called_once()
        mock_db.create_grocery_item.assert_not_called()

    def test_skips_ingredients_with_empty_name(self, service, mock_db):
        mock_db.create_grocery_item.return_value = dict(FAKE_ITEM)

        results = service.add_from_recipe(FAKE_USER_ID, FAKE_RECIPE_ID, [{"name": "", "qty": "1"}])

        assert results == []
        mock_db.create_grocery_item.assert_not_called()

    def test_returns_all_affected_items(self, service, mock_db):
        mock_db.find_active_grocery_item.return_value = None
        mock_db.create_grocery_item.side_effect = [
            {**FAKE_ITEM, "id": "item-1"},
            {**FAKE_ITEM, "id": "item-2"},
        ]

        results = service.add_from_recipe(FAKE_USER_ID, FAKE_RECIPE_ID, [{"name": "Milk"}, {"name": "Eggs"}])

        assert len(results) == 2


class TestMarkBought:
    def test_marks_item_as_bought(self, service, mock_db):
        updated = {**FAKE_ITEM, "bought": True}
        mock_db.update_grocery_item.return_value = updated

        result = service.mark_bought(FAKE_USER_ID, FAKE_ITEM["id"])

        assert result["bought"] is True
        call_kwargs = mock_db.update_grocery_item.call_args
        assert call_kwargs.kwargs["household_id"] == FAKE_HOUSEHOLD_ID
        assert call_kwargs.args[1]["bought"] is True
        assert "bought_at" in call_kwargs.args[1]

    def test_raises_when_item_not_found(self, service, mock_db):
        mock_db.update_grocery_item.return_value = None

        with pytest.raises(NotFoundException):
            service.mark_bought(FAKE_USER_ID, "nonexistent-id")


class TestRestoreItem:
    def test_restores_bought_item_to_active(self, service, mock_db):
        bought = dict(FAKE_BOUGHT_ITEM)
        mock_db.get_grocery_item.return_value = bought
        mock_db.find_active_grocery_item.return_value = None
        mock_db.update_grocery_item.return_value = {**bought, "bought": False, "bought_at": None}

        result = service.restore_item(FAKE_USER_ID, bought["id"])

        assert result["bought"] is False
        mock_db.update_grocery_item.assert_called_once_with(bought["id"], {"bought": False, "bought_at": None})

    def test_merges_into_existing_active_item_on_restore(self, service, mock_db):
        bought = {**FAKE_BOUGHT_ITEM, "name": "Milk", "qty": "1 L"}
        active_match = {**FAKE_ITEM, "name": "Milk", "qty": "2 L"}
        mock_db.get_grocery_item.return_value = bought
        mock_db.find_active_grocery_item.return_value = active_match
        mock_db.update_grocery_item.return_value = {**active_match, "qty": "3 L"}

        service.restore_item(FAKE_USER_ID, bought["id"])

        mock_db.update_grocery_item.assert_called_once()
        merged_qty = mock_db.update_grocery_item.call_args.args[1]["qty"]
        assert merged_qty.lower() == "3 l"
        mock_db.delete_grocery_item.assert_called_once_with(bought["id"])

    def test_raises_when_item_not_found(self, service, mock_db):
        mock_db.get_grocery_item.return_value = None

        with pytest.raises(NotFoundException):
            service.restore_item(FAKE_USER_ID, "nonexistent-id")


class TestRemoveItem:
    def test_deletes_item(self, service, mock_db):
        mock_db.delete_grocery_item.return_value = True

        service.remove_item(FAKE_USER_ID, FAKE_ITEM["id"])

        mock_db.delete_grocery_item.assert_called_once_with(FAKE_ITEM["id"], household_id=FAKE_HOUSEHOLD_ID)

    def test_raises_when_item_not_found(self, service, mock_db):
        mock_db.delete_grocery_item.return_value = False

        with pytest.raises(NotFoundException):
            service.remove_item(FAKE_USER_ID, "nonexistent-id")


class TestClearHistory:
    def test_deletes_all_bought_items(self, service, mock_db):
        service.clear_history(FAKE_USER_ID)

        mock_db.delete_bought_grocery_items.assert_called_once_with(FAKE_HOUSEHOLD_ID)

    def test_raises_when_no_household(self, service, mock_db):
        mock_db.get_household_by_user.return_value = None

        with pytest.raises(NotFoundException):
            service.clear_history(FAKE_USER_ID)
