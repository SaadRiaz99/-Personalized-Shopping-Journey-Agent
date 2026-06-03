import json                            # For reading JSON product data from file
from collections import defaultdict    # Creates dict that auto-defaults missing keys
from pathlib import Path               # Cross-platform file path handling
from typing import Optional            # Type hint for optional parameters
from functools import lru_cache        # Cache for repeated search queries


# Path to the data directory (parent of agent/ → data/)
_DATA_DIR = Path(__file__).resolve().parent.parent / "data"
# Full path to the products JSON file
_PRODUCTS_FILE = _DATA_DIR / "products.json"

# Lazy-loaded caches (None until first load)
_catalogue: list[dict] | None = None           # All products
_by_id: dict[int, dict] | None = None          # Index: product_id → product
_by_category: dict[str, list[dict]] | None = None  # Index: category → products
_by_tag: dict[str, list[dict]] | None = None       # Index: tag → products

# Search result cache: maps (frozenset of param tuples) → JSON result
_search_cache: dict[str, str] = {}
_SEARCH_CACHE_MAX = 256


def _cache_key(
    query: str, category: str | None, min_price: float | None,
    max_price: float | None, min_rating: float | None,
    min_discount: int | None, in_stock_only: bool, sort_by: str,
    limit: int, offset: int,
) -> str:
    """Build a deterministic cache key from all search params."""
    return f"{query}|{category}|{min_price}|{max_price}|{min_rating}|{min_discount}|{in_stock_only}|{sort_by}|{limit}|{offset}"


def load_products() -> list[dict]:
    """Load all products from data/products.json (cached after first call)."""
    global _catalogue, _by_id, _by_category, _by_tag
    if _catalogue is None:                     # Only load once
        with open(_PRODUCTS_FILE, "r", encoding="utf-8") as f:
            _catalogue = json.load(f)          # Parse the 1M-product JSON array
        _by_id = {p["id"]: p for p in _catalogue}        # Build ID lookup dict
        _by_category = defaultdict(list)
        _by_tag = defaultdict(list)
        for p in _catalogue:                                # Group products by
            _by_category[p["category"]].append(p)           # their category field
            for t in p["tags"]:                              # and by each tag
                _by_tag[t].append(p)
    return _catalogue


def get_by_id(pid: int) -> dict | None:
    """Look up a single product by its numeric ID. Returns None if not found."""
    if _by_id is None:
        load_products()                          # Ensure cache is built
    return _by_id.get(pid)                       # Returns None for missing IDs


def get_categories() -> list[str]:
    """Return sorted list of all category names in the catalogue."""
    if _by_category is None:
        load_products()
    return sorted(_by_category.keys())           # Alphabetical order


def get_by_tag(tag: str) -> list[dict]:
    """Return all products with the given tag. Uses cached tag index."""
    if _by_tag is None:
        load_products()
    return _by_tag.get(tag, [])


def _has(p: dict, field: str) -> bool:
    """Check if a product dict has a given non-null field."""
    return field in p and p[field] is not None


def search(
    query:        Optional[str]   = None,   # Keyword(s) to match against title/tags
    category:     Optional[str]   = None,   # Only return products in this category
    min_price:    Optional[float] = None,   # Minimum price filter (if data has price)
    max_price:    Optional[float] = None,   # Maximum price filter (if data has price)
    min_rating:   Optional[float] = None,   # Minimum rating filter (1.0–5.0)
    min_discount: Optional[int]   = None,   # Minimum discount % filter (if data has discount)
    in_stock_only: bool           = False,  # Only return in-stock (if data has in_stock)
    sort_by:      str             = "relevance",  # "rating" | "price_asc" | "price_desc"
    limit:        int             = 10,     # Max results per page
    offset:       int             = 0,      # Pagination start index
) -> dict:
    """Search & filter the catalogue. Returns {items, total, offset, limit}."""

    # Build cache key from all params
    _query = query or ""
    key = _cache_key(_query, category, min_price, max_price, min_rating,
                     min_discount, in_stock_only, sort_by, limit, offset)

    # Check cache first
    cached = _search_cache.get(key)
    if cached is not None:
        return cached

    if _by_category is None:
        load_products()
    # Start with either a single category's products or the full catalogue
    pool = _by_category[category] if category and category in _by_category else _catalogue

    results: list[dict] = []
    # Split query into individual words — ALL must match (AND logic)
    words = [w.lower() for w in _query.split()] if _query else None

    for p in pool:
        # Skip if any query word is missing from title AND every tag
        if words and not all(
            w in p["title"].lower() or any(w in t for t in p["tags"])
            for w in words
        ):
            continue
        # Apply optional filters (each skipped if the field doesn't exist in data)
        if min_rating is not None and _has(p, "rating") and p["rating"] < min_rating:
            continue
        if min_price is not None and _has(p, "price") and p["price"] < min_price:
            continue
        if max_price is not None and _has(p, "price") and p["price"] > max_price:
            continue
        if in_stock_only and _has(p, "in_stock") and not p["in_stock"]:
            continue
        if min_discount is not None and _has(p, "discount") and p["discount"] < min_discount:
            continue
        results.append(p)                      # Passed all filters

    # Sort results if a sort mode is specified and the field exists
    if sort_by == "rating" and results and _has(results[0], "rating"):
        results.sort(key=lambda x: -x["rating"])
    elif sort_by == "price_asc" and results and _has(results[0], "price"):
        results.sort(key=lambda x: x["price"])
    elif sort_by == "price_desc" and results and _has(results[0], "price"):
        results.sort(key=lambda x: -x["price"])

    total = len(results)
    page  = results[offset: offset + limit]    # Slice for pagination

    result = {"items": page, "total": total, "offset": offset, "limit": limit}

    # Store in cache if under max size
    if len(_search_cache) < _SEARCH_CACHE_MAX:
        _search_cache[key] = result

    return result
