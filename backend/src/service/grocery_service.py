import re

from src.db.db import DB
from src.errors import NotFoundException
from src.utils.general import timestamp
from src.utils.logger import logger as log

_HISTORY_LIMIT = 30


def _norm_name(s: str) -> str:
    return re.sub(r"\s+", " ", str(s or "").lower().strip())


def _parse_qty(s: str | None) -> dict | None:
    if not s:
        return None
    m = re.match(r"^([\d]+(?:[.,]\d+)?)\s*(.*)$", str(s).strip())
    if not m:
        return None
    try:
        value = float(m.group(1).replace(",", "."))
    except ValueError:
        return None
    return {"value": value, "unit": (m.group(2) or "").strip().lower()}


def _merge_qty(a: str | None, b: str | None) -> str | None:
    if not a and not b:
        return None
    if not a:
        return b
    if not b:
        return a
    if _norm_name(a) == _norm_name(b):
        p = _parse_qty(a)
        if p:
            total = round(p["value"] * 2, 2)
            unit_part = f" {p['unit']}" if p["unit"] else ""
            return f"{total:g}{unit_part}"
    pa, pb = _parse_qty(a), _parse_qty(b)
    if pa and pb and pa["unit"] == pb["unit"]:
        total = round(pa["value"] + pb["value"], 2)
        unit_part = f" {pa['unit']}" if pa["unit"] else ""
        return f"{total:g}{unit_part}"
    return f"{a} + {b}"


class GroceryService:
    def __init__(self, db: DB):
        self.db = db

    def _resolve_household(self, user_id: str) -> str:
        household = self.db.get_household_by_user(user_id)
        if not household:
            raise NotFoundException("You must belong to a household to manage grocery items.")
        return household["id"]

    def list_items(self, user_id: str) -> dict:
        household_id = self._resolve_household(user_id)
        log.info(f"Listing grocery items for household {household_id}")
        active = self.db.find_grocery_items(household_id, bought=False)
        history = self.db.find_grocery_items(household_id, bought=True, limit=_HISTORY_LIMIT)
        log.info(f"Found {len(active)} active and {len(history)} history items for household {household_id}")
        all_items = active + history
        recipe_ids = list({i["source_recipe_id"] for i in all_items if i.get("source_recipe_id")})
        titles = self.db.get_recipe_titles_by_ids(recipe_ids)
        for item in all_items:
            item["source_recipe_title"] = titles.get(item.get("source_recipe_id"))
        return {"active": active, "history": history}

    def add_item(self, user_id: str, name: str, qty: str | None) -> dict:
        household_id = self._resolve_household(user_id)
        key = _norm_name(name)
        existing = self.db.find_active_grocery_item(household_id, key)
        if existing:
            merged_qty = _merge_qty(existing.get("qty"), qty)
            log.info(f"Merging '{name}' into existing item {existing['id']} (qty: {existing.get('qty')!r} + {qty!r} -> {merged_qty!r})")
            return self.db.update_grocery_item(existing["id"], {"qty": merged_qty})
        log.info(f"Adding new grocery item '{name}' (qty={qty!r}) to household {household_id}")
        return self.db.create_grocery_item(
            household_id=household_id,
            name=name.strip(),
            qty=qty or None,
            added_by=user_id,
        )

    def add_from_recipe(self, user_id: str, recipe_id: str, ingredients: list[dict]) -> list[dict]:
        household_id = self._resolve_household(user_id)
        log.info(f"Adding {len(ingredients)} ingredients from recipe {recipe_id} to household {household_id}")
        results = []
        skipped = 0
        merged = 0
        created = 0
        for ing in ingredients:
            ing_name = ing.get("name", "").strip()
            if not ing_name:
                skipped += 1
                continue
            ing_qty = ing.get("qty") or None
            key = _norm_name(ing_name)
            existing = self.db.find_active_grocery_item(household_id, key)
            if existing:
                merged_qty = _merge_qty(existing.get("qty"), ing_qty)
                log.info(f"Merging ingredient '{ing_name}' into existing item {existing['id']} (qty -> {merged_qty!r})")
                updated = self.db.update_grocery_item(existing["id"], {"qty": merged_qty})
                results.append(updated)
                merged += 1
            else:
                log.info(f"Adding ingredient '{ing_name}' (qty={ing_qty!r}) from recipe {recipe_id}")
                result = self.db.create_grocery_item(
                    household_id=household_id,
                    name=ing_name,
                    qty=ing_qty,
                    added_by=user_id,
                    source_recipe_id=recipe_id,
                )
                results.append(result)
                created += 1
        log.info(f"Recipe {recipe_id}: {created} created, {merged} merged, {skipped} skipped")
        return results

    def mark_bought(self, user_id: str, item_id: str) -> dict:
        household_id = self._resolve_household(user_id)
        log.info(f"Marking item {item_id} as bought for household {household_id}")
        result = self.db.update_grocery_item(
            item_id, {"bought": True, "bought_at": timestamp()}, household_id=household_id
        )
        if not result:
            log.warning(f"Item {item_id} not found in household {household_id}")
            raise NotFoundException("Grocery item not found.")
        return result

    def restore_item(self, user_id: str, item_id: str) -> dict:
        household_id = self._resolve_household(user_id)
        log.info(f"Restoring item {item_id} to active list for household {household_id}")
        # fetch is required here: we need name + qty to check for an active merge target
        item = self.db.get_grocery_item(item_id, household_id)
        if not item:
            log.warning(f"Item {item_id} not found in household {household_id}")
            raise NotFoundException("Grocery item not found.")
        key = _norm_name(item["name"])
        active_match = self.db.find_active_grocery_item(household_id, key)
        if active_match and active_match["id"] != item_id:
            merged_qty = _merge_qty(active_match.get("qty"), item.get("qty"))
            log.info(f"Merging restored item {item_id} into active item {active_match['id']} (qty -> {merged_qty!r})")
            updated = self.db.update_grocery_item(active_match["id"], {"qty": merged_qty})
            self.db.delete_grocery_item(item_id)
            return updated
        return self.db.update_grocery_item(item_id, {"bought": False, "bought_at": None})

    def remove_item(self, user_id: str, item_id: str) -> None:
        household_id = self._resolve_household(user_id)
        log.info(f"Removing item {item_id} from household {household_id}")
        deleted = self.db.delete_grocery_item(item_id, household_id=household_id)
        if not deleted:
            log.warning(f"Item {item_id} not found in household {household_id}")
            raise NotFoundException("Grocery item not found.")

    def clear_history(self, user_id: str) -> None:
        household_id = self._resolve_household(user_id)
        log.info(f"Clearing bought history for household {household_id}")
        self.db.delete_bought_grocery_items(household_id)
