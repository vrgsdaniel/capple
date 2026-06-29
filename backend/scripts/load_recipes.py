import json
import asyncio
import uuid
from src.repository.store import create_store_client
from src.repository.repository import Repository
from rapidfuzz import fuzz

# -----------------------------
# CONFIG
# -----------------------------

INPUT_FILE = "../veggie_recipes.json"
SIMILARITY_THRESHOLD = 90  # title similarity


# -----------------------------
# NORMALIZATION HELPERS
# -----------------------------


def normalize_title(title: str) -> str:
    if not title:
        return ""
    return title.lower().strip()


def ingredient_signature(ingredients: list[str | dict]) -> set:
    """Extract ingredient names from list (handles both strings and dicts with 'item' key)."""
    result = set()
    for i in ingredients:
        if isinstance(i, dict):
            item = i.get("item", "")
        else:
            item = i
        result.add(str(item).lower().strip())
    return result


# -----------------------------
# RECIPE TRANSFORMATION
# -----------------------------


def transform_recipe(recipe: dict) -> dict | None:
    """Transform recipe to database schema. Returns None if transformation fails or recipe is not vegetarian."""
    try:
        return {
            "id": str(uuid.uuid4()),  # Generate new UUID
            "name": recipe.get("name", ""),
            "labels": recipe.get("labels", []),
            "ingredients": recipe.get("ingredients", []),
            "instructions": recipe.get("instructions", ""),
            "recipe_type": recipe.get("recipe_type"),
            "prep_time_minutes": recipe.get("prep_time_minutes", 0),
            "cook_time_minutes": recipe.get("cook_time_minutes", 0),
            "source_name": recipe.get("source_name", ""),
            "source_url": recipe.get("source_url", recipe.get("id", "")),
            "servings": recipe.get("servings"),
            "rating": recipe.get("rating"),
            "image_uri": recipe.get("image_uri", ""),
            "num_ratings": recipe.get("num_ratings", 0),
        }
    except Exception as e:
        print(f"❌ Failed to transform recipe {recipe.get('name', 'unknown')}: {e}")
        return None


def transform_recipes(recipes: list[dict]) -> list[dict]:
    """Transform multiple recipes, filtering out any that fail transformation."""
    transformed = []
    for recipe in recipes:
        result = transform_recipe(recipe)
        if result is not None:
            transformed.append(result)
    return transformed


# -----------------------------
# LOAD DATA
# -----------------------------


def load_recipes():
    with open(INPUT_FILE, "r") as f:
        return json.load(f)


# -----------------------------
# FETCH EXISTING RECIPES
# -----------------------------


async def fetch_existing(repo: Repository):
    result, _ = await repo.find_recipes_with_count(page=1, limit=1000)
    return result


# -----------------------------
# DUPLICATE DETECTION
# -----------------------------


def is_duplicate(new, existing):
    new_title = normalize_title(new["name"])
    new_ing = ingredient_signature(new["ingredients"])

    for r in existing:
        existing_title = normalize_title(r["name"])

        # 1. exact URL match (fast path)
        if new["source_url"] == r["source_url"]:
            return True, "same_url"

        # 2. fuzzy title match
        title_score = fuzz.token_set_ratio(new_title, existing_title)

        if title_score >= SIMILARITY_THRESHOLD:
            return True, f"title_match_{title_score}"

        # 3. ingredient overlap (secondary signal)
        if r["ingredients"]:
            existing_ing = ingredient_signature(r["ingredients"])
            overlap = len(new_ing & existing_ing) / max(len(new_ing), 1)

            if overlap > 0.9:
                return True, f"ingredient_overlap_{overlap:.2f}"

    return False, None


# -----------------------------
# MAIN PIPELINE
# -----------------------------


async def run(repo: Repository):
    data = load_recipes()

    print(f"Loaded {len(data)} recipes")

    existing = await fetch_existing(repo)

    # backup existing recipes to a JSON file
    with open("existing_recipes_backup.json", "w") as f:
        json.dump(existing, f, indent=2)

    inserted = 0
    skipped = 0
    duplicate_reasons = {}
    to_insert = []

    for r in data:
        dup, reason = is_duplicate(r, existing)

        if dup:
            skipped += 1
            duplicate_reasons[reason] = duplicate_reasons.get(reason, 0) + 1
            continue

        to_insert.append(r)
        existing.append(r)
        inserted += 1

    if to_insert:
        transformed = transform_recipes(to_insert)
        print(f"Transformed: {len(transformed)} recipes (filtered {len(to_insert) - len(transformed)})")
        if transformed:
            await repo.bulk_insert_recipes(transformed)
            print(f"✅ Successfully inserted {len(transformed)} recipes")

    print("\n====================")
    print("📊 INGESTION REPORT")
    print("====================")
    print(f"Inserted: {inserted}")
    print(f"Skipped: {skipped}")

    print("\n--- duplicate reasons ---")
    for k, v in duplicate_reasons.items():
        print(f"{k}: {v}")


async def main():
    store_client = await create_store_client()
    repo = Repository(store_client)
    await run(repo)


# -----------------------------
# ENTRYPOINT
# -----------------------------

if __name__ == "__main__":
    asyncio.run(main())
