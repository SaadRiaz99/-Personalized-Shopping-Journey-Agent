"""LRU caching layer for Qdrant queries to avoid redundant embeddings + searches."""

import time
import logging
from collections import OrderedDict
from typing import Optional, Any

logger = logging.getLogger(__name__)
_DEFAULT_TTL = 300.0
_DEFAULT_MAX_SIZE = 128


class LRUQueryCache:
    def __init__(self, max_size: int = _DEFAULT_MAX_SIZE, ttl: float = _DEFAULT_TTL):
        self._max_size = max_size
        self._ttl = ttl
        self._cache: OrderedDict[str, tuple[float, Any]] = OrderedDict()

    def _key(
        self,
        query: str,
        category: Optional[str] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        min_rating: Optional[float] = None,
        in_stock_only: bool = False,
        top_k: int = 10,
    ) -> str:
        return f"{query}|{category}|{min_price}|{max_price}|{min_rating}|{in_stock_only}|{top_k}"

    def get(
        self,
        query: str,
        category: Optional[str] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        min_rating: Optional[float] = None,
        in_stock_only: bool = False,
        top_k: int = 10,
    ) -> Optional[Any]:
        key = self._key(query, category, min_price, max_price, min_rating, in_stock_only, top_k)
        if key not in self._cache:
            return None
        ts, value = self._cache[key]
        if time.time() - ts > self._ttl:
            del self._cache[key]
            return None
        self._cache.move_to_end(key)
        return value

    def set(
        self,
        query: str,
        category: Optional[str] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        min_rating: Optional[float] = None,
        in_stock_only: bool = False,
        top_k: int = 10,
        value: Any = None,
    ):
        key = self._key(query, category, min_price, max_price, min_rating, in_stock_only, top_k)
        self._cache[key] = (time.time(), value)
        self._cache.move_to_end(key)
        if len(self._cache) > self._max_size:
            self._cache.popitem(last=False)

    def clear(self):
        self._cache.clear()

    def __len__(self) -> int:
        return len(self._cache)

    @property
    def ttl(self) -> float:
        return self._ttl


qdrant_cache = LRUQueryCache()
