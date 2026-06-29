import json
import asyncio
from src.repository.store import create_store_client
from src.repository.repository import Repository

# -----------------------------
# CONFIG
# -----------------------------

BACKUP_FILE = "existing_recipes_backup.json"


# -----------------------------
# LOAD BACKUP
# -----------------------------


def load_backup():
    """Load recipes from backup JSON file."""
    try:
        with open(BACKUP_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"❌ Backup file not found: {BACKUP_FILE}")
        return None
    except json.JSONDecodeError:
        print(f"❌ Invalid JSON in backup file: {BACKUP_FILE}")
        return None


# -----------------------------
# RESTORE
# -----------------------------


async def restore(repo: Repository):
    """Restore recipes from backup to database."""
    recipes = load_backup()

    if not recipes:
        print("No recipes to restore")
        return

    print(f"Loaded {len(recipes)} recipes from backup")

    try:
        result = await repo.bulk_insert_recipes(recipes)
        print(f"✅ Successfully restored {len(result)} recipes")
    except Exception as e:
        print(f"❌ Failed to restore recipes: {e}")


async def main():
    store_client = await create_store_client()
    repo = Repository(store_client)
    await restore(repo)


# -----------------------------
# ENTRYPOINT
# -----------------------------

if __name__ == "__main__":
    asyncio.run(main())
