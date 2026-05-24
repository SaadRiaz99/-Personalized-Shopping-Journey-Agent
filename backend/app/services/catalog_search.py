import json
import os
from pathlib import Path
from typing import Optional

PRODUCTS_PATH = Path(__file__).parents[3] / "Catalog_search_agent" / "products.json"


def _load_products() -> list[dict]:
    path = PRODUCTS_PATH
    if not path.exists():
        alt = Path(__file__).parent / "products.json"
        if alt.exists():
            path = alt
        else:
            return []
    with open(path) as f:
        return json.load(f)


CATALOG_PRODUCTS: list[dict] = _load_products()

CATEGORIES: list[str] = sorted(set(p["category"] for p in CATALOG_PRODUCTS)) if CATALOG_PRODUCTS else []


def search_products(
    query: str = "",
    category: Optional[str] = None,
    max_price: Optional[float] = None,
    min_price: Optional[float] = None,
    min_rating: Optional[float] = None,
    sort_by: str = "relevance",
    page: int = 1,
    page_size: int = 20,
) -> dict:
    results = list(CATALOG_PRODUCTS)

    q = query.strip().lower()
    if q:
        results = [
            p for p in results
            if q in p["name"].lower() or q in p["description"].lower()
        ]

    if category:
        results = [p for p in results if p["category"].lower() == category.lower()]

    if max_price is not None:
        results = [p for p in results if p["price"] <= max_price]

    if min_price is not None:
        results = [p for p in results if p["price"] >= min_price]

    if min_rating is not None:
        results = [p for p in results if p["rating"] >= min_rating]

    if sort_by == "price_asc":
        results.sort(key=lambda p: p["price"])
    elif sort_by == "price_desc":
        results.sort(key=lambda p: p["price"], reverse=True)
    elif sort_by == "rating":
        results.sort(key=lambda p: p["rating"], reverse=True)
    elif sort_by == "name":
        results.sort(key=lambda p: p["name"])

    total = len(results)
    start = (page - 1) * page_size
    end = start + page_size
    page_results = results[start:end]

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": max(1, (total + page_size - 1) // page_size),
        "products": page_results,
        "query": query,
        "category": category,
    }


def get_product(product_id: int) -> Optional[dict]:
    return next((p for p in CATALOG_PRODUCTS if p["id"] == product_id), None)


def list_categories() -> list[str]:
    return CATEGORIES


def search_simple(query: str) -> list[dict]:
    result = search_products(query=query)
    return result["products"]


def get_recommendations_by_category(category: str, limit: int = 10) -> list[dict]:
    result = search_products(category=category, sort_by="rating", page_size=limit)
    return result["products"]
