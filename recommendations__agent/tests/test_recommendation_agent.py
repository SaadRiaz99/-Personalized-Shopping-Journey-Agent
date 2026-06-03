"""
tests/test_recommendation_agent.py
----------------------------------
Automated test suite for the ShopBot Recommendation Agent.

Categories:
  A. Cold Start Scenarios  (TC01–TC04)
  B. Filter Criteria       (TC05–TC10)
  C. LLM Output Format     (TC11–TC14)
  D. Latency / Stress      (TC15–TC17)
  E. Invalid / Malformed   (TC18–TC22)
  F. Session & Guardrails  (TC23–TC26)
"""

import json
import time
import pytest
from unittest.mock import MagicMock

import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

from agent.session_memory import InMemorySession, get_or_create_session, drop_session
from agent.context        import AgentContext
from agent.products       import load_products, search, get_by_id, get_categories
from agent.guardrails     import (
    injection_abuse_guardrail,
    off_topic_guardrail,
    response_quality_guardrail,
)
from agent.tools import (
    search_items_fn,
    filter_by_tag_fn,
    get_item_details_fn,
    compare_products_fn,
    _all_items,
    CATALOGUE,
)


_REQUIRED_FIELDS = {"id", "title", "tags", "rating", "category"}


def make_ctx(session_id: str = "test-session") -> MagicMock:
    session = InMemorySession(session_id)
    ctx_obj = AgentContext(session=session, user_id="test-user", request_id="req-001")
    mock = MagicMock()
    mock.context = ctx_obj
    return mock


def assert_valid_product(item: dict, msg: str = ""):
    missing = _REQUIRED_FIELDS - set(item.keys())
    assert not missing, f"{msg} — missing fields: {missing}"
    assert isinstance(item["id"], int), f"{msg} — id not int"
    assert isinstance(item["title"], str), f"{msg} — title not str"
    assert isinstance(item["tags"], list), f"{msg} — tags not list"
    assert isinstance(item["rating"], (int, float)), f"{msg} — rating not numeric"
    assert 0 <= item["rating"] <= 5, f"{msg} — rating out of range"
    assert isinstance(item["category"], str), f"{msg} — category not str"


def assert_valid_json(raw: str) -> list | dict:
    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        pytest.fail(f"Invalid JSON returned: {e}")


def _items(result_str: str) -> list:
    """Extract items from search result (handles paginated format)."""
    data = json.loads(result_str)
    if isinstance(data, dict) and "items" in data:
        return data["items"]
    return data


class TestColdStart:

    def test_tc01_fresh_session_has_empty_history(self):
        session = InMemorySession("cold-1")
        assert session.turn_count == 0
        assert len(session.seen_ids) == 0
        assert session.preferences == {}

    def test_tc02_fresh_session_default_preferences(self):
        session = InMemorySession("cold-2")
        assert session.preferences == {}
        assert isinstance(session.preferences, dict)

    def test_tc03_cold_search_returns_all_catalogue(self):
        all_items = _all_items()
        assert len(all_items) >= 15

    def test_tc04_independent_sessions_dont_share_state(self):
        s1 = InMemorySession("cold-a")
        s2 = InMemorySession("cold-b")
        s1.mark_seen([1, 2, 3])
        s2.mark_seen([4, 5])
        assert len(s1.seen_ids) == 3
        assert len(s2.seen_ids) == 2
        assert s1.seen_ids.isdisjoint(s2.seen_ids)


class TestFilterCriteria:

    def test_tc05_category_search_electronics(self):
        result = _items(search_items_fn("Electronics"))
        assert len(result) >= 1
        for item in result:
            assert item["category"] == "Electronics"

    def test_tc06_tag_and_min_rating(self):
        result = json.loads(filter_by_tag_fn("sci-fi", min_rating=4.7))
        assert len(result) >= 1
        for item in result:
            assert item["rating"] >= 4.7

    def test_tc07_multi_word_and_query(self):
        result = _items(search_items_fn("sci-fi"))
        titles = {r["title"] for r in result}
        assert "Dune" in titles
        assert "Inception" in titles

    def test_tc08_nonexistent_category_returns_empty(self):
        result = json.loads(search_items_fn("NonExistentCategory999"))
        assert result == {"items": [], "total": 0, "offset": 0}

    def test_tc09_search_with_min_rating_filter(self):
        results = search(query="phone", min_rating=4.7)
        for item in results["items"]:
            assert item["rating"] >= 4.7

    def test_tc10_search_pagination(self):
        results = search(query="book", limit=3, offset=0)
        assert len(results["items"]) <= 3
        assert results["limit"] == 3
        assert results["offset"] == 0


class TestLlmOutputFormat:

    def test_tc11_search_returns_valid_json(self):
        raw = search_items_fn("phone")
        data = assert_valid_json(raw)
        assert isinstance(data, dict)
        assert "items" in data
        assert isinstance(data["items"], list)

    def test_tc12_each_product_has_required_schema(self):
        raw = search_items_fn("phone")
        data = json.loads(raw)
        items = data["items"] if isinstance(data, dict) and "items" in data else data
        for i, item in enumerate(items):
            assert_valid_product(item, msg=f"product index {i}")

    def test_tc13_filter_by_tag_only_valid_tag(self):
        raw = filter_by_tag_fn("sci-fi")
        data = json.loads(raw)
        for item in data:
            assert "sci-fi" in item["tags"], f"{item['title']} missing 'sci-fi' tag"

    def test_tc14_get_item_details_returns_valid_schema(self):
        raw = get_item_details_fn(1)
        item = assert_valid_json(raw)
        assert_valid_product(item)
        assert item["id"] == 1
        assert item["title"] == "Dune"


class TestPropertyBased:

    def test_tc27_search_filters_dont_crash_random_combos(self):
        from hypothesis import given, strategies as st, settings

        @given(
            query=st.one_of(st.none(), st.text(max_size=10, min_size=0)),
            category=st.one_of(st.none(), st.sampled_from(["Book", "Movie", "Electronics", "Home", "Apparel", "Health", "Toys"])),
            min_price=st.one_of(st.none(), st.floats(0, 5000, allow_nan=False, allow_infinity=False)),
            max_price=st.one_of(st.none(), st.floats(0, 5000, allow_nan=False, allow_infinity=False)),
            min_rating=st.one_of(st.none(), st.floats(0, 5, allow_nan=False, allow_infinity=False)),
            sort_by=st.sampled_from(["relevance", "rating", "price_asc", "price_desc"]),
            in_stock_only=st.booleans(),
            limit=st.integers(1, 50),
            offset=st.integers(0, 100),
        )
        @settings(deadline=None, max_examples=50)
        def _check(query, category, min_price, max_price, min_rating, sort_by, in_stock_only, limit, offset):
            if min_price is not None and max_price is not None and min_price > max_price:
                min_price, max_price = max_price, min_price
            result = search(
                query=query, category=category,
                min_price=min_price, max_price=max_price,
                min_rating=min_rating,
                sort_by=sort_by, in_stock_only=in_stock_only,
                limit=limit, offset=offset,
            )
            assert isinstance(result, dict)
            assert "items" in result
            assert "total" in result
            assert isinstance(result["items"], list)
            assert len(result["items"]) <= limit

        _check()

    def test_tc28_search_results_always_match_filters(self):
        from hypothesis import given, strategies as st, settings

        @given(
            query=st.one_of(st.none(), st.text(max_size=10, min_size=1, alphabet=st.characters(min_codepoint=32, max_codepoint=126))),
            category=st.one_of(st.none(), st.sampled_from(["Book", "Movie", "Electronics"])),
            min_price=st.one_of(st.none(), st.floats(0, 1000, allow_nan=False, allow_infinity=False)),
            max_price=st.one_of(st.none(), st.floats(0, 1000, allow_nan=False, allow_infinity=False)),
            min_rating=st.one_of(st.none(), st.floats(1, 5, allow_nan=False, allow_infinity=False)),
        )
        @settings(deadline=None, max_examples=50)
        def _check(query, category, min_price, max_price, min_rating):
            if min_price is not None and max_price is not None and min_price > max_price:
                min_price, max_price = max_price, min_price
            result = search(
                query=query, category=category,
                min_price=min_price, max_price=max_price,
                min_rating=min_rating, limit=50,
            )
            for item in result["items"]:
                if category:
                    assert item["category"] == category
                if min_rating is not None and "rating" in item and item["rating"] is not None:
                    assert item["rating"] >= min_rating
                if min_price is not None and "price" in item and item["price"] is not None:
                    assert item["price"] >= min_price
                if max_price is not None and "price" in item and item["price"] is not None:
                    assert item["price"] <= max_price

        _check()


class TestLatencyAndStress:

    def test_tc15_search_completes_under_15s(self):
        start = time.time()
        _items(search_items_fn("book"))
        elapsed = time.time() - start
        assert elapsed < 15, f"search took {elapsed:.2f}s (limit 15s)"

    def test_tc16_load_products_completes_under_15s(self):
        start = time.time()
        products = load_products()
        elapsed = time.time() - start
        assert elapsed < 15, f"load_products took {elapsed:.2f}s (limit 15s)"
        assert len(products) > 1000

    def test_tc17_broad_tag_filter_completes_under_15s(self):
        start = time.time()
        json.loads(filter_by_tag_fn("sci-fi"))
        elapsed = time.time() - start
        assert elapsed < 15, f"filter_by_tag took {elapsed:.2f}s (limit 15s)"


class TestInvalidInput:

    def test_tc18_get_item_negative_id(self):
        result = get_item_details_fn(-1)
        assert "No item found" in result

    def test_tc19_get_item_zero_id(self):
        result = get_item_details_fn(0)
        assert "No item found" in result

    def test_tc20_search_empty_string(self):
        result = _items(search_items_fn(""))
        assert len(result) <= 20
        assert len(result) > 0

    def test_tc21_search_special_chars_and_injection(self):
        result = json.loads(search_items_fn("'; DROP TABLE products; --"))
        assert result == {"items": [], "total": 0, "offset": 0}

    def test_tc22_filter_by_tag_empty_string(self):
        result = json.loads(filter_by_tag_fn(""))
        assert result == []


class TestSessionAndGuardrails:

    def test_tc23_session_preserves_seen_ids(self):
        session = InMemorySession("sess-23")
        session.mark_seen([10, 20])
        session.mark_seen([30, 40])
        assert session.seen_ids == {10, 20, 30, 40}

    @pytest.mark.asyncio
    async def test_tc24_guardrail_blocks_empty_output(self):
        ctx = make_ctx()
        agent = MagicMock()
        result = await response_quality_guardrail.guardrail_function(ctx, agent, "")
        assert result.tripwire_triggered is True

    @pytest.mark.asyncio
    async def test_tc25_guardrail_handles_list_input(self):
        ctx = make_ctx()
        agent = MagicMock()
        list_input = [{"role": "user", "content": "recommend a laptop"}]
        result = await off_topic_guardrail.guardrail_function(ctx, agent, list_input)
        assert result.tripwire_triggered is False

    def test_tc26_get_or_create_returns_same_session(self):
        drop_session("shared-goc")
        s1 = get_or_create_session("shared-goc")
        s2 = get_or_create_session("shared-goc")
        assert s1 is s2
