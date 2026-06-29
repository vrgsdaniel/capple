import httpx
import xml.etree.ElementTree as ET
from urllib.parse import urljoin
import time
from typing import List, Set

# -----------------------------
# CONFIG: veg-focused sources
# -----------------------------
SEED_SITES = [
    "https://www.minimalistbaker.com",
    "https://cookieandkate.com",
    "https://www.loveandlemons.com",
    "https://www.pickuplimes.com",
    "https://www.budgetbytes.com",
    "https://www.bbcgoodfood.com",
    "https://www.seriouseats.com",
]


# High-signal category pages (VERY important)
CATEGORY_PAGES = [
    "https://www.minimalistbaker.com/recipe-index/?fwp_special-diet=vegan",
    "https://cookieandkate.com/recipes/",
    "https://www.loveandlemons.com/recipes/",
]

COMMON_SITEMAPS = [
    "/sitemap.xml",
    "/sitemap_index.xml",
    "/sitemap-index.xml",
    "/post-sitemap.xml",
    "/recipe-sitemap.xml",
]


VEG_KEYWORDS = [
    "vegetarian",
    "vegan",
    "plant",
    "lentil",
    "chickpea",
    "tofu",
    "vegetable",
    "curry",
]


def fetch(url: str) -> str:
    try:
        r = httpx.get(url, timeout=20, follow_redirects=True)
        if r.status_code == 200:
            return r.text
    except Exception:
        pass
    return ""


# -----------------------------
# SITEMAP PARSING
# -----------------------------
def parse_sitemap_urls(xml_text: str) -> List[str]:
    try:
        root = ET.fromstring(xml_text)
    except Exception:
        return []

    ns = {}
    if "}" in root.tag:
        ns = {"ns": root.tag.split("}")[0].strip("{")}

    urls = []
    for loc in root.findall(".//ns:loc", ns) if ns else root.findall(".//loc"):
        if loc.text:
            urls.append(loc.text)

    return urls


def is_sitemap_index(xml_text: str) -> bool:
    return "<sitemapindex" in xml_text.lower()


# -----------------------------
# CATEGORY PAGE LINK EXTRACTION
# (very lightweight HTML scan)
# -----------------------------
def extract_links_from_html(base_url: str, html: str) -> List[str]:
    links = []
    for part in html.split("href=")[1:]:
        quote = part[0]
        if quote not in ['"', "'"]:
            continue
        end = part.find(quote, 1)
        if end == -1:
            continue

        link = part[1:end]
        full = urljoin(base_url, link)

        if any(k in full for k in ["recipe", "recipes", "food"]):
            links.append(full)

    return links


# -----------------------------
# SITEMAP DISCOVERY
# -----------------------------
def get_sitemap_urls(site: str) -> List[str]:
    for path in COMMON_SITEMAPS:
        url = site.rstrip("/") + path
        xml = fetch(url)
        if not xml:
            continue

        if is_sitemap_index(xml):
            sub_sitemaps = parse_sitemap_urls(xml)

            all_urls = []
            for sm in sub_sitemaps:
                sub_xml = fetch(sm)
                all_urls.extend(parse_sitemap_urls(sub_xml))
                time.sleep(0.2)

            return all_urls

        else:
            return parse_sitemap_urls(xml)

    return []


# -----------------------------
# FILTERING
# -----------------------------
def is_probably_veg(url: str) -> bool:
    url = url.lower()
    return any(k in url for k in VEG_KEYWORDS)


def clean_urls(urls: List[str]) -> Set[str]:
    return {u.split("#")[0].split("?")[0] for u in urls if u.startswith("http")}


# -----------------------------
# MAIN PIPELINE
# -----------------------------
def crawl():
    all_urls = set()

    print("🔍 Crawling sitemaps...")
    for site in SEED_SITES:
        print(f"\nSite: {site}")

        urls = get_sitemap_urls(site)
        print(f"  sitemap URLs found: {len(urls)}")

        for u in urls:
            if is_probably_veg(u):
                all_urls.add(u)

        time.sleep(0.5)

    print("\n🌿 Crawling category pages...")
    for page in CATEGORY_PAGES:
        print(f"\nPage: {page}")
        html = fetch(page)

        links = extract_links_from_html(page, html)
        print(f"  links found: {len(links)}")

        all_urls.update(links)
        time.sleep(0.5)

    # cleanup
    all_urls = clean_urls(all_urls)

    print("\n-------------------------")
    print(f"✅ TOTAL UNIQUE URLS: {len(all_urls)}")
    print("-------------------------\n")

    # print sample
    for i, url in enumerate(list(all_urls)[:50]):
        print(f"{i+1}. {url}")

    # save
    with open("recipe_urls.txt", "w") as f:
        for url in sorted(all_urls):
            f.write(url + "\n")

    print("\n💾 Saved to recipe_urls.txt")


if __name__ == "__main__":
    crawl()
