import asyncio
import httpx
import json
import time
import logging
from bs4 import BeautifulSoup
from markdownify import markdownify as md
from collections import defaultdict
from urllib.parse import urlparse

# ----------------------------
# CONFIG
# ----------------------------

URL_FILE = "recipe_urls.txt"
CONCURRENCY = 15

MEAT_KEYWORDS = {"chicken", "beef", "pork", "fish", "salmon", "shrimp", "bacon", "lamb", "tuna", "anchovy"}

JUNK_KEYWORDS = {"what is", "guide", "glossary", "tips", "how to choose", "basics", "technique"}

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")

# ----------------------------
# STATS
# ----------------------------

stats = defaultdict(int)
rejection_reasons = defaultdict(int)
site_stats = defaultdict(lambda: defaultdict(int))
accepted_recipes = []


def site(url: str) -> str:
    return urlparse(url).netloc


def record(url: str, status: str, reason: str = ""):
    s = site(url)
    stats[status] += 1
    site_stats[s][status] += 1
    if reason:
        rejection_reasons[reason] += 1


# ----------------------------
# LOAD URLS
# ----------------------------


def load_urls(path: str) -> list[str]:
    with open(path, "r") as f:
        return [line.strip() for line in f if line.strip()]


# ----------------------------
# FETCH
# ----------------------------


async def fetch(client: httpx.AsyncClient, url: str) -> str | None:
    try:
        r = await client.get(url, follow_redirects=True, timeout=20)
        if r.status_code == 200:
            return r.text
        record(url, "failed_http", str(r.status_code))
    except Exception as e:
        record(url, "failed_http", str(e))
    return None


# ----------------------------
# JSON-LD EXTRACTION
# ----------------------------


def extract_jsonld(html: str):
    soup = BeautifulSoup(html, "html.parser")
    blocks = []

    for tag in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(tag.string or "")
            if isinstance(data, list):
                blocks.extend(data)
            else:
                blocks.append(data)
        except Exception:
            continue

    return blocks


def is_recipe(obj: dict) -> bool:
    t = obj.get("@type")
    if isinstance(t, list):
        return "Recipe" in t
    return t == "Recipe"


# ----------------------------
# MARKDOWN
# ----------------------------


def extract_markdown(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")

    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()

    return md(str(soup))


# ----------------------------
# FILTERS
# ----------------------------


def is_junk(obj: dict) -> bool:
    text = json.dumps(obj).lower()
    return any(k in text for k in JUNK_KEYWORDS)


def is_vegetarian(ingredients: list[str]) -> bool:
    text = " ".join(ingredients).lower()
    return not any(m in text for m in MEAT_KEYWORDS)


# ----------------------------
# NORMALIZATION
# ----------------------------


def normalize(obj: dict, url: str, markdown: str) -> dict:
    return {
        "id": url,
        "name": obj.get("name"),
        "ingredients": obj.get("recipeIngredient", []),
        "instructions": obj.get("recipeInstructions", ""),
        "prep_time_minutes": obj.get("prepTime"),
        "cook_time_minutes": obj.get("cookTime"),
        "servings": obj.get("recipeYield"),
        "image_uri": obj.get("image"),
        "source_url": url,
        "source_name": site(url),
        "raw_markdown": markdown,
    }


# ----------------------------
# CORE PIPELINE
# ----------------------------


async def process(url: str, client: httpx.AsyncClient):
    html = await fetch(client, url)

    if not html:
        record(url, "discarded", "fetch_failed")
        return

    markdown = extract_markdown(html)
    jsonlds = extract_jsonld(html)

    if not jsonlds:
        record(url, "discarded", "no_jsonld")
        return

    recipe_obj = None
    for obj in jsonlds:
        if isinstance(obj, dict) and is_recipe(obj):
            recipe_obj = obj
            break

    if not recipe_obj:
        record(url, "discarded", "not_recipe")
        return

    if is_junk(recipe_obj):
        record(url, "discarded", "junk_page")
        return

    ingredients = recipe_obj.get("recipeIngredient", [])
    if not ingredients:
        record(url, "discarded", "no_ingredients")
        return

    data = normalize(recipe_obj, url, markdown)
    data["is_vegetarian"] = is_vegetarian(ingredients)

    accepted_recipes.append(data)
    record(url, "accepted")

    logging.info(f"✔ accepted: {data['name']}")


# ----------------------------
# WORKER POOL
# ----------------------------


async def worker(queue: asyncio.Queue, client: httpx.AsyncClient):
    while True:
        url = await queue.get()
        if url is None:
            queue.task_done()
            break

        await process(url, client)
        queue.task_done()


# ----------------------------
# RUNNER
# ----------------------------


async def run(urls: list[str]):
    start = time.time()

    queue = asyncio.Queue()

    for url in urls:
        queue.put_nowait(url)

    async with httpx.AsyncClient() as client:
        workers = [asyncio.create_task(worker(queue, client)) for _ in range(CONCURRENCY)]

        await queue.join()

        for _ in workers:
            queue.put_nowait(None)

        await asyncio.gather(*workers)

    duration = time.time() - start

    # ----------------------------
    # REPORT
    # ----------------------------

    report = {
        "total_urls": len(urls),
        "accepted": stats["accepted"],
        "discarded": stats["discarded"],
        "failed_http": stats["failed_http"],
        "duration_sec": duration,
        "rejection_reasons": dict(rejection_reasons),
        "site_stats": {k: dict(v) for k, v in site_stats.items()},
    }

    print("\n======================")
    print("📊 INGESTION REPORT")
    print("======================\n")

    print(json.dumps(report, indent=2))

    # ----------------------------
    # SAVE OUTPUTS
    # ----------------------------

    with open("recipes.json", "w") as f:
        json.dump(accepted_recipes, f, indent=2)

    with open("ingestion_report.json", "w") as f:
        json.dump(report, f, indent=2)

    print("\n💾 Saved:")
    print(" - recipes.json")
    print(" - ingestion_report.json")


# ----------------------------
# ENTRYPOINT
# ----------------------------

if __name__ == "__main__":
    urls = load_urls(URL_FILE)
    asyncio.run(run(urls))
