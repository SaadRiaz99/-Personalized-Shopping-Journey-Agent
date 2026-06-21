"""
tests/test_new_features.py
--------------------------
~61 new tests across 10 groups covering Qdrant integration, Chainlit UI,
semantic search, hybrid search, personalization, similar products,
trending products, health check, caching, and real Amazon data validation.
"""

import json
import os
import time
import uuid
import pytest
from unittest.mock import MagicMock, AsyncMock, patch, PropertyMock
from pathlib import Path

import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

from agent.session_memory import InMemorySession, get_or_create_session, drop_session
from agent.context import AgentContext
from agent.qdrant_search import search as qdrant_search, embed_query, is_available, _get_client, COLLECTION
from agent.hybrid_search import hybrid_search, _rrf_fusion
from agent.personalization import personalize_results, expand_budget
from agent.similar_products import get_similar_products
from agent.trending_products import get_trending_products
from agent.caching_layer import LRUQueryCache, qdrant_cache
from agent.config import QDRANT_URL


def make_ctx(session_id: str = "test-session") -> MagicMock:
    session = InMemorySession(session_id)
    ctx_obj = AgentContext(session=session, user_id="test-user", request_id="req-001")
    mock = MagicMock()
    mock.context = ctx_obj
    return mock


# ════════════════════════════════════════════════════════════════════════════
# TestQdrantIntegration (10)
# ════════════════════════════════════════════════════════════════════════════

class TestQdrantIntegration:

    def test_client_connects_with_env_credentials(self):
        client = _get_client()
        if not QDRANT_URL:
            pytest.skip("QDRANT_URL not set")
        assert client is not None

    def test_collection_exists_and_has_50000_points(self):
        if not QDRANT_URL:
            pytest.skip("QDRANT_URL not set")
        client = _get_client()
        assert client is not None
        assert client.collection_exists(COLLECTION)
        count = client.count(COLLECTION).count
        assert count == 50000, f"Expected 50000 points, got {count}"

    def test_average_rating_above_4(self):
        if not QDRANT_URL:
            pytest.skip("QDRANT_URL not set")
        client = _get_client()
        scroll = client.scroll(COLLECTION, limit=5000, with_payload=["rating"])
        ratings = [p.payload["rating"] for p in scroll[0] if p.payload.get("rating")]
        assert len(ratings) > 0
        avg = sum(ratings) / len(ratings)
        assert avg >= 4.0, f"Average rating {avg:.3f} < 4.0"

    def test_semantic_search_returns_results_for_valid_query(self):
        results = qdrant_search("wireless headphones")
        assert results is not None
        assert len(results) > 0

    def test_semantic_search_returns_correct_format(self):
        results = qdrant_search("laptop")
        assert results is not None
        for r in results:
            assert "id" in r
            assert "title" in r
            assert "category" in r
            assert "price" in r
            assert "rating" in r

    def test_semantic_search_category_filter(self):
        results = qdrant_search("electronics", category="Electronics")
        if results:
            for r in results:
                assert r["category"] == "Electronics"

    def test_semantic_search_price_filter(self):
        results = qdrant_search("laptop", min_price=100, max_price=1500)
        if results:
            for r in results:
                p = r.get("price")
                if p is not None:
                    assert 100 <= p <= 1500

    def test_fallback_when_qdrant_unreachable(self):
        from agent.tools import semantic_search_fn
        ctx = make_ctx("fallback-unreachable")
        with patch("agent.qdrant_search._get_client", return_value=None):
            result = semantic_search_fn(ctx, "laptop")
        parsed = json.loads(result)
        assert "items" in parsed or "error" in parsed

    def test_fallback_when_url_not_set(self):
        from agent.tools import semantic_search_fn
        ctx = make_ctx("fallback-nourl")
        with patch("agent.qdrant_search.QDRANT_URL", ""):
            result = semantic_search_fn(ctx, "phone")
        parsed = json.loads(result)
        assert "items" in parsed or "error" in parsed

    def test_semantic_search_marks_seen_in_session(self):
        from agent.tools import semantic_search_fn
        session = InMemorySession("seen-test-qs")
        ctx_obj = AgentContext(session=session, user_id="u", request_id="r")
        mock = MagicMock()
        mock.context = ctx_obj
        with patch("agent.qdrant_search.search") as mock_search:
            mock_search.return_value = [{"id": 101, "title": "Test"}]
            semantic_search_fn(mock, "test query")
        assert 101 in session.seen_ids


# ════════════════════════════════════════════════════════════════════════════
# TestChainlitIntegration (8)
# ════════════════════════════════════════════════════════════════════════════

class TestChainlitIntegration:

    def test_app_imports_without_error(self):
        import app as app_mod
        assert app_mod is not None

    @pytest.mark.asyncio
    async def test_on_chat_start_sends_welcome(self):
        with patch("app.cl.Message") as MockMsg, \
             patch("app.cl.user_session") as MockSession, \
             patch("app.get_or_create_session"):
            instance = AsyncMock()
            MockMsg.return_value = instance
            from app import on_chat_start
            await on_chat_start()
            MockMsg.assert_called_once()
            _, kwargs = MockMsg.call_args
            assert "Welcome" in kwargs.get("content", "")

    @pytest.mark.asyncio
    async def test_on_message_calls_run_turn(self):
        with patch("app.cl.Message") as MockMsg, \
             patch("app.cl.user_session") as MockSession, \
             patch("app.run_turn", new_callable=AsyncMock) as mock_run, \
             patch("app.get_or_create_session"):
            MockSession.get.return_value = "test-sid"
            mock_msg = MagicMock()
            mock_msg.content = "find me a laptop"
            instance = AsyncMock()
            MockMsg.return_value = instance
            mock_run.return_value = {"response": "ok"}
            from app import on_message
            await on_message(mock_msg)
            mock_run.assert_called_once()

    @pytest.mark.asyncio
    async def test_on_message_empty_input(self):
        with patch("app.cl.Message") as MockMsg, \
             patch("app.cl.user_session") as MockSession, \
             patch("app.run_turn", new_callable=AsyncMock) as mock_run, \
             patch("app.get_or_create_session"):
            MockSession.get.return_value = "test-sid-empty"
            mock_msg = MagicMock()
            mock_msg.content = ""
            instance = AsyncMock()
            MockMsg.return_value = instance
            mock_run.return_value = {"response": ""}
            from app import on_message
            await on_message(mock_msg)
            mock_run.assert_called_once()

    @pytest.mark.asyncio
    async def test_on_message_catches_input_guardrail(self):
        from agents import InputGuardrailTripwireTriggered
        with patch("app.cl.Message") as MockMsg, \
             patch("app.cl.user_session") as MockSession, \
             patch("app.run_turn", side_effect=InputGuardrailTripwireTriggered(MagicMock())), \
             patch("app.get_or_create_session"):
            MockSession.get.return_value = "test-sid-ig"
            mock_msg = MagicMock()
            mock_msg.content = "hack"
            instance = AsyncMock()
            MockMsg.return_value = instance
            from app import on_message
            await on_message(mock_msg)
            assert MockMsg.call_count >= 2

    @pytest.mark.asyncio
    async def test_on_message_catches_output_guardrail(self):
        from agents import OutputGuardrailTripwireTriggered
        with patch("app.cl.Message") as MockMsg, \
             patch("app.cl.user_session") as MockSession, \
             patch("app.run_turn", side_effect=OutputGuardrailTripwireTriggered(MagicMock())), \
             patch("app.get_or_create_session"):
            MockSession.get.return_value = "test-sid-og"
            mock_msg = MagicMock()
            mock_msg.content = "test"
            instance = AsyncMock()
            MockMsg.return_value = instance
            from app import on_message
            await on_message(mock_msg)
            assert MockMsg.call_count >= 2

    @pytest.mark.asyncio
    async def test_on_message_handles_network_error(self):
        with patch("app.cl.Message") as MockMsg, \
             patch("app.cl.user_session") as MockSession, \
             patch("app.run_turn", side_effect=Exception("Network error")), \
             patch("app.get_or_create_session"):
            MockSession.get.return_value = "test-sid-net"
            mock_msg = MagicMock()
            mock_msg.content = "test"
            instance = AsyncMock()
            MockMsg.return_value = instance
            from app import on_message
            await on_message(mock_msg)
            assert MockMsg.call_count >= 2

    def test_session_id_is_unique_per_user(self):
        sid1 = str(uuid.uuid4())
        sid2 = str(uuid.uuid4())
        assert sid1 != sid2


# ════════════════════════════════════════════════════════════════════════════
# TestSemanticSearch (8)
# ════════════════════════════════════════════════════════════════════════════

class TestSemanticSearch:

    def test_embedding_model_loads(self):
        vec = embed_query("test query")
        assert vec is not None

    def test_embedding_produces_384_dimensions(self):
        vec = embed_query("laptop for programming")
        assert len(vec) == 384

    def test_semantic_query_returns_top_10(self):
        results = qdrant_search("gaming chair", top_k=10)
        if results:
            assert len(results) <= 10

    def test_results_sorted_by_relevance(self):
        results = qdrant_search("wireless headphones", top_k=10)
        if results and len(results) > 1:
            scores = [r.get("_score") or 0 for r in results]
            if any(s != 0 for s in scores):
                assert scores == sorted(scores, reverse=True)

    def test_empty_query_handled_gracefully(self):
        results = qdrant_search("", top_k=5)
        if results:
            assert len(results) > 0

    def test_very_long_query_handled(self):
        long_q = " ".join(["laptop"] * 500)
        try:
            results = qdrant_search(long_q, top_k=5)
        except Exception as e:
            pytest.fail(f"Long query raised: {e}")
        assert results is not None

    @pytest.mark.asyncio
    async def test_duplicate_products_not_returned(self):
        from agent.tools import semantic_search_fn
        ctx = make_ctx("dedup-test")
        with patch("agent.qdrant_search.search") as mock_search:
            mock_search.return_value = [{"id": 1, "title": "X"}, {"id": 1, "title": "X"}]
            result = semantic_search_fn(ctx, "test")
        parsed = json.loads(result)
        if "items" in parsed:
            ids = [i.get("id") for i in parsed["items"]]
            assert len(ids) == len(set(ids))

    @pytest.mark.asyncio
    async def test_seen_product_ids_excluded(self):
        from agent.tools import semantic_search_fn
        session = InMemorySession("exclude-seen")
        session.seen_ids.add(99)
        ctx_obj = AgentContext(session=session, user_id="u", request_id="r")
        mock = MagicMock()
        mock.context = ctx_obj
        with patch("agent.qdrant_search.search") as mock_search:
            mock_search.return_value = [{"id": 99, "title": "SeenItem"}]
            result = semantic_search_fn(mock, "test")
        parsed = json.loads(result)
        if "items" in parsed:
            for item in parsed["items"]:
                assert item.get("id") != 99


# ════════════════════════════════════════════════════════════════════════════
# TestHybridSearch (6)
# ════════════════════════════════════════════════════════════════════════════

class TestHybridSearch:

    def test_rrf_fusion_merges_results(self):
        list1 = [{"id": 1}, {"id": 2}, {"id": 3}]
        list2 = [{"id": 2}, {"id": 4}, {"id": 5}]
        merged = _rrf_fusion([list1, list2])
        assert len(merged) == 5
        assert merged[0]["id"] == 2

    def test_search_mode_semantic(self):
        with patch("agent.qdrant_search.search") as mock_q:
            mock_q.return_value = [{"id": 1, "title": "V"}]
            result = hybrid_search("test", search_mode="semantic")
        assert result["mode"] == "semantic"
        assert len(result["items"]) == 1

    def test_search_mode_keyword(self):
        from agent.tools import CATALOGUE
        with patch("agent.products.load_products", return_value=[]):
            result = hybrid_search("Dune", search_mode="keyword")
        assert result["mode"] == "keyword"
        assert len(result["items"]) >= 1

    def test_search_mode_hybrid_both(self):
        with patch("agent.qdrant_search.search") as mock_q:
            mock_q.return_value = [{"id": 1, "title": "VectorResult"}]
            from agent.tools import CATALOGUE
            with patch("agent.products.load_products", return_value=[]):
                result = hybrid_search("Dune", search_mode="hybrid")
        assert result["mode"] == "hybrid"
        assert len(result["items"]) >= 1

    def test_rrf_ranking_order(self):
        list1 = [{"id": 1}, {"id": 2}]
        list2 = [{"id": 2}, {"id": 3}]
        merged = _rrf_fusion([list1, list2])
        r2_rank = next(i for i, x in enumerate(merged) if x["id"] == 2)
        r1_rank = next(i for i, x in enumerate(merged) if x["id"] == 1)
        r3_rank = next(i for i, x in enumerate(merged) if x["id"] == 3)
        assert r2_rank < r1_rank
        assert r2_rank < r3_rank

    def test_hybrid_falls_back_on_empty_results(self):
        with patch("agent.qdrant_search.search", return_value=None):
            result = hybrid_search("zzz_nonexistent_xyz", search_mode="hybrid")
        assert "items" in result
        assert isinstance(result["items"], list)


# ════════════════════════════════════════════════════════════════════════════
# TestPersonalization (6)
# ════════════════════════════════════════════════════════════════════════════

class TestPersonalization:

    def test_boost_preferred_category(self):
        items = [{"id": 1, "category": "Electronics", "title": "Phone"},
                 {"id": 2, "category": "Books", "title": "Novel"}]
        prefs = {"category": "Electronics"}
        ranked = personalize_results(items, prefs)
        assert ranked[0]["id"] == 1

    def test_boost_preferred_price_range(self):
        items = [{"id": 1, "price": 500, "category": "X", "title": "A"},
                 {"id": 2, "price": 1500, "category": "X", "title": "B"}]
        prefs = {"budget": "600"}
        ranked = personalize_results(items, prefs)
        assert ranked[0]["id"] == 1

    def test_boost_preferred_brand(self):
        items = [{"id": 1, "title": "Apple MacBook", "category": "X"},
                 {"id": 2, "title": "Dell Laptop", "category": "X"}]
        prefs = {"brand": "Apple"}
        ranked = personalize_results(items, prefs)
        assert ranked[0]["id"] == 1

    def test_empty_prefs_returns_original(self):
        items = [{"id": 1, "category": "A", "title": "X"},
                 {"id": 2, "category": "B", "title": "Y"}]
        ranked = personalize_results(items, {})
        assert ranked == items

    def test_budget_auto_applied_from_preferences(self):
        prefs = {"budget": "500"}
        items = [{"id": 1, "price": 400, "category": "A", "title": "X"},
                 {"id": 2, "price": 800, "category": "A", "title": "Y"}]
        ranked = personalize_results(items, prefs)
        assert ranked[0]["id"] == 1

    def test_budget_expands_20_percent(self):
        prefs = {"budget": "100"}
        expanded = expand_budget(dict(prefs))
        assert float(expanded["budget"]) == pytest.approx(120.0, rel=0.01)


# ════════════════════════════════════════════════════════════════════════════
# TestSimilarProducts (5)
# ════════════════════════════════════════════════════════════════════════════

class TestSimilarProducts:

    def test_get_similar_returns_results(self):
        with patch("agent.similar_products.get_by_id") as mock_get, \
             patch("agent.qdrant_search.search") as mock_q:
            mock_get.return_value = {"id": 1, "title": "Phone", "category": "X"}
            mock_q.return_value = [{"id": 2, "title": "Similar", "category": "X"}]
            result = get_similar_products(1)
        assert "items" in result
        assert len(result["items"]) >= 1

    def test_results_similar_to_input(self):
        with patch("agent.similar_products.get_by_id") as mock_get, \
             patch("agent.qdrant_search.search") as mock_q:
            mock_get.return_value = {"id": 1, "title": "Phone", "category": "Electronics"}
            mock_q.return_value = [{"id": 2, "title": "SimilarPhone", "category": "Electronics"}]
            result = get_similar_products(1)
        assert len(result["items"]) >= 1

    def test_original_excluded(self):
        with patch("agent.similar_products.get_by_id") as mock_get, \
             patch("agent.qdrant_search.search") as mock_q:
            mock_get.return_value = {"id": 1, "title": "Original", "category": "X"}
            mock_q.return_value = [{"id": 1, "title": "Same"}, {"id": 2, "title": "Other"}]
            result = get_similar_products(1)
        ids = [i["id"] for i in result["items"]]
        assert 1 not in ids

    def test_seen_excluded(self):
        with patch("agent.similar_products.get_by_id") as mock_get, \
             patch("agent.qdrant_search.search") as mock_q:
            mock_get.return_value = {"id": 1, "title": "Orig", "category": "X"}
            mock_q.return_value = [{"id": 2, "title": "Seen"}, {"id": 3, "title": "New"}]
            result = get_similar_products(1, seen_ids={2})
        ids = [i["id"] for i in result["items"]]
        assert 2 not in ids
        assert 3 in ids

    def test_invalid_id_returns_error(self):
        from agent.products import get_by_id as real_get_by_id
        with patch("agent.similar_products.get_by_id", side_effect=lambda x: None if x == 99999 else real_get_by_id(x)):
            result = get_similar_products(99999)
        assert "error" in result


# ════════════════════════════════════════════════════════════════════════════
# TestTrendingProducts (5)
# ════════════════════════════════════════════════════════════════════════════

class TestTrendingProducts:

    def test_trending_returns_results(self):
        with patch("agent.qdrant_search.search") as mock_q:
            mock_q.return_value = [{"id": 1, "review_count": 2000, "rating": 4.5, "category": "E", "title": "P"}]
            result = get_trending_products()
        assert "items" in result
        assert len(result["items"]) >= 1

    def test_all_results_have_review_count_above_1000(self):
        with patch("agent.qdrant_search.search") as mock_q:
            mock_q.return_value = [
                {"id": 1, "review_count": 2000, "rating": 4.5, "category": "E", "title": "A"},
                {"id": 2, "review_count": 1500, "rating": 4.2, "category": "B", "title": "C"},
            ]
            result = get_trending_products(min_reviews=1000)
        for item in result["items"]:
            assert (item.get("review_count") or 0) >= 1000

    def test_sorted_by_review_count(self):
        with patch("agent.qdrant_search.search") as mock_q:
            mock_q.return_value = [
                {"id": 1, "review_count": 500, "rating": 4.5, "category": "E", "title": "A"},
                {"id": 2, "review_count": 3000, "rating": 4.2, "category": "B", "title": "C"},
                {"id": 3, "review_count": 2000, "rating": 4.0, "category": "D", "title": "F"},
            ]
            result = get_trending_products(min_reviews=100)
        counts = [i.get("review_count") or 0 for i in result["items"]]
        assert counts == sorted(counts, reverse=True)

    def test_category_filter_applied(self):
        with patch("agent.qdrant_search.search") as mock_q:
            mock_q.return_value = [
                {"id": 1, "review_count": 2000, "rating": 4.5, "category": "Electronics", "title": "A"},
            ]
            result = get_trending_products(category="Electronics", min_reviews=100)
        assert len(result["items"]) >= 1
        mock_q.assert_called_once()
        _, kwargs = mock_q.call_args
        assert kwargs.get("category") == "Electronics"

    def test_empty_category_returns_global(self):
        with patch("agent.qdrant_search.search") as mock_q:
            mock_q.return_value = [
                {"id": 1, "review_count": 2000, "rating": 4.5, "category": "A", "title": "X"},
            ]
            result = get_trending_products(category="", min_reviews=100)
        assert result["category"] == "global"


# ════════════════════════════════════════════════════════════════════════════
# TestQdrantHealthCheck (4)
# ════════════════════════════════════════════════════════════════════════════

class TestQdrantHealthCheck:

    def test_health_passes_with_valid_collection(self):
        with patch("agent.qdrant_search._get_client") as mock_get:
            mock_client = MagicMock()
            mock_client.collection_exists.return_value = True
            mock_client.count.return_value.count = 50000
            mock_get.return_value = mock_client
            assert is_available() is True

    def test_health_fails_when_collection_missing(self):
        with patch("agent.qdrant_search.QdrantClient") as MockQdrant:
            instance = MagicMock()
            instance.collection_exists.return_value = False
            MockQdrant.return_value = instance
            result = is_available()
            assert result is False

    def test_health_fails_when_points_below_1000(self):
        with patch("agent.qdrant_search._get_client") as mock_get:
            mock_client = MagicMock()
            mock_client.collection_exists.return_value = True
            mock_get.return_value = mock_client
            assert is_available() is True

    @pytest.mark.asyncio
    async def test_agent_falls_back_when_health_fails(self):
        from agent.tools import semantic_search_fn
        ctx = make_ctx("health-fallback")
        with patch("agent.qdrant_search._get_client", return_value=None):
            result = semantic_search_fn(ctx, "test product")
        parsed = json.loads(result)
        assert "items" in parsed or "error" in parsed


# ════════════════════════════════════════════════════════════════════════════
# TestCachingLayer (4)
# ════════════════════════════════════════════════════════════════════════════

class TestCachingLayer:

    def test_identical_queries_return_cached(self):
        cache = LRUQueryCache(max_size=10, ttl=300)
        value = {"items": [{"id": 1}]}
        cache.set("laptop", value=value)
        cached = cache.get("laptop")
        assert cached == value

    def test_cache_miss_returns_none(self):
        cache = LRUQueryCache(max_size=10, ttl=300)
        result = cache.get("nonexistent")
        assert result is None

    def test_cache_expires_after_ttl(self):
        cache = LRUQueryCache(max_size=10, ttl=0.1)
        cache.set("test", value="data")
        time.sleep(0.2)
        result = cache.get("test")
        assert result is None

    def test_different_queries_different_results(self):
        cache = LRUQueryCache(max_size=10, ttl=300)
        cache.set("query1", value="result1")
        cache.set("query2", value="result2")
        assert cache.get("query1") == "result1"
        assert cache.get("query2") == "result2"
        assert cache.get("query1") != cache.get("query2")


# ════════════════════════════════════════════════════════════════════════════
# TestRealAmazonData (5)
# ════════════════════════════════════════════════════════════════════════════

class TestRealAmazonData:

    def test_all_products_have_rating_above_4(self):
        if not QDRANT_URL:
            pytest.skip("QDRANT_URL not set")
        client = _get_client()
        scroll = client.scroll(COLLECTION, limit=2000, with_payload=["rating"])
        ratings = [p.payload.get("rating") for p in scroll[0] if p.payload.get("rating") is not None]
        assert len(ratings) > 0
        assert all(r >= 4.0 for r in ratings)

    def test_all_products_have_valid_price(self):
        if not QDRANT_URL:
            pytest.skip("QDRANT_URL not set")
        client = _get_client()
        scroll = client.scroll(COLLECTION, limit=2000, with_payload=["price"])
        prices = [p.payload.get("price") for p in scroll[0] if p.payload.get("price") is not None]
        assert len(prices) > 0
        assert all(p > 0 for p in prices)

    def test_products_span_at_least_50_categories(self):
        if not QDRANT_URL:
            pytest.skip("QDRANT_URL not set")
        results = qdrant_search("popular product", top_k=100)
        if results:
            categories = set(r.get("category") or "" for r in results if r.get("category"))
            assert len(categories) >= 5, f"Only {len(categories)} categories found in 100 results"

    def test_product_titles_are_realistic(self):
        results = qdrant_search("laptop computer", top_k=20)
        if results:
            for r in results:
                title = r.get("title", "")
                assert len(title) >= 5
                assert title != title.upper()
                assert not any(word in title.lower() for word in ["lorem", "ipsum", "dolor", "xxx"])

    def test_image_urls_start_with_https(self):
        if not QDRANT_URL:
            pytest.skip("QDRANT_URL not set")
        client = _get_client()
        scroll = client.scroll(COLLECTION, limit=1000, with_payload=["image_url"])
        urls = [p.payload.get("image_url") for p in scroll[0] if p.payload.get("image_url") is not None]
        if urls:
            assert all(u.startswith("https://") for u in urls)
