"""Hybrid semantic + vector search service for the backend catalog."""

import difflib
import os
from typing import Optional

from qdrant_client import QdrantClient
from qdrant_client.http import models as qdrant_models

from shared.products import ALL_PRODUCTS

import asyncio

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

COLLECTION_NAME = "catalog_products"
EMBED_DIM = 384

# ---------------------------------------------------------------------------
# Qdrant + Embeddings (lazy)
# ---------------------------------------------------------------------------

_embedder = None
_qdrant: QdrantClient | None = None
_qdrant_ready = False
_qdrant_error: Optional[str] = None


def _init_embedder():
    global _embedder
    if _embedder is None:
        from sentence_transformers import SentenceTransformer
        _embedder = SentenceTransformer("all-MiniLM-L6-v2")


def _embed_text(text: str) -> list[float]:
    return _embedder.encode(text).tolist()


def _product_text(p: dict) -> str:
    return f"{p['name']} {p['description']} {p['category']}"


def _build_index_sync():
    global _qdrant, _qdrant_ready, _qdrant_error
    try:
        _init_embedder()
        _qdrant = QdrantClient(":memory:")
        _qdrant.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=qdrant_models.VectorParams(
                size=EMBED_DIM, distance=qdrant_models.Distance.COSINE
            ),
        )
        points = []
        for i, p in enumerate(ALL_PRODUCTS):
            vec = _embed_text(_product_text(p))
            points.append(qdrant_models.PointStruct(id=p["id"], vector=vec, payload=p))
            if (i + 1) % 200 == 0:
                print(f"  Indexed {i+1}/{len(ALL_PRODUCTS)} products")
        _qdrant.upsert(collection_name=COLLECTION_NAME, points=points)
        _qdrant_ready = True
        print(f"  Qdrant ready ({len(ALL_PRODUCTS)} products indexed)")
    except Exception as e:
        _qdrant_error = str(e)
        print(f"  Qdrant indexing FAILED: {e}")


async def ensure_indexed():
    if _qdrant_ready or _qdrant_error:
        return
    await asyncio.to_thread(_build_index_sync)


def vector_search(query: str, top_k: int = 50) -> list[dict]:
    if not _qdrant_ready:
        return []
    try:
        vec = _embed_text(query)
        hits = _qdrant.search(
            collection_name=COLLECTION_NAME, query_vector=vec, limit=top_k,
        )
        return [h.payload for h in hits]
    except Exception:
        return []


def is_qdrant_ready():
    return _qdrant_ready


def qdrant_error():
    return _qdrant_error


# ---------------------------------------------------------------------------
# Semantic helpers
# ---------------------------------------------------------------------------


def _tokenize(text: str) -> list[str]:
    text = text.lower()
    table = str.maketrans("-_/.,:;!?()[]{}\"'", " " * 17)
    text = text.translate(table)
    return [t for t in text.split() if len(t) > 1]


def _stem(word: str) -> str:
    w = word
    if len(w) > 4 and w.endswith("ing"):
        w = w[:-3]
    elif len(w) > 3 and w.endswith("s") and not w.endswith("ss"):
        w = w[:-1]
    elif len(w) > 4 and w.endswith("ed"):
        w = w[:-2]
    return w


def _token_similarity(a: str, b: str) -> float:
    if a == b:
        return 1.0
    if _stem(a) == _stem(b):
        return 0.9
    shorter, longer = (a, b) if len(a) <= len(b) else (b, a)
    if len(shorter) >= len(longer) * 0.5 and shorter in longer:
        return 0.8
    return difflib.SequenceMatcher(None, a, b).ratio()


def _semantic_score(query: str, product: dict) -> float:
    q_tokens = _tokenize(query)
    if not q_tokens:
        return 1.0
    stops = {
        "the", "a", "an", "is", "are", "was", "were", "be", "to", "of", "in",
        "for", "on", "with", "at", "by", "from", "and", "or", "but", "not",
        "this", "that", "these", "those", "it", "its", "i", "you", "we", "they",
        "me", "my", "your", "our", "do", "does", "did", "have", "has", "had",
        "can", "will", "would", "could", "should", "may", "all", "each", "every",
        "some", "any", "no", "both", "what", "which", "who", "how", "why",
        "when", "where", "there", "here", "about", "up", "out", "if", "so",
    }
    relevant = [t for t in q_tokens if t not in stops]
    if not relevant:
        return 1.0
    name_tokens = _tokenize(product["name"])
    desc_tokens = _tokenize(product["description"])
    score = 0.0
    matched_strong = 0
    any_strong = False
    for qt in relevant:
        best = 0.0
        for pt in name_tokens:
            s = _token_similarity(qt, pt)
            if s > best:
                best = s
        for pt in desc_tokens:
            s = _token_similarity(qt, pt) * 0.7
            if s > best:
                best = s
        if best >= 0.7:
            matched_strong += 1
            any_strong = True
        score += best
    if not any_strong:
        return 0.0
    coverage = matched_strong / len(relevant)
    score *= (1 + coverage * 0.5)
    return score


# ---------------------------------------------------------------------------
# Hybrid search
# ---------------------------------------------------------------------------


def hybrid_search(
    query: str,
    category: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    min_rating: Optional[float] = None,
    semantic_weight: float = 0.4,
) -> list[dict]:
    results = list(ALL_PRODUCTS)
    if category:
        results = [p for p in results if p["category"].lower() == category.lower()]
    if min_price is not None:
        results = [p for p in results if p["price"] >= min_price]
    if max_price is not None:
        results = [p for p in results if p["price"] <= max_price]
    if min_rating is not None:
        results = [p for p in results if p["rating"] >= min_rating]

    semantic_scores = {p["id"]: _semantic_score(query, p) for p in results}
    max_ss = max(semantic_scores.values()) if semantic_scores else 1

    try:
        vector_results = vector_search(query, top_k=50)
        vector_ids = {p["id"] for p in vector_results}
        vector_rank = {pid: i for i, pid in enumerate(vector_ids)}
        max_vr = len(vector_ids)
    except Exception:
        vector_ids = set()
        vector_rank = {}
        max_vr = 1

    scored = []
    for p in results:
        ss = semantic_scores[p["id"]] / max_ss if max_ss else 0
        if ss == 0:
            continue
        if p["id"] in vector_rank:
            vs = 1.0 - (vector_rank[p["id"]] / max_vr)
        else:
            vs = 0.0
        combined = semantic_weight * ss + (1 - semantic_weight) * vs
        scored.append((p, combined))

    scored.sort(key=lambda x: -x[1])
    return [p for p, _ in scored]
