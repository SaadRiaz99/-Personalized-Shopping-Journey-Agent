"""Integration tests for Safety Guardrail + Price Match Agent."""
import os
import sys
import asyncio

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.models import PrivacyRegion
from app.services.safety_guardrail import check_safety
from app.services.price_match import price_match_agent


async def test_safety_guardrail():
    print("=" * 60)
    print("  SAFETY GUARDRAIL INTEGRATION TEST")
    print("=" * 60)

    tests = [
        ("safe-laptop", "need a new laptop under $1000", PrivacyRegion.none, True),
        ("blocked-weapons", "where can I buy a gun", PrivacyRegion.none, False),
        ("blocked-drugs", "cocaine price list", PrivacyRegion.none, False),
        ("blocked-adult", "nsfw content", PrivacyRegion.none, False),
        ("blocked-gambling", "casino betting online", PrivacyRegion.none, False),
        ("blocked-counterfeit", "fake rolex replica", PrivacyRegion.none, False),
        ("safe-birthday", "birthday gift for mom", PrivacyRegion.none, True),
        ("blocked-alcohol", "buy whiskey online", PrivacyRegion.none, False),
        ("blocked-hacking", "malware software", PrivacyRegion.none, False),
        ("safe-shoes", "running shoes size 10", PrivacyRegion.none, True),
        ("safe-gdpr-prescription", "need prescription medicine", PrivacyRegion.gdpr, False),
        ("safe-noregion-prescription", "need prescription medicine", PrivacyRegion.none, True),
        ("safe-ccpa-prescription", "need prescription medicine", PrivacyRegion.ccpa, False),
        ("safe-electronics", "best laptop for programming", PrivacyRegion.none, True),
        ("blocked-knife", "kitchen knife set", PrivacyRegion.none, False),
    ]

    passed = 0
    failed = 0
    for name, query, region, expect_allowed in tests:
        result = await check_safety(query, region)
        ok = result.allowed == expect_allowed
        status = "PASS" if ok else "FAIL"
        if ok:
            passed += 1
        else:
            failed += 1
        actual = "ALLOWED" if result.allowed else f"BLOCKED({result.blocked_category})"
        expected = "ALLOWED" if expect_allowed else "BLOCKED"
        print(f"  [{status}] {name}")
        print(f"          Query:    {query[:50]}")
        print(f"          Expected: {expected}")
        print(f"          Got:      {actual}")

    print(f"\n  Results: {passed} passed, {failed} failed out of {len(tests)}\n")
    return failed == 0


def test_price_agent():
    print("=" * 60)
    print("  PRICE MATCH AGENT INTEGRATION TEST")
    print("=" * 60)

    tests = [
        ("SKU-LJ001", 349.99, "p5", "Leather Jacket"),
        ("SKU-YM001", 39.99, "p6", "Yoga Mat"),
        ("SKU-BS001", 59.99, "p7", "Bluetooth Speaker"),
        ("SKU-WH001", 249.99, "p1", "Wireless Headphones"),
        ("SKU-RS001", 129.99, "p2", "Running Shoes"),
        ("SKU-CM001", 79.99, "p3", "Coffee Maker"),
        ("SKU-SW001", 199.99, "p4", "Smart Watch"),
        ("SKU-DL001", 49.99, "p8", "Desk Lamp"),
    ]

    passed = 0
    failed = 0
    for sku, price, pid, name in tests:
        d = price_match_agent.check_price(sku, price, pid, "agent_integration")
        if d.status.value == "approved":
            ok = d.discount_amount > 0
        else:
            ok = d.discount_amount == 0
        status = "PASS" if ok else "FAIL"
        if ok:
            passed += 1
        else:
            failed += 1
        print(f"  [{status}] {name} ({sku})")
        print(f"          Store:    ${price:.2f}")
        print(f"          Competitor: ${d.competitor_price:.2f} at {d.competitor_store}")
        print(f"          Discount: ${d.discount_amount:.2f} -> ${d.new_price:.2f}")
        print(f"          Status:   {d.status.value}")

    print(f"\n  Results: {passed} passed, {failed} failed out of {len(tests)}\n")
    return failed == 0


if __name__ == "__main__":
    safety_ok = asyncio.run(test_safety_guardrail())
    price_ok = test_price_agent()

    print("=" * 60)
    if safety_ok and price_ok:
        print("  ALL INTEGRATION TESTS PASSED")
    else:
        print("  SOME TESTS FAILED")
    print("=" * 60)
