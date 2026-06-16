"""Catalog search using hybrid semantic + vector search with Qdrant."""

from typing import Optional
from shared.products import ALL_PRODUCTS, CATEGORIES, get_product, list_categories, get_recommendations_by_category
from app.services.semantic_search import hybrid_search


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
    if query.strip():
        results = hybrid_search(query, category, min_price, max_price, min_rating)
    else:
        results = list(ALL_PRODUCTS)
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
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "total_pages": max(1, (total + page_size - 1) // page_size),
        "products": results[start:end],
        "query": query,
        "category": category,
    }


def search_simple(query: str) -> list[dict]:
    result = search_products(query=query)
    return result["products"]
