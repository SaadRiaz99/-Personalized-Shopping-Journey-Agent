import json                           # Convert tool results to JSON strings
from typing import Optional

from agents import function_tool       # Decorator to turn a function into an LLM tool

from agent.products import load_products, get_categories, get_by_id, get_by_tag


# ── Hardcoded high-quality catalogue (always available) ────────────────────────
CATALOGUE = [
    {"id": 1, "title": "Dune", "tags": ["sci-fi", "epic"], "rating": 4.8, "category": "Book"},
    {"id": 2, "title": "The Martian", "tags": ["sci-fi", "survival"], "rating": 4.5, "category": "Book"},
    {"id": 3, "title": "Atomic Habits", "tags": ["self-help", "productivity"], "rating": 4.7, "category": "Book"},
    {"id": 4, "title": "Deep Work", "tags": ["self-help", "focus"], "rating": 4.6, "category": "Book"},
    {"id": 5, "title": "Inception", "tags": ["sci-fi", "thriller"], "rating": 4.9, "category": "Movie"},
    {"id": 6, "title": "The Dark Knight", "tags": ["action", "drama"], "rating": 4.8, "category": "Movie"},
    {"id": 7, "title": "Parasite", "tags": ["drama", "thriller"], "rating": 4.7, "category": "Movie"},
    {"id": 8, "title": "Sony WH-1000XM5", "tags": ["headphones", "audio"], "rating": 4.6, "category": "Electronics"},
    {"id": 9, "title": "MacBook Air M3", "tags": ["laptop", "productivity"], "rating": 4.8, "category": "Electronics"},
    {"id": 10, "title": "Kindle Paperwhite", "tags": ["e-reader", "books"], "rating": 4.5, "category": "Electronics"},
    {"id": 11, "title": "Ergonomic Chair", "tags": ["furniture", "office"], "rating": 4.4, "category": "Home"},
    {"id": 12, "title": "Philips Hue Lights", "tags": ["smart-home", "lighting"], "rating": 4.3, "category": "Home"},
    {"id": 13, "title": "Samsung Galaxy S24", "tags": ["phone", "android", "smartphone"], "rating": 4.7, "category": "Electronics"},
    {"id": 14, "title": "iPhone 15 Pro", "tags": ["phone", "ios", "smartphone"], "rating": 4.8, "category": "Electronics"},
    {"id": 15, "title": "Google Pixel 8", "tags": ["phone", "android", "smartphone"], "rating": 4.5, "category": "Electronics"},
]


# ── Max results cap ────────────────────────────────────────────────────────────
_MAX_RESULTS = 20


def _all_items() -> list[dict]:
    """Return hardcoded catalogue + JSON file products merged together."""
    return CATALOGUE + load_products()


def search_items_fn(
    query:        str = "",
    category:     Optional[str] = None,
    min_price:    Optional[float] = None,
    max_price:    Optional[float] = None,
    min_rating:   Optional[float] = None,
    sort_by:      Optional[str] = "relevance",
    in_stock_only: bool = False,
) -> str:
    """Full-text search across item titles, categories, and tags.

    Supports filtering by category, price range, minimum rating, stock status,
    and sorting by rating or price.
    """
    q = query.lower()
    results = []
    for item in _all_items():
        if q not in item["title"].lower() and q not in item["category"].lower() and not any(q in t for t in item["tags"]):
            continue
        if category and item["category"].lower() != category.lower():
            continue
        if min_rating is not None and item["rating"] < min_rating:
            continue
        if min_price is not None:
            price = item.get("price")
            if price is not None and price < min_price:
                continue
        if max_price is not None:
            price = item.get("price")
            if price is not None and price > max_price:
                continue
        if in_stock_only:
            stock = item.get("in_stock")
            if stock is not None and not stock:
                continue
        results.append(item)

    if sort_by == "rating":
        results.sort(key=lambda x: -x["rating"])
    elif sort_by == "price_asc":
        results.sort(key=lambda x: x.get("price") or 0)
    elif sort_by == "price_desc":
        results.sort(key=lambda x: -(x.get("price") or 0))

    return json.dumps(results[:_MAX_RESULTS])


def filter_by_tag_fn(tag: str, min_rating: Optional[float] = None, category: Optional[str] = None) -> str:
    """Filter items by tag, optional minimum rating, and optional category."""
    # Use tag index for O(1) tag lookup on file products
    file_items = get_by_tag(tag)
    results = [item for item in CATALOGUE if tag in item["tags"]] + list(file_items)

    if min_rating is not None:
        results = [item for item in results if item["rating"] >= min_rating]
    if category is not None:
        results = [item for item in results if item["category"].lower() == category.lower()]
    return json.dumps(results[:_MAX_RESULTS])


def get_item_details_fn(item_id: int) -> str:
    """Retrieve full details for a specific item by ID."""
    for item in _all_items():
        if item["id"] == item_id:
            return json.dumps(item)
    return f"No item found with id {item_id}"


def list_categories_fn() -> str:
    """List all product categories available in the catalogue."""
    cats = get_categories()
    return json.dumps(cats)


# ── Register functions as LLM-callable tools ──────────────────────────────────
search_items     = function_tool(search_items_fn,     name_override="search_items",     strict_mode=False)
filter_by_tag    = function_tool(filter_by_tag_fn,    name_override="filter_by_tag",    strict_mode=False)
get_item_details = function_tool(get_item_details_fn, name_override="get_item_details", strict_mode=False)
list_categories  = function_tool(list_categories_fn,  name_override="list_categories",  strict_mode=False)
