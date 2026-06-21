"""Find products similar to a given product using Qdrant vector search."""

import logging
from typing import Optional
from . import qdrant_search
from .products import get_by_id

logger = logging.getLogger(__name__)
_TOP_K = 10


def get_similar_products(
    product_id: int,
    seen_ids: Optional[set] = None,
    top_k: int = _TOP_K,
) -> dict:
    item = get_by_id(product_id)
    if item is None:
        return {"error": f"No product found with id {product_id}"}

    title = item.get("title", "")
    category = item.get("category", "")

    results = qdrant_search.search(
        query=title,
        category=category,
        top_k=top_k + 1,
    )

    if results is None:
        return {"error": "Semantic search unavailable"}

    filtered = []
    for r in results:
        rid = r.get("id")
        if rid == product_id:
            continue
        if seen_ids and rid in seen_ids:
            continue
        filtered.append(r)
        if len(filtered) >= top_k:
            break

    return {
        "items": filtered,
        "total": len(filtered),
        "original_id": product_id,
        "original_title": title,
    }
