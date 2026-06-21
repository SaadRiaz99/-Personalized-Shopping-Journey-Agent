"""Get trending products based on review count and rating."""

import logging
from typing import Optional
from . import qdrant_search

logger = logging.getLogger(__name__)
_TOP_K = 10
_MIN_REVIEWS = 1000


def get_trending_products(
    category: Optional[str] = None,
    top_k: int = _TOP_K,
    min_reviews: int = _MIN_REVIEWS,
) -> dict:
    results = qdrant_search.search(
        query="trending popular bestseller",
        category=category,
        min_rating=4.0,
        top_k=top_k * 3,
    )

    if results is None:
        return {"error": "Trending products unavailable"}

    items = [r for r in results if (r.get("review_count") or 0) >= min_reviews]

    items.sort(key=lambda x: -(x.get("review_count") or 0))

    return {"items": items[:top_k], "total": len(items), "category": category or "global"}
