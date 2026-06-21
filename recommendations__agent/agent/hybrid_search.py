"""Hybrid search combining vector (Qdrant) and keyword (products) results with
Reciprocal Rank Fusion (RRF) for merged, ranked results."""

import json
import logging
from typing import Optional
from . import qdrant_search
from .tools import search_items_fn

logger = logging.getLogger(__name__)
_RRF_K = 60


def _rrf_fusion(
    ranked_lists: list[list[dict]],
    id_key: str = "id",
    score_key: str = "_rrf_score",
) -> list[dict]:
    scores: dict[int, float] = {}
    details: dict[int, dict] = {}
    for rank_list in ranked_lists:
        for rank, item in enumerate(rank_list):
            pid = item.get(id_key)
            if pid is None:
                continue
            scores[pid] = scores.get(pid, 0.0) + 1.0 / (_RRF_K + rank + 1)
            details[pid] = item
    merged = sorted(details.values(), key=lambda x: -scores[x[id_key]])
    for item in merged:
        item[score_key] = round(scores[item[id_key]], 4)
    return merged


def hybrid_search(
    query: str,
    category: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    min_rating: Optional[float] = None,
    in_stock_only: bool = False,
    search_mode: str = "hybrid",
    top_k: int = 10,
) -> dict:
    if search_mode == "semantic":
        vector_results = qdrant_search.search(
            query=query, category=category, min_price=min_price,
            max_price=max_price, min_rating=min_rating,
            in_stock_only=in_stock_only, top_k=top_k,
        )
        items = vector_results or []
        return {"items": items, "total": len(items), "mode": "semantic"}

    if search_mode == "keyword":
        kw_raw = json.loads(search_items_fn(
            query=query, category=category, min_price=min_price,
            max_price=max_price, min_rating=min_rating,
            in_stock_only=in_stock_only,
        ))
        items = kw_raw.get("items", [])
        return {"items": items, "total": len(items), "mode": "keyword"}

    if search_mode == "hybrid":
        vector_results = qdrant_search.search(
            query=query, category=category, min_price=min_price,
            max_price=max_price, min_rating=min_rating,
            in_stock_only=in_stock_only, top_k=top_k,
        )
        kw_raw = json.loads(search_items_fn(
            query=query, category=category, min_price=min_price,
            max_price=max_price, min_rating=min_rating,
            in_stock_only=in_stock_only,
        ))
        kw_items = kw_raw.get("items", [])
        lists_to_merge = []
        if vector_results:
            lists_to_merge.append(vector_results)
        if kw_items:
            lists_to_merge.append(kw_items)
        if not lists_to_merge:
            return {"items": [], "total": 0, "mode": "hybrid"}
        merged = _rrf_fusion(lists_to_merge)
        return {"items": merged[:top_k], "total": len(merged), "mode": "hybrid"}

    return {"items": [], "total": 0, "mode": search_mode}
