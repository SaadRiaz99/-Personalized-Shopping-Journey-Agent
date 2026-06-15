import logging
from typing import Optional
from functools import lru_cache

from qdrant_client import QdrantClient
from qdrant_client.http.models import Filter, FieldCondition, MatchValue, Range, QueryResponse
from sentence_transformers import SentenceTransformer

from .config import QDRANT_URL, QDRANT_API_KEY

logger = logging.getLogger(__name__)

COLLECTION = "products"
DIM        = 384
MODEL_NAME = "all-MiniLM-L6-v2"
TOP_K      = 10

_SENTENCE_MODEL: SentenceTransformer | None = None


def _get_encoder() -> SentenceTransformer:
    global _SENTENCE_MODEL
    if _SENTENCE_MODEL is None:
        logger.info("Loading embedding model %s ...", MODEL_NAME)
        _SENTENCE_MODEL = SentenceTransformer(MODEL_NAME)
    return _SENTENCE_MODEL


def _get_client() -> QdrantClient | None:
    if not QDRANT_URL:
        return None
    try:
        return QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY, timeout=10)
    except Exception as e:
        logger.warning("Failed to create Qdrant client: %s", e)
        return None


def embed_query(text: str) -> list[float]:
    encoder = _get_encoder()
    return encoder.encode(text, normalize_embeddings=True).tolist()


def _build_filter(
    category: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    min_rating: Optional[float] = None,
    in_stock_only: bool = False,
) -> Filter | None:
    conditions = []
    if category:
        conditions.append(FieldCondition(key="category", match=MatchValue(value=category)))
    if min_price is not None:
        conditions.append(FieldCondition(key="price", range=Range(gte=min_price)))
    if max_price is not None:
        conditions.append(FieldCondition(key="price", range=Range(lte=max_price)))
    if min_rating is not None:
        conditions.append(FieldCondition(key="rating", range=Range(gte=min_rating)))
    if in_stock_only:
        conditions.append(FieldCondition(key="in_stock", match=MatchValue(value=True)))
    return Filter(must=conditions) if conditions else None


def search(
    query: str,
    category: Optional[str] = None,
    min_price: Optional[float] = None,
    max_price: Optional[float] = None,
    min_rating: Optional[float] = None,
    in_stock_only: bool = False,
    top_k: int = TOP_K,
) -> list[dict] | None:
    client = _get_client()
    if client is None:
        return None

    try:
        info = client.get_collection(COLLECTION)
        count = client.count(COLLECTION).count
        if count == 0:
            logger.warning("Qdrant collection '%s' is empty", COLLECTION)
            return None
    except Exception as e:
        logger.warning("Qdrant collection check failed: %s", e)
        return None

    vector = embed_query(query)
    qfilter = _build_filter(category, min_price, max_price, min_rating, in_stock_only)

    try:
        hits = client.query_points(
            collection_name=COLLECTION,
            query=vector,
            query_filter=qfilter,
            limit=top_k,
            with_payload=True,
        ).points
    except Exception as e:
        logger.warning("Qdrant search failed: %s", e)
        return None

    results = []
    for h in hits:
        p = h.payload
        results.append({
            "id":       p.get("id"),
            "title":    p.get("title", ""),
            "category": p.get("category", ""),
            "price":    p.get("price"),
            "rating":   p.get("rating"),
            "in_stock": p.get("in_stock"),
            "discount": p.get("discount_pct"),
            "tags":     [],
        })
    return results


def is_available() -> bool:
    if not QDRANT_URL:
        return False
    try:
        client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY, timeout=5)
        return client.collection_exists(COLLECTION)
    except Exception:
        return False
