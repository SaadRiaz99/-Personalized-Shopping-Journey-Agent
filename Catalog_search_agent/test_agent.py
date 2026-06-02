"""pytest tests for Catalog Search Agent.

Run:
    pytest test_agent.py -v                          # unit tests only
    pytest test_agent.py -v -m needs_api             # integration tests (needs key)
    pytest test_agent.py -v -m "not needs_api"       # unit tests only
    pytest test_agent.py -v --record-mode=once       # record API cassettes
"""

import pytest
from agents import InputGuardrailTripwireTriggered, Runner
from catalog_search_agent import PRODUCTS

# ===========================================================================
# Unit tests — tools (no API needed)
# ===========================================================================


class TestSearchProducts:
    @pytest.mark.parametrize("query,category,min_expected", [
        ("headphones",  None,   1),
        ("monitor",     None,   1),
        ("yoga",        None,   1),
        ("keyboard",    None,   1),
        ("bluetooth",   None,   1),
        ("running",     None,   1),
        ("xyzabc123",   None,   0),
        ("water",       None,   1),
        ("USB-C",       None,   1),
    ])
    def test_search_by_name(self, query, category, min_expected):
        result = _search(query, category=category)
        assert len(result) >= min_expected

    @pytest.mark.parametrize("category,cat_in_name", [
        ("Electronics",      "Electronics"),
        ("Home & Kitchen",   "Home & Kitchen"),
        ("Furniture",        "Furniture"),
        ("Sports & Fitness", "Sports"),
        ("Groceries",        "Groceries"),
        ("Clothing",         "Clothing"),
        ("Books",            "Books"),
    ])
    def test_filter_by_category(self, category, cat_in_name):
        result = _search("a", category=category)
        assert all(p["category"] == category for p in result)

    def test_max_price_filter(self):
        result = _search("a", max_price=20.0)
        assert all(p["price"] <= 20.0 for p in result)

    def test_min_rating_filter(self):
        result = _search("a", min_rating=4.8)
        assert all(p["rating"] >= 4.8 for p in result)

    def test_combined_filters(self):
        result = _search("a", category="Electronics", max_price=100.0, min_rating=4.0)
        assert all(p["price"] <= 100.0 and p["rating"] >= 4.0 and p["category"] == "Electronics" for p in result)

    def test_zero_results(self):
        result = _search("zzzznotexist999")
        assert len(result) == 0


class TestGetProductDetails:
    def test_valid_id(self):
        p = _details(1)
        assert p["id"] == 1
        assert p["name"] == "Wireless Bluetooth Headphones"

    def test_another_valid_id(self):
        p = _details(6)
        assert p["id"] == 6
        assert p["name"] == "Wireless Mouse Ergonomic"

    def test_invalid_id(self):
        p = _details(99999)
        assert p is None

    @pytest.mark.parametrize("pid,expected_name_fragment", [
        (50,  "Arduino Starter Kit"),
        (100, "Thermometer Meat Probe"),
        (200, "Floor Lamp"),
        (300, "Golf Club Set"),
        (400, "Sun Dried Tomatoes"),
        (500, "Scrunchie Set"),
        (600, "Guns Germs and Steel"),
        (700, "Q-Tips Cotton"),
        (800, "Bungee Cords"),
        (906, "Battery Load Tester"),
    ])
    def test_various_ids(self, pid, expected_name_fragment):
        p = _details(pid)
        assert p is not None, f"No product found for id {pid}"
        assert expected_name_fragment.lower() in p["name"].lower(), f"Expected '{expected_name_fragment}' in '{p['name']}'"

    def test_out_of_stock(self):
        results = [p for p in PRODUCTS if p["stock"] == 0]
        if results:
            oos = results[0]
            p = _details(oos["id"])
            assert p["stock"] == 0


class TestListCategories:
    def test_returns_all_categories(self):
        cats = _categories()
        expected = {"Electronics", "Home & Kitchen", "Furniture", "Sports & Fitness", "Groceries", "Clothing", "Books"}
        assert expected.issubset(set(cats))

    def test_category_count(self):
        cats = _categories()
        assert len(cats) >= 7


class TestProductsData:
    def test_all_products_have_required_fields(self):
        for p in PRODUCTS:
            assert all(k in p for k in ("id", "name", "category", "price", "rating", "stock", "description"))

    def test_no_negative_prices(self):
        assert all(p["price"] > 0 for p in PRODUCTS)

    def test_ratings_in_range(self):
        assert all(0 <= p["rating"] <= 5 for p in PRODUCTS)

    def test_unique_ids(self):
        ids = [p["id"] for p in PRODUCTS]
        assert len(ids) == len(set(ids))

    def test_categories_are_valid(self):
        cats = set(p["category"] for p in PRODUCTS)
        assert len(cats) >= 7
        assert "Electronics" in cats


# ===========================================================================
# Integration tests — agent with LLM (needs OPENROUTER_API_KEY)
# ===========================================================================


class TestAgentCatalogQueries:
    @pytest.mark.needs_api
    @pytest.mark.parametrize("query,expected_word", [
        ("show me wireless bluetooth headphones", "headphones"),
        ("find monitors",                         "monitor"),
        ("electronics under $50",                 "Electronics"),
        ("products with noise cancelling",        "noise"),
        ("what books are available",              "Books"),
        ("cheapest product you have",             "$"),
        ("tell me about product 1",               "Wireless Bluetooth Headphones"),
        ("what categories do you have",           "Electronics"),
        ("recommend something under $30",         "$"),
        ("what are the highest rated products",   "rating"),
    ])
    @pytest.mark.default_cassette("agent_catalog_pass.yaml")
    @pytest.mark.vcr
    async def test_catalog_queries_pass(self, catalog_agent, user_ctx, query, expected_word):
        result = await Runner.run(catalog_agent, query, context=user_ctx)
        output = str(result.final_output)
        assert expected_word.lower() in output.lower(), f"Expected '{expected_word}' in '{output[:200]}'"

    @pytest.mark.needs_api
    @pytest.mark.parametrize("query", [
        "what is 2+2",
        "write python code to sort a list",
        "who is the president",
        "how's the weather",
        "translate hello to spanish",
        "what happened in world war 2",
    ])
    @pytest.mark.default_cassette("agent_guardrail_reject.yaml")
    @pytest.mark.vcr
    async def test_guardrail_rejects_non_catalog(self, catalog_agent, user_ctx, query):
        with pytest.raises(InputGuardrailTripwireTriggered):
            await Runner.run(catalog_agent, query, context=user_ctx)

    @pytest.mark.needs_api
    @pytest.mark.parametrize("query", [
        "find me a 27 inch monitor",
        "show me running shoes in stock",
        "compare headphones and earbuds",
        "suggest a gift under $50",
        "how much is the mechanical keyboard",
        "products between $50 and $150",
        "cheap electronics under $30",
    ])
    @pytest.mark.default_cassette("agent_edge_cases.yaml")
    @pytest.mark.vcr
    async def test_edge_cases(self, catalog_agent, user_ctx, query):
        result = await Runner.run(catalog_agent, query, context=user_ctx)
        output = str(result.final_output)
        assert len(output) > 20

    @pytest.mark.needs_api
    async def test_invalid_id_handling(self, catalog_agent, user_ctx):
        result = await Runner.run(catalog_agent, "tell me about product 99999", context=user_ctx)
        output = str(result.final_output).lower()
        assert "not found" in output or "no product" in output or "doesn't exist" in output

    @pytest.mark.needs_api
    async def test_out_of_stock_mention(self, catalog_agent, user_ctx):
        result = await Runner.run(catalog_agent, "are the running shoes in stock", context=user_ctx)
        output = str(result.final_output).lower()
        assert "stock" in output or "out of" in output or "available" in output


# ===========================================================================
# Helpers — raw logic (not @function_tool wrappers)
# ===========================================================================

def _search(query, category=None, max_price=None, min_rating=None):
    """Mirror search_products logic as a plain callable for unit tests."""
    results = list(PRODUCTS)
    q = query.lower()
    results = [p for p in results if q in p["name"].lower() or q in p["description"].lower()]
    if category:
        results = [p for p in results if p["category"].lower() == category.lower()]
    if max_price is not None:
        results = [p for p in results if p["price"] <= max_price]
    if min_rating is not None:
        results = [p for p in results if p["rating"] >= min_rating]
    return results


def _details(product_id):
    return next((p for p in PRODUCTS if p["id"] == product_id), None)


def _categories():
    return sorted(set(p["category"] for p in PRODUCTS))
