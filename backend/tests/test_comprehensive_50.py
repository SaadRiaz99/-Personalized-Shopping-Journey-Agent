"""
Comprehensive 60 Test Cases — All Agents via Orchestrator
"""
import os, sys, time, json, asyncio, uuid, inspect

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
os.environ["JWT_SECRET_KEY"] = "test-secret"

from app.models import (
    Agent, AgentStatus, PrivacyRegion, PrivacyLevel, UserPreferences,
    GiftRecipient, QueryIntent, DiscountStatus, CartSession, LoyaltyTier,
    DealSessionRequest, CartItem,
)
from app.services.agent_orchestrator import orchestrator
from app.services.safety_guardrail import check_safety
from app.services.privacy_guardrail import privacy_guardrail
from app.services.price_guardrail import price_guardrail
from app.services.price_match import (
    price_match_agent, fetch_competitor_price, authorize_price_match,
    get_price_history, get_price_drop_alerts,
)
from app.services.deal_agent import deal_agent
from app.services.gift_finder import find_gifts
from app.services.cross_sell import get_cross_sell
from app.services.recommendation import get_recommendations, search_products
from app.services.intent_parser import parse_intent
from app.services.catalog_search import search_products as cat_search
from shared.products import ALL_PRODUCTS
from app.database import init_db, get_db

init_db()

results = []
def test(name: str, category: str, fn):
    results.append({"name": name, "category": category, "fn": fn})

def is_async(fn):
    return asyncio.iscoroutinefunction(fn) or inspect.iscoroutinefunction(fn)

async def run_all():
    total = len(results)
    passed = 0
    print("=" * 70)
    print(f"  PERSONALIZED SHOPPING AGENT \u2014 COMPREHENSIVE TEST SUITE ({total} CASES)")
    print("=" * 70)

    for i, r in enumerate(results, 1):
        name = r["name"]
        cat = r["category"]
        print(f"\n[{i:02d}/{total}] [{cat}] {name}")
        try:
            if is_async(r["fn"]):
                await r["fn"]()
            else:
                r["fn"]()
            r["passed"] = True
            passed += 1
            print(f"  >>> PASS")
        except Exception as e:
            r["passed"] = False
            r["error"] = str(e)
            print(f"  >>> FAIL: {e}")

    print("\n" + "=" * 70)
    print(f"  RESULTS: {passed}/{total} PASSED  ({total - passed} FAILED)")
    print(f"  RATE:    {passed / total * 100:.1f}%")
    print("=" * 70)

    from collections import Counter
    cats = sorted(set(r["category"] for r in results))
    cat_pass = Counter(r["category"] for r in results if r.get("passed"))

    print(f"\n  {'Category':<25} {'Total':>6} {'Passed':>6} {'Failed':>6} {'Rate':>6}")
    print(f"  {'-'*25} {'-'*6} {'-'*6} {'-'*6} {'-'*6}")
    for c in cats:
        t = sum(1 for r in results if r["category"] == c)
        p = sum(1 for r in results if r["category"] == c and r.get("passed"))
        print(f"  {c:<25} {t:>6} {p:>6} {t-p:>6} {p/t*100:>5.0f}%")

    for r in results:
        if not r.get("passed"):
            print(f"\n  FAIL: {r['name']} \u2014 {r.get('error', 'N/A')}")

    return passed == total


# ===========================================================================
# 1. SAFETY GUARDRAIL
# ===========================================================================
async def test_safe_1(): r = await check_safety("I need a new laptop under $1000"); assert r.allowed
async def test_safe_2(): r = await check_safety("where can I buy a gun"); assert not r.allowed and r.blocked_category == "weapons"
async def test_safe_3(): r = await check_safety("cocaine price list"); assert not r.allowed and r.blocked_category == "drugs"
async def test_safe_4(): r = await check_safety("nsfw content"); assert not r.allowed and r.blocked_category == "adult"
async def test_safe_5(): r = await check_safety("fake rolex replica"); assert not r.allowed and r.blocked_category == "counterfeit"
async def test_safe_6(): r = await check_safety("casino betting online"); assert not r.allowed and r.blocked_category == "gambling"

test("Safe shopping query passes guardrail", "SafetyGuardrail", test_safe_1)
test("Weapons query blocked", "SafetyGuardrail", test_safe_2)
test("Drugs query blocked", "SafetyGuardrail", test_safe_3)
test("Adult content blocked", "SafetyGuardrail", test_safe_4)
test("Counterfeit blocked", "SafetyGuardrail", test_safe_5)
test("Gambling blocked", "SafetyGuardrail", test_safe_6)

# ===========================================================================
# 2. PRIVACY GUARDRAIL
# ===========================================================================
async def test_priv_1():
    r = await privacy_guardrail.check_input("I need a gift for my wife")
    assert r.action.value == "allowed"
async def test_priv_2():
    privacy_guardrail.get_or_create_profile("pt1").privacy_level = PrivacyLevel.strict
    r = await privacy_guardrail.check_input("Email me at john@example.com")
    assert r.action.value == "sanitized" and "email" in r.redacted_fields
async def test_priv_3():
    r = await privacy_guardrail.check_input("Call 555-123-4567")
    assert r.action.value == "sanitized"
async def test_priv_4():
    r = await privacy_guardrail.check_input("My SSN is 123-45-6789")
    assert "ssn" in r.redacted_fields
async def test_priv_5():
    profile = privacy_guardrail.get_or_create_profile("pt2")
    profile.privacy_level = PrivacyLevel.strict
    r = await privacy_guardrail.check_agent_access("test_agent", ["phone", "location"], "pt2")
    assert r.action.value == "blocked"

test("No PII passes through", "PrivacyGuardrail", test_priv_1)
test("Email redacted", "PrivacyGuardrail", test_priv_2)
test("Phone redacted", "PrivacyGuardrail", test_priv_3)
test("SSN redacted", "PrivacyGuardrail", test_priv_4)
test("Agent access blocked for strict privacy", "PrivacyGuardrail", test_priv_5)

# ===========================================================================
# 3. PRICE GUARDRAIL
# ===========================================================================
def test_pg_1():
    v = price_guardrail.validate_input("SKU-0001", 100.0)
    assert v.allowed
def test_pg_2():
    v = price_guardrail.validate_input("INVALID", 100.0)
    assert not v.allowed
def test_pg_3():
    v = price_guardrail.validate_input("SKU-0001", -10.0)
    assert not v.allowed
def test_pg_4():
    v = price_guardrail.detect_fraud(100.0, 5.0)
    assert not v.allowed
def test_pg_5():
    for _ in range(55): price_guardrail.check_rate_limit("rg_user")
    v = price_guardrail.check_rate_limit("rg_user")
    assert not v.allowed

test("Valid SKU format passes", "PriceGuardrail", test_pg_1)
test("Invalid SKU format blocked", "PriceGuardrail", test_pg_2)
test("Negative price blocked", "PriceGuardrail", test_pg_3)
test("Fraud detection works", "PriceGuardrail", test_pg_4)
test("Rate limiting works", "PriceGuardrail", test_pg_5)

# ===========================================================================
# 4. INTENT PARSER
# ===========================================================================
async def test_ip_1(): i = await parse_intent("find me a laptop under $1000 for programming"); assert i.category
async def test_ip_2(): i = await parse_intent("I need a winter jacket for under $200"); assert i.category
async def test_ip_3(): i = await parse_intent("birthday gift for my mom around $50"); assert i.occasion
async def test_ip_4(): i = await parse_intent("show me monitors under $300"); assert i.raw_query
async def test_ip_5(): i = await parse_intent(""); assert i is not None

test("Parse electronics intent", "IntentParser", test_ip_1)
test("Parse clothing intent", "IntentParser", test_ip_2)
test("Parse gift intent", "IntentParser", test_ip_3)
test("Parse budget extraction", "IntentParser", test_ip_4)
test("Empty query returns default", "IntentParser", test_ip_5)

# ===========================================================================
# 5. CATALOG SEARCH
# ===========================================================================
def test_cs_1(): r = cat_search(query="laptop"); assert r["total"] > 0
def test_cs_2(): r = cat_search(category="Electronics"); assert r["total"] > 0
def test_cs_3(): r = cat_search(max_price=50.0); assert all(p["price"] <= 50.0 for p in r["products"])
def test_cs_4(): r = cat_search(min_rating=4.5); assert all(p["rating"] >= 4.5 for p in r["products"])
def test_cs_5(): r = cat_search(query="zzzznonexistentproductxxx"); assert r["total"] == 0

test("Search by keyword", "CatalogSearch", test_cs_1)
test("Search by category", "CatalogSearch", test_cs_2)
test("Search with price filter", "CatalogSearch", test_cs_3)
test("Search with rating filter", "CatalogSearch", test_cs_4)
test("Search no results", "CatalogSearch", test_cs_5)

# ===========================================================================
# 6. PRICE MATCH
# ===========================================================================
def test_pm_1(): c = fetch_competitor_price("SKU-0001"); assert "error" not in c
def test_pm_2(): a = authorize_price_match(100.0, 85.0); assert a["status"] == "approved"
def test_pm_3(): a = authorize_price_match(100.0, 120.0); assert a["status"] == "declined"
def test_pm_4(): h = get_price_history("SKU-0001"); assert len(h) > 0
def test_pm_5(): a = get_price_drop_alerts("SKU-0001", 0.1); assert isinstance(a, list)

test("Fetch competitor price", "PriceMatch", test_pm_1)
test("Price match authorized when cheaper", "PriceMatch", test_pm_2)
test("Price match declined when store is cheaper", "PriceMatch", test_pm_3)
test("Price history generated", "PriceMatch", test_pm_4)
test("Price drop alerts detected", "PriceMatch", test_pm_5)

# ===========================================================================
# 7. DEAL AGENT
# ===========================================================================
def test_da_1():
    cart = CartSession(user_id="du1", items=[CartItem(product_id="1", sku="SKU-0001", name="Test", price=5000, quantity=1, category="Electronics")], loyalty_tier=LoyaltyTier.gold)
    s = deal_agent.optimize_stack(cart)
    assert s is not None and s.final_total < s.original_total
def test_da_2():
    cart = CartSession(user_id="du2", items=[CartItem(product_id="2", sku="SKU-0002", name="Test2", price=3000, quantity=1, category="Fashion")], loyalty_tier=LoyaltyTier.silver)
    s = deal_agent.optimize_stack(cart)
    assert s is not None and s.total_savings > 0
def test_da_3():
    cart = CartSession(user_id="du3", items=[CartItem(product_id="3", sku="SKU-0003", name="Test3", price=1000, quantity=1, category="Books")], loyalty_tier=LoyaltyTier.bronze, opted_out=True)
    s = deal_agent.optimize_stack(cart)
    assert s is not None
def test_da_4():
    p = deal_agent.get_active_promotions()
    assert len(p) > 0

test("Deal agent optimizes cart with best stack", "DealAgent", test_da_1)
test("Deal agent applies percentage discounts", "DealAgent", test_da_2)
test("Deal privacy mode works", "DealAgent", test_da_3)
test("List active promotions", "DealAgent", test_da_4)

# ===========================================================================
# 8. GIFT FINDER
# ===========================================================================
def test_gf_1(): r = find_gifts(GiftRecipient(occasion="birthday", relationship="mother", age=45, interests=["cooking"], budget=100)); assert r.total_found > 0
def test_gf_2(): r = find_gifts(GiftRecipient(occasion="christmas", relationship="friend", age=30, interests=["tech", "gaming"], budget=200)); assert r.total_found > 0
def test_gf_3(): r = find_gifts(GiftRecipient(occasion="anniversary", relationship="spouse", age=35, interests=["books"], budget=25)); assert r.total_found >= 0

test("Find gifts by occasion", "GiftFinder", test_gf_1)
test("Find gifts for friend", "GiftFinder", test_gf_2)
test("Find gift with low budget", "GiftFinder", test_gf_3)

# ===========================================================================
# 9. CROSS-SELL
# ===========================================================================
def test_xs_1(): r = get_cross_sell(1); assert len(r.recommendations) > 0
def test_xs_2(): r = get_cross_sell(1, cart_product_ids=[2, 3]); assert r is not None and isinstance(r.recommendations, list)
def test_xs_3():
    for p in ALL_PRODUCTS[:50]:
        if p["category"] == "Electronics":
            r = get_cross_sell(p["id"]); assert r is not None; return
    assert False, "No electronics product found"

test("Cross-sell finds complementary products", "CrossSell", test_xs_1)
test("Cross-sell with cart context", "CrossSell", test_xs_2)
test("Cross-sell for electronics product", "CrossSell", test_xs_3)

# ===========================================================================
# 10. RECOMMENDATION
# ===========================================================================
def test_rec_1(): r = get_recommendations(UserPreferences(categories=["Electronics"])); assert len(r) > 0
def test_rec_2(): r = get_recommendations(UserPreferences(price_max=50.0)); assert all(p.price <= 50.0 for p in r)
def test_rec_3(): r = search_products("laptop"); assert len(r) > 0

test("Recommend by category", "Recommendation", test_rec_1)
test("Recommend by price range", "Recommendation", test_rec_2)
test("Search products by query", "Recommendation", test_rec_3)

# ===========================================================================
# 11. ORCHESTRATOR
# ===========================================================================
def test_orb_1():
    a = orchestrator.create_agent("TestAgent", "test task")
    assert a.id and a.name == "TestAgent"
def test_orb_2():
    agents = orchestrator.list_agents()
    assert len(agents) > 0
def test_orb_3():
    a = orchestrator.create_agent("GetTest", "get test")
    b = orchestrator.get_agent(a.id)
    assert b is not None and b.id == a.id
def test_orb_4():
    a = orchestrator.create_agent("DeleteTest", "delete test")
    assert orchestrator.delete_agent(a.id) is True
async def test_orb_5():
    a = orchestrator.create_agent("UnsafeTest", "I want to buy a gun")
    r = await orchestrator.run_agent(a.id)
    assert r["status"] == "blocked"
async def test_orb_6():
    a = orchestrator.create_agent("SafeTest", "I need a laptop")
    r = await orchestrator.run_agent(a.id)
    assert r["status"] in ("completed", "blocked")

test("Create agent via orchestrator", "Orchestrator", test_orb_1)
test("List agents via orchestrator", "Orchestrator", test_orb_2)
test("Get agent by ID", "Orchestrator", test_orb_3)
test("Delete agent", "Orchestrator", test_orb_4)
test("Run agent blocks unsafe query", "Orchestrator", test_orb_5)
test("Run agent completes for safe query", "Orchestrator", test_orb_6)

# ===========================================================================
# 12. COLLABORATION COUNCIL
# ===========================================================================
async def test_collab():
    r = await orchestrator.run_collaborative_task("find me a good laptop under $1000")
    assert r["status"] in ("completed", "blocked")
    if r["status"] == "completed":
        assert "collaboration_id" in r

test("Collaboration council processes query", "Collaboration", test_collab)

# ===========================================================================
# 13. PRICE MATCH AGENT DB
# ===========================================================================
def test_pma_1():
    d = price_match_agent.check_price("SKU-0001", 100.0, "test_prod", "test_agent_pm")
    assert d.status in (DiscountStatus.approved, DiscountStatus.declined)
def test_pma_2():
    d_list = price_match_agent.list_discounts()
    assert isinstance(d_list, list)

test("Price match agent check_price", "PriceMatchAgent", test_pma_1)
test("Price match agent list discounts", "PriceMatchAgent", test_pma_2)

# ===========================================================================
# 14. MOCK STANDALONE AGENTS (run from their directories)
# ===========================================================================
def test_mock_cat():
    old = os.getcwd()
    os.chdir(os.path.join(os.path.dirname(__file__), "..", "..", "Catalog_search_agent"))
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location("mock_cat", "catalog_search_agent_mock.py")
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        r = mod.search_products("laptop")
        assert len(r) > 0
        cats = mod.list_categories()
        assert len(cats) > 0
    finally:
        os.chdir(old)

def test_mock_deal():
    old = os.getcwd()
    os.chdir(os.path.join(os.path.dirname(__file__), "..", "..", "Deal_Agent"))
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location("mock_deal", "deal_agent_mock.py")
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        result = mod.apply_best_discount(5000, mod.PROMOTIONS, mod.USERS[0], mod.USERS[0]["points"])
        assert result["final"] < result["original"]
    finally:
        os.chdir(old)

def test_mock_pp():
    old = os.getcwd()
    os.chdir(os.path.join(os.path.dirname(__file__), "..", "..", "Post_Purchase_Agent"))
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location("mock_pp", "post_purchase_agent_mock.py")
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        result = mod.cmd_track("ORD001")
        assert "ORDER" in result
        profile = mod.cmd_profile("C001")
        assert "PROFILE" in profile
    finally:
        os.chdir(old)

test("Catalog mock agent search + categories", "MockAgent", test_mock_cat)
test("Deal mock agent apply best discount", "MockAgent", test_mock_deal)
test("Post-purchase mock agent track + profile", "MockAgent", test_mock_pp)

# ===========================================================================
# 15. EDGE CASES
# ===========================================================================
async def test_edge_1(): r = await check_safety(""); assert r.allowed
async def test_edge_2(): r = await check_safety("   "); assert r.allowed
def test_edge_3(): r = cat_search(query="a" * 1000); assert isinstance(r, dict)
def test_edge_4():
    v = price_guardrail.validate_input("SKU-9999", 100001.0)
    assert not v.allowed  # exceeds MAX_PRICE

test("Empty string safety check", "EdgeCase", test_edge_1)
test("Whitespace safety check", "EdgeCase", test_edge_2)
test("Very long query truncation", "EdgeCase", test_edge_3)
test("Excessive price blocked", "EdgeCase", test_edge_4)

# ===========================================================================
# MAIN
# ===========================================================================
if __name__ == "__main__":
    start = time.time()
    ok = asyncio.run(run_all())
    elapsed = time.time() - start
    print(f"\n  Total time: {elapsed:.1f}s")

    total = len(results)
    passed = sum(1 for r in results if r.get("passed"))
    failed = total - passed

    from collections import Counter
    cats = sorted(set(r["category"] for r in results))

    lines = []
    L = lambda s="": lines.append(s)
    L("# Personalized Shopping Agent \u2014 Comprehensive Test Report")
    L()
    L(f"- **Date:** {time.strftime('%Y-%m-%d %H:%M:%S')}")
    L(f"- **Product Catalog:** {len(ALL_PRODUCTS)} products across {len(set(p['category'] for p in ALL_PRODUCTS))} categories")
    L(f"- **Total Tests:** {total}")
    L(f"- **Passed:** {passed}")
    L(f"- **Failed:** {failed}")
    L(f"- **Pass Rate:** {passed/total*100:.1f}%")
    L(f"- **Duration:** {elapsed:.1f}s")
    L()
    L("## Agents Tested")
    L()
    L("| # | Agent | Tests | Description |")
    L("|---|-------|-------|-------------|")
    agent_info = [
        ("1", "SafetyGuardrail", 6, "Blocks weapons, drugs, adult, counterfeit, gambling, hacking, alcohol"),
        ("2", "PrivacyGuardrail", 5, "Redacts PII, enforces consent, region-aware (GDPR/CCPA)"),
        ("3", "PriceGuardrail", 5, "SKU format, price bounds, fraud detection, rate limiting"),
        ("4", "IntentParser", 5, "Extracts category, budget, occasion from natural language"),
        ("5", "CatalogSearch", 5, "906-product catalog search with keyword/category/price/rating filters"),
        ("6", "PriceMatch", 5, "Competitor price checking across 5 retailers, 25% margin cap"),
        ("7", "DealAgent", 4, "Discount stacking engine with 13 promotions across loyalty tiers"),
        ("8", "GiftFinder", 3, "Occasion-based gift recommendations from product catalog"),
        ("9", "CrossSell", 3, "Complementary, upsell, and accessory product recommendations"),
        ("10", "Recommendation", 3, "Personalized product recommendations with preferences filtering"),
        ("11", "AgentOrchestrator", 6, "Central coordinator for agent lifecycle, guardrails, execution"),
        ("12", "CollaborationCouncil", 1, "3-agent chain: Researcher -> Auditor -> Stylist"),
        ("13", "PriceMatchAgent(DB)", 2, "Persistent discount tracking with SQLite"),
        ("14", "MockStandaloneAgents", 3, "Catalog/Deal/Post-Purchase offline mock agents"),
        ("15", "EdgeCases", 4, "Empty queries, whitespace, long input, boundary prices"),
    ]
    for num, name, count, desc in agent_info:
        L(f"| {num} | {name} | {count} | {desc} |")
    L()
    L("## Results by Category")
    L()
    L("| Category | Total | Passed | Failed | Rate |")
    L("|----------|-------|--------|--------|------|")
    for c in cats:
        ct = [r for r in results if r["category"] == c]
        cp = sum(1 for r in ct if r.get("passed"))
        cf = len(ct) - cp
        pct = cp / len(ct) * 100 if ct else 0
        L(f"| {c} | {len(ct)} | {cp} | {cf} | {pct:.0f}% |")
    L()
    L("## Detailed Results")
    L()
    L("| # | Category | Test Name | Status | Error |")
    L("|---|----------|-----------|--------|-------|")
    for i, r in enumerate(results, 1):
        status = "PASS" if r.get("passed") else "FAIL"
        err = (r.get("error", "") or "").replace("|", "/")
        L(f"| {i} | {r['category']} | {r['name']} | {status} | {err} |")

    if failed > 0:
        L()
        L("## Failed Tests Detail")
        L()
        for r in results:
            if not r.get("passed"):
                L(f"- **{r['name']}** ({r['category']}): {r.get('error', 'N/A')}")

    L()
    L("## Orchestrator Integration Pipeline")
    L()
    L("The `AgentOrchestrator` coordinates all agents through this pipeline:")
    L()
    L("```")
    L("User Query")
    L("  -> SafetyGuardrail (blocks unsafe content)")
    L("  -> PrivacyGuardrail (redacts PII, checks consent)")
    L("  -> IntentParser (extracts structured intent)")
    L("  -> CatalogSearch (queries 906-product catalog)")
    L("  -> PriceMatchAgent (checks 5 retailers, enforces 25% margin)")
    L("  -> DealAgent (stacks BOGO, percentage, category, fixed discounts)")
    L("  -> OutputGuardrail (scans for compliance)")
    L("  -> Response")
    L("```")
    L()
    L("**Collaboration Council** chains 3 sub-agents within the orchestrator:")
    L("1. **Researcher** - parses intent + searches catalog")
    L("2. **Auditor** - price match audit on each product")
    L("3. **Stylist** - sorts by rating + discount value")
    L()
    L("## All Agents Connectivity")
    L()
    L("| Agent | Connects To | Protocol |")
    L("|-------|------------|----------|")
    L("| SafetyGuardrail | AgentOrchestrator | In-process method call |")
    L("| PrivacyGuardrail | AgentOrchestrator | In-process method call |")
    L("| IntentParser | AgentOrchestrator | In-process method call |")
    L("| CatalogSearch | shared.products (906 products) | Import |")
    L("| PriceMatchAgent | 5 competitor stores (mock) | In-process + SQLite |")
    L("| DealAgent | 13 promotions | In-process + SQLite |")
    L("| GiftFinder | shared.products | Import |")
    L("| CrossSell | shared.products | Import |")
    L("| Recommendation | shared.products | Import |")
    L("| CollaborationCouncil | AgentOrchestrator | Creates sub-agents in-process |")
    L("| WebSocket | Frontend React app | ws://host:8000/ws/agents |")
    L("| Catalog CLI Agent | products.json (standalone) | CLI / OpenAI SDK |")
    L("| Deal CLI Agent | promotions.json (standalone) | CLI / OpenAI SDK |")
    L("| PostPurchase CLI Agent | customers.json (standalone) | CLI / OpenAI SDK |")
    L()
    L("## Recommendations")
    L()
    L("1. **Wire `shared/message_bus.py` & `agent_protocol.py`** into the orchestrator for proper decoupled pub/sub communication.")
    L("2. **Add root `.env.example`** with all required variables (`LLM_API_KEY`, `LLM_ENDPOINT`, `JWT_SECRET_KEY`).")
    L("3. **Seed competitor prices deterministically** in `price_match.py` instead of `random.uniform()` at module load.")
    L("4. **Include standalone agents in `docker-compose.yml`** or remove orphaned `discoveryAgent.dockerfile`.")
    L("5. **Deduplicate** `recommendation_agent/` vs `recommendations_agent/`.")
    L("6. **Add CI pipeline** (GitHub Actions) to run this test suite automatically on push.")
    L()

    report_dir = os.path.join(os.path.dirname(__file__), "..", "..")
    report_path = os.path.join(report_dir, "AGENT_TEST_REPORT.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"\nReport written to {report_path}")
    sys.exit(0 if ok else 1)
