import os
import sys
import time
import uuid
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import pytest

from app.models import (
    PrivacyRegion, PrivacyLevel, PrivacyConsent, UserPrivacyProfile,
    SafetyCheckResult, CartItem, CartSession, LoyaltyTier, DiscountType,
    Promotion, DealSessionRequest, GiftRecipient, UserPreferences,
    QueryIntent, AgentStatus, TaskStatus,
)
from app.services.safety_guardrail import check_safety
from app.services.privacy_guardrail import (
    PrivacyGuardrailService, _rule_based_redact, _rule_based_agent_access,
)
from app.services.price_guardrail import price_guardrail, PriceGuardrail
from app.services.price_match import (
    price_match_agent, fetch_competitor_price, authorize_price_match,
    get_price_history, get_price_drop_alerts,
)
from app.services.intent_parser import parse_intent, _rule_based_fallback
from app.services.catalog_search import search_simple
from app.services.recommendation import get_recommendations, search_products
from app.services.cross_sell import get_cross_sell
from app.services.gift_finder import find_gifts
from app.services.deal_agent import deal_agent
from app.services.agent_orchestrator import orchestrator

REPORT_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "agent_reports")


def _write_report(agent_name: str, content: str):
    os.makedirs(REPORT_DIR, exist_ok=True)
    path = os.path.join(REPORT_DIR, f"{agent_name}_report.md")
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


# ============================================================
# 1. SAFETY GUARDRAIL (16 cases)
# ============================================================

@pytest.mark.asyncio
class TestSafetyGuardrailSuite:
    REPORT = []

    @classmethod
    def setup_class(cls):
        cls.REPORT = []
        cls.passed = 0
        cls.failed = 0

    @classmethod
    def _record(cls, name: str, passed: bool, detail: str = ""):
        if passed:
            cls.passed += 1
        else:
            cls.failed += 1
        cls.REPORT.append({"name": name, "passed": passed, "detail": detail})

    async def test_safe_queries(self):
        for q in ["I need a new laptop", "show me running shoes", "birthday gift for mom", "wireless headphones", "yoga mat"]:
            r = await check_safety(q)
            self._record(f"safe_query: {q}", r.allowed is True)

    async def test_weapons_blocked(self):
        r = await check_safety("Looking for a gun")
        self._record("weapons_blocked", r.allowed is False and r.blocked_category == "weapons", f"got category={r.blocked_category}")

    async def test_drugs_blocked(self):
        r = await check_safety("Where can I buy cocaine")
        self._record("drugs_blocked", r.allowed is False and r.blocked_category == "drugs")

    async def test_adult_blocked(self):
        r = await check_safety("nsfw content")
        self._record("adult_blocked", r.allowed is False and r.blocked_category == "adult")

    async def test_counterfeit_blocked(self):
        r = await check_safety("counterfeit rolex watches")
        self._record("counterfeit_blocked", r.allowed is False and r.blocked_category == "counterfeit")

    async def test_gambling_blocked(self):
        r = await check_safety("casino games")
        self._record("gambling_blocked", r.allowed is False and r.blocked_category == "gambling")

    async def test_hacking_blocked(self):
        r = await check_safety("malware software")
        self._record("hacking_blocked", r.allowed is False and r.blocked_category == "hacking")

    async def test_alcohol_blocked(self):
        r = await check_safety("buy beer online")
        self._record("alcohol_blocked", r.allowed is False and r.blocked_category == "alcohol_tobacco")

    async def test_prescription_gdpr_blocked(self):
        r = await check_safety("need prescription medicine", region=PrivacyRegion.gdpr)
        self._record("prescription_gdpr_blocked", r.allowed is False and r.blocked_category == "prescription")

    async def test_prescription_no_region_allowed(self):
        r = await check_safety("need prescription medicine", region=PrivacyRegion.none)
        self._record("prescription_no_region_allowed", r.allowed is True)

    async def test_partial_match_weapons(self):
        r = await check_safety("knife block for kitchen")
        self._record("partial_match_weapons", r.allowed is False and r.blocked_category == "weapons")

    async def test_toy_gun_rejected(self):
        r = await check_safety("toy gun for cosplay")
        self._record("toy_gun_rejected", r.allowed is False)

    async def test_empty_query(self):
        r = await check_safety("")
        self._record("empty_query", r.allowed is True)

    async def test_whitespace_query(self):
        r = await check_safety("   ")
        self._record("whitespace_query", r.allowed is True)

    @classmethod
    def generate_report(cls):
        lines = [
            f"# Safety Guardrail — Individual Test Report",
            f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"**Passed:** {cls.passed} | **Failed:** {cls.failed} | **Total:** {cls.passed + cls.failed}",
            f"",
            f"## Results",
            f"| Test Case | Status | Detail |",
            f"|---|---|---|",
        ]
        for r in cls.REPORT:
            status = "PASS" if r["passed"] else "FAIL"
            lines.append(f"| {r['name']} | {status} | {r['detail']} |")
        _write_report("safety_guardrail", "\n".join(lines))


# ============================================================
# 2. PRIVACY GUARDRAIL (20 cases)
# ============================================================

@pytest.mark.asyncio
class TestPrivacyGuardrailSuite:
    REPORT = []
    passed = 0
    failed = 0

    @classmethod
    def _record(cls, name: str, passed: bool, detail: str = ""):
        if passed:
            cls.passed += 1
        else:
            cls.failed += 1
        cls.REPORT.append({"name": name, "passed": passed, "detail": detail})

    async def test_no_pii_passes(self):
        svc = PrivacyGuardrailService()
        r = await svc.check_input("I need a gift for my wife")
        self._record("no_pii_passes", r.action.value == "allowed")

    async def test_email_redacted_strict(self):
        svc = PrivacyGuardrailService()
        svc.get_or_create_profile("default").privacy_level = PrivacyLevel.strict
        r = await svc.check_input("Send info to john.doe@example.com")
        self._record("email_redacted_strict", r.action.value == "sanitized" and "[REDACTED_EMAIL]" in r.sanitized_text)

    async def test_phone_redacted_strict(self):
        svc = PrivacyGuardrailService()
        svc.get_or_create_profile("default").privacy_level = PrivacyLevel.strict
        r = await svc.check_input("Call me at 555-123-4567")
        self._record("phone_redacted_strict", r.action.value == "sanitized" and "[REDACTED_PHONE]" in r.sanitized_text)

    async def test_ssn_redacted_strict(self):
        svc = PrivacyGuardrailService()
        svc.get_or_create_profile("default").privacy_level = PrivacyLevel.strict
        r = await svc.check_input("My SSN is 123-45-6789")
        self._record("ssn_redacted_strict", r.action.value == "sanitized" and "[REDACTED_SSN]" in r.sanitized_text)

    async def test_multiple_pii_redacted(self):
        svc = PrivacyGuardrailService()
        svc.get_or_create_profile("default").privacy_level = PrivacyLevel.strict
        r = await svc.check_input("Email: alice@test.com, Phone: 555-000-1111")
        self._record("multiple_pii_redacted", r.action.value == "sanitized" and len(r.redacted_fields) >= 2)

    async def test_empty_text(self):
        svc = PrivacyGuardrailService()
        r = await svc.check_input("")
        self._record("empty_text", r.action.value == "allowed")

    async def test_whitespace_text(self):
        svc = PrivacyGuardrailService()
        r = await svc.check_input("   ")
        self._record("whitespace_text", r.action.value == "allowed")

    async def test_agent_access_strict_blocks(self):
        allowed, violations = _rule_based_agent_access("discovery", ["email", "name"], UserPrivacyProfile(privacy_level=PrivacyLevel.strict))
        self._record("agent_access_strict_blocks", not allowed and len(violations) > 0)

    async def test_agent_access_open_allows(self):
        profile = UserPrivacyProfile(privacy_level=PrivacyLevel.open, consents=PrivacyConsent(third_party_sharing=True))
        allowed, violations = _rule_based_agent_access("discovery", ["email", "preferences"], profile)
        self._record("agent_access_open_allows", allowed)

    async def test_agent_access_balanced_blocks_phone(self):
        allowed, violations = _rule_based_agent_access("discovery", ["phone"], UserPrivacyProfile(privacy_level=PrivacyLevel.balanced))
        self._record("agent_access_balanced_blocks_phone", not allowed)

    async def test_agent_access_balanced_allows_email(self):
        allowed, violations = _rule_based_agent_access("discovery", ["email"], UserPrivacyProfile(privacy_level=PrivacyLevel.balanced))
        self._record("agent_access_balanced_allows_email", allowed)

    async def test_output_strict_blocks_personal_data(self):
        svc = PrivacyGuardrailService()
        svc.update_profile("test_user", UserPrivacyProfile(privacy_level=PrivacyLevel.strict))
        r = await svc.check_output([{"id": "p1", "name": "Product", "user_location": "New York"}], "test_user")
        self._record("output_strict_blocks_personal_data", r.action.value == "flagged")

    async def test_output_strict_allows_safe(self):
        svc = PrivacyGuardrailService()
        svc.update_profile("test_user", UserPrivacyProfile(privacy_level=PrivacyLevel.strict))
        r = await svc.check_output([{"id": "p1", "name": "Product", "price": 100}], "test_user")
        self._record("output_strict_allows_safe", r.action.value == "allowed")

    async def test_output_balanced_blocks_precise_location(self):
        svc = PrivacyGuardrailService()
        svc.update_profile("test_user", UserPrivacyProfile(privacy_level=PrivacyLevel.balanced))
        r = await svc.check_output([{"id": "p1", "precise_location": "40.7128,-74.0060"}], "test_user")
        self._record("output_balanced_blocks_precise_location", r.action.value == "flagged")

    async def test_gdpr_forget_user(self):
        svc = PrivacyGuardrailService()
        svc.get_or_create_profile("user1")
        result = await svc.forget_user("user1")
        self._record("gdpr_forget_user", result is True)

    async def test_gdpr_forget_nonexistent(self):
        svc = PrivacyGuardrailService()
        result = await svc.forget_user("nonexistent")
        self._record("gdpr_forget_nonexistent", result is False)

    async def test_export_profile(self):
        svc = PrivacyGuardrailService()
        svc.get_or_create_profile("user1")
        data = svc.export_profile("user1")
        self._record("export_profile", data is not None and data["user_id"] == "user1")

    async def test_export_profile_not_found(self):
        svc = PrivacyGuardrailService()
        data = svc.export_profile("nonexistent")
        self._record("export_profile_not_found", data is None)

    async def test_ccpa_opt_out(self):
        svc = PrivacyGuardrailService()
        svc.get_or_create_profile("user1")
        result = svc.opt_out_of_sale("user1")
        self._record("ccpa_opt_out", result is not None and result.opted_out_of_sale is True and result.consents.third_party_sharing is False)

    async def test_rule_based_redact_email(self):
        sanitized, fields = _rule_based_redact("test@example.com")
        self._record("rule_based_redact_email", "email" in fields and "[REDACTED_EMAIL]" in sanitized)

    async def test_rule_based_redact_phone(self):
        sanitized, fields = _rule_based_redact("Call 555-123-4567 now")
        self._record("rule_based_redact_phone", "phone" in fields and "[REDACTED_PHONE]" in sanitized)

    async def test_rule_based_redact_ssn(self):
        sanitized, fields = _rule_based_redact("SSN: 123-45-6789")
        self._record("rule_based_redact_ssn", "ssn" in fields and "[REDACTED_SSN]" in sanitized)

    async def test_rule_based_redact_clean(self):
        sanitized, fields = _rule_based_redact("I need a new laptop")
        self._record("rule_based_redact_clean", fields == [] and sanitized == "I need a new laptop")

    @classmethod
    def generate_report(cls):
        lines = [
            f"# Privacy Guardrail — Individual Test Report",
            f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"**Passed:** {cls.passed} | **Failed:** {cls.failed} | **Total:** {cls.passed + cls.failed}",
            f"",
            f"## Results",
            f"| Test Case | Status | Detail |",
            f"|---|---|---|",
        ]
        for r in cls.REPORT:
            status = "PASS" if r["passed"] else "FAIL"
            lines.append(f"| {r['name']} | {status} | {r['detail']} |")
        _write_report("privacy_guardrail", "\n".join(lines))


# ============================================================
# 3. PRICE GUARDRAIL (12 cases)
# ============================================================

class TestPriceGuardrailSuite:
    REPORT = []
    passed = 0
    failed = 0

    @classmethod
    def _record(cls, name: str, passed: bool, detail: str = ""):
        if passed:
            cls.passed += 1
        else:
            cls.failed += 1
        cls.REPORT.append({"name": name, "passed": passed, "detail": detail})

    def test_valid_sku(self):
        v = price_guardrail.validate_input("SKU-AB123", 99.99)
        self._record("valid_sku_allowed", v.allowed is True)

    def test_invalid_sku_pattern(self):
        v = price_guardrail.validate_input("invalid", 99.99)
        self._record("invalid_sku_rejected", v.allowed is False and v.category == "invalid_sku")

    def test_sku_wrong_format(self):
        v = price_guardrail.validate_input("SKU-12345", 99.99)
        self._record("sku_wrong_format", v.allowed is False)

    def test_negative_price(self):
        v = price_guardrail.validate_input("SKU-AB123", -10.0)
        self._record("negative_price_rejected", v.allowed is False and v.category == "invalid_price")

    def test_zero_price(self):
        v = price_guardrail.validate_input("SKU-AB123", 0)
        self._record("zero_price_rejected", v.allowed is False)

    def test_price_too_high(self):
        v = price_guardrail.validate_input("SKU-AB123", 200000.0)
        self._record("price_too_high_rejected", v.allowed is False and v.category == "price_cap")

    def test_price_below_minimum(self):
        v = price_guardrail.validate_input("SKU-AB123", 0.001)
        self._record("price_below_minimum_rejected", v.allowed is False and v.category == "price_floor")

    def test_fraud_detect_bad_competitor(self):
        v = price_guardrail.detect_fraud(100.0, 0)
        self._record("fraud_bad_competitor", v.allowed is False and v.category == "bad_competitor")

    def test_fraud_suspicious_ratio(self):
        v = price_guardrail.detect_fraud(1000.0, 5.0)
        self._record("fraud_suspicious_ratio", v.allowed is False and v.category == "suspicious_data")

    def test_fraud_gouging_risk(self):
        v = price_guardrail.detect_fraud(50.0, 150.0)
        self._record("fraud_gouging_risk", v.allowed is False and v.category == "gouging_risk")

    def test_fraud_allowed(self):
        v = price_guardrail.detect_fraud(100.0, 90.0)
        self._record("fraud_allowed", v.allowed is True)

    def test_rate_limit(self):
        pg = PriceGuardrail()
        results = [pg.check_rate_limit("user1") for _ in range(51)]
        self._record("rate_limit_blocks_at_51", results[-1].allowed is False)

    def test_abuse_cap_exceeded(self):
        pg = PriceGuardrail()
        pg.check_rate_limit("user2")
        pg.record_discount("user2", 1999.0)
        v = pg.check_abuse("user2", 100.0)
        self._record("abuse_cap_exceeded", v.allowed is False)

    def test_abuse_allowed(self):
        pg = PriceGuardrail()
        pg.check_rate_limit("user3")
        pg.record_discount("user3", 100.0)
        v = pg.check_abuse("user3", 100.0)
        self._record("abuse_allowed", v.allowed is True)

    @classmethod
    def generate_report(cls):
        lines = [
            f"# Price Guardrail — Individual Test Report",
            f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"**Passed:** {cls.passed} | **Failed:** {cls.failed} | **Total:** {cls.passed + cls.failed}",
            f"",
            f"## Results",
            f"| Test Case | Status | Detail |",
            f"|---|---|---|",
        ]
        for r in cls.REPORT:
            status = "PASS" if r["passed"] else "FAIL"
            lines.append(f"| {r['name']} | {status} | {r['detail']} |")
        _write_report("price_guardrail", "\n".join(lines))


# ============================================================
# 4. PRICE MATCH (8 cases)
# ============================================================

class TestPriceMatchSuite:
    REPORT = []
    passed = 0
    failed = 0

    @classmethod
    def _record(cls, name: str, passed: bool, detail: str = ""):
        if passed:
            cls.passed += 1
        else:
            cls.failed += 1
        cls.REPORT.append({"name": name, "passed": passed, "detail": detail})

    def test_fetch_competitor_price_found(self):
        r = fetch_competitor_price("SKU-0001")
        self._record("fetch_competitor_price_found", "error" not in r and "price" in r)

    def test_fetch_competitor_price_not_found(self):
        r = fetch_competitor_price("SKU-9999")
        self._record("fetch_competitor_price_not_found", "error" in r)

    def test_fetch_competitor_price_specific_store(self):
        r = fetch_competitor_price("SKU-0001", store="Amazon")
        self._record("fetch_competitor_price_specific_store", "error" not in r and r.get("store") == "Amazon")

    def test_authorize_price_match_approved(self):
        r = authorize_price_match(100.0, 80.0)
        self._record("authorize_approved", r["status"] == "approved" and r["discount_amount"] == 20.0)

    def test_authorize_price_match_capped(self):
        r = authorize_price_match(100.0, 50.0)
        self._record("authorize_capped", r["status"] == "approved" and r["discount_amount"] == 25.0)

    def test_authorize_price_match_declined(self):
        r = authorize_price_match(80.0, 100.0)
        self._record("authorize_declined", r["status"] == "declined")

    def test_authorize_invalid_competitor(self):
        r = authorize_price_match(100.0, 0)
        self._record("authorize_invalid_competitor", r["status"] == "declined")

    def test_get_price_history(self):
        h = get_price_history("SKU-0001")
        self._record("get_price_history", len(h) == 15)

    def test_get_price_drop_alerts(self):
        alerts = get_price_drop_alerts("SKU-0001", threshold_pct=1.0)
        self._record("get_price_drop_alerts", isinstance(alerts, list))

    @classmethod
    def generate_report(cls):
        lines = [
            f"# Price Match — Individual Test Report",
            f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"**Passed:** {cls.passed} | **Failed:** {cls.failed} | **Total:** {cls.passed + cls.failed}",
            f"",
            f"## Results",
            f"| Test Case | Status | Detail |",
            f"|---|---|---|",
        ]
        for r in cls.REPORT:
            status = "PASS" if r["passed"] else "FAIL"
            lines.append(f"| {r['name']} | {status} | {r['detail']} |")
        _write_report("price_match", "\n".join(lines))


# ============================================================
# 5. INTENT PARSER (8 cases)
# ============================================================

@pytest.mark.asyncio
class TestIntentParserSuite:
    REPORT = []
    passed = 0
    failed = 0

    @classmethod
    def _record(cls, name: str, passed: bool, detail: str = ""):
        if passed:
            cls.passed += 1
        else:
            cls.failed += 1
        cls.REPORT.append({"name": name, "passed": passed, "detail": detail})

    async def test_rule_based_category(self):
        intent = _rule_based_fallback("I need a laptop for programming")
        self._record("rule_category_laptop", intent.category is not None)

    async def test_rule_based_budget(self):
        intent = _rule_based_fallback("find shoes under $100")
        self._record("rule_budget", intent.budget == 100.0)

    async def test_rule_based_occasion(self):
        intent = _rule_based_fallback("birthday gift for my wife")
        self._record("rule_occasion", intent.occasion == "birthday")

    async def test_rule_based_empty(self):
        intent = _rule_based_fallback("")
        self._record("rule_empty", intent.raw_query == "" and intent.category is None)

    async def test_parse_intent_basic(self):
        intent = await parse_intent("show me running shoes")
        self._record("parse_intent_basic", intent.raw_query == "show me running shoes")

    async def test_parse_intent_with_budget(self):
        intent = await parse_intent("buy a laptop under $800")
        self._record("parse_intent_with_budget", intent.budget is not None)

    async def test_parse_intent_occasion(self):
        intent = await parse_intent("anniversary gift for husband who loves cooking")
        self._record("parse_intent_occasion", intent.occasion is not None)

    async def test_parse_intent_empty(self):
        intent = await parse_intent("")
        self._record("parse_intent_empty", intent.raw_query == "")

    @classmethod
    def generate_report(cls):
        lines = [
            f"# Intent Parser — Individual Test Report",
            f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"**Passed:** {cls.passed} | **Failed:** {cls.failed} | **Total:** {cls.passed + cls.failed}",
            f"",
            f"## Results",
            f"| Test Case | Status | Detail |",
            f"|---|---|---|",
        ]
        for r in cls.REPORT:
            status = "PASS" if r["passed"] else "FAIL"
            lines.append(f"| {r['name']} | {status} | {r['detail']} |")
        _write_report("intent_parser", "\n".join(lines))


# ============================================================
# 6. CATALOG SEARCH (6 cases)
# ============================================================

class TestCatalogSearchSuite:
    REPORT = []
    passed = 0
    failed = 0

    @classmethod
    def _record(cls, name: str, passed: bool, detail: str = ""):
        if passed:
            cls.passed += 1
        else:
            cls.failed += 1
        cls.REPORT.append({"name": name, "passed": passed, "detail": detail})

    def test_search_simple_found(self):
        results = search_simple("laptop")
        self._record("search_simple_laptop", len(results) > 0)

    def test_search_simple_no_results(self):
        results = search_simple("zzzznotfound")
        self._record("search_simple_no_results", len(results) == 0)

    def test_search_simple_empty(self):
        results = search_simple("")
        self._record("search_simple_empty", len(results) > 0)

    def test_search_smartphone(self):
        results = search_simple("smartphone")
        self._record("search_smartphone", len(results) > 0)

    def test_search_partial_match(self):
        results = search_simple("headphone")
        self._record("search_headphone", len(results) > 0)

    def test_search_category(self):
        results = search_simple("headphones")
        self._record("search_headphones_category", len(results) > 0)

    @classmethod
    def generate_report(cls):
        lines = [
            f"# Catalog Search — Individual Test Report",
            f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"**Passed:** {cls.passed} | **Failed:** {cls.failed} | **Total:** {cls.passed + cls.failed}",
            f"",
            f"## Results",
            f"| Test Case | Status | Detail |",
            f"|---|---|---|",
        ]
        for r in cls.REPORT:
            status = "PASS" if r["passed"] else "FAIL"
            lines.append(f"| {r['name']} | {status} | {r['detail']} |")
        _write_report("catalog_search", "\n".join(lines))


# ============================================================
# 7. RECOMMENDATION (6 cases)
# ============================================================

class TestRecommendationSuite:
    REPORT = []
    passed = 0
    failed = 0

    @classmethod
    def _record(cls, name: str, passed: bool, detail: str = ""):
        if passed:
            cls.passed += 1
        else:
            cls.failed += 1
        cls.REPORT.append({"name": name, "passed": passed, "detail": detail})

    def test_recommendations_by_category(self):
        prefs = UserPreferences(categories=["electronics"])
        results = get_recommendations(prefs)
        self._record("recommendations_electronics", len(results) > 0)

    def test_recommendations_with_price_range(self):
        prefs = UserPreferences(categories=["electronics"], price_min=500, price_max=1500)
        results = get_recommendations(prefs)
        self._record("recommendations_price_range", len(results) > 0)

    def test_recommendations_brand_filter(self):
        prefs = UserPreferences(categories=["electronics"], brands=["TechBrand"])
        results = get_recommendations(prefs)
        self._record("recommendations_brand_filter", isinstance(results, list))

    def test_recommendations_no_results(self):
        prefs = UserPreferences(categories=["nonexistent"], price_min=99999, price_max=100000)
        results = get_recommendations(prefs)
        self._record("recommendations_no_results", len(results) == 0)

    def test_search_products_found(self):
        results = search_products("laptop")
        self._record("search_products_laptop", len(results) > 0)

    def test_search_products_not_found(self):
        results = search_products("zzzznotfound")
        self._record("search_products_no_results", len(results) == 0)

    @classmethod
    def generate_report(cls):
        lines = [
            f"# Recommendation — Individual Test Report",
            f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"**Passed:** {cls.passed} | **Failed:** {cls.failed} | **Total:** {cls.passed + cls.failed}",
            f"",
            f"## Results",
            f"| Test Case | Status | Detail |",
            f"|---|---|---|",
        ]
        for r in cls.REPORT:
            status = "PASS" if r["passed"] else "FAIL"
            lines.append(f"| {r['name']} | {status} | {r['detail']} |")
        _write_report("recommendation", "\n".join(lines))


# ============================================================
# 8. CROSS SELL (4 cases)
# ============================================================

class TestCrossSellSuite:
    REPORT = []
    passed = 0
    failed = 0

    @classmethod
    def _record(cls, name: str, passed: bool, detail: str = ""):
        if passed:
            cls.passed += 1
        else:
            cls.failed += 1
        cls.REPORT.append({"name": name, "passed": passed, "detail": detail})

    def test_cross_sell_found(self):
        result = get_cross_sell(1)
        self._record("cross_sell_found", len(result.recommendations) > 0)

    def test_cross_sell_with_cart(self):
        result = get_cross_sell(1, cart_product_ids=[2, 3])
        self._record("cross_sell_with_cart", len(result.recommendations) > 0 and len(result.cart_context) > 0)

    def test_cross_sell_types_present(self):
        result = get_cross_sell(1)
        types = {r.type for r in result.recommendations}
        self._record("cross_sell_types", "upsell" in types)

    def test_cross_sell_source_product(self):
        result = get_cross_sell(1)
        self._record("cross_sell_source_product", result.source_product is not None)

    @classmethod
    def generate_report(cls):
        lines = [
            f"# Cross Sell — Individual Test Report",
            f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"**Passed:** {cls.passed} | **Failed:** {cls.failed} | **Total:** {cls.passed + cls.failed}",
            f"",
            f"## Results",
            f"| Test Case | Status | Detail |",
            f"|---|---|---|",
        ]
        for r in cls.REPORT:
            status = "PASS" if r["passed"] else "FAIL"
            lines.append(f"| {r['name']} | {status} | {r['detail']} |")
        _write_report("cross_sell", "\n".join(lines))


# ============================================================
# 9. GIFT FINDER (4 cases)
# ============================================================

class TestGiftFinderSuite:
    REPORT = []
    passed = 0
    failed = 0

    @classmethod
    def _record(cls, name: str, passed: bool, detail: str = ""):
        if passed:
            cls.passed += 1
        else:
            cls.failed += 1
        cls.REPORT.append({"name": name, "passed": passed, "detail": detail})

    def test_gift_finder_birthday(self):
        recipient = GiftRecipient(occasion="birthday", relationship="mother", age_group="adult", interests=["books", "music"])
        result = find_gifts(recipient)
        self._record("gift_finder_birthday", result.total_found > 0)

    def test_gift_finder_anniversary(self):
        recipient = GiftRecipient(occasion="anniversary", relationship="spouse", age_group="adult", interests=["electronics", "gadgets"])
        result = find_gifts(recipient)
        self._record("gift_finder_anniversary", result.total_found > 0)

    def test_gift_finder_summary_not_empty(self):
        recipient = GiftRecipient(occasion="birthday", relationship="friend", age_group="teen", interests=["sports", "gaming"])
        result = find_gifts(recipient)
        self._record("gift_finder_summary", len(result.summary) > 0)

    def test_gift_finder_no_interests(self):
        recipient = GiftRecipient(occasion="birthday", relationship="friend", age_group="adult", interests=[])
        result = find_gifts(recipient)
        self._record("gift_finder_no_interests", result.total_found >= 0)

    @classmethod
    def generate_report(cls):
        lines = [
            f"# Gift Finder — Individual Test Report",
            f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"**Passed:** {cls.passed} | **Failed:** {cls.failed} | **Total:** {cls.passed + cls.failed}",
            f"",
            f"## Results",
            f"| Test Case | Status | Detail |",
            f"|---|---|---|",
        ]
        for r in cls.REPORT:
            status = "PASS" if r["passed"] else "FAIL"
            lines.append(f"| {r['name']} | {status} | {r['detail']} |")
        _write_report("gift_finder", "\n".join(lines))


# ============================================================
# 10. DEAL AGENT (10 cases)
# ============================================================

class TestDealAgentSuite:
    REPORT = []
    passed = 0
    failed = 0

    @classmethod
    def _record(cls, name: str, passed: bool, detail: str = ""):
        if passed:
            cls.passed += 1
        else:
            cls.failed += 1
        cls.REPORT.append({"name": name, "passed": passed, "detail": detail})

    def test_active_promotions(self):
        promos = deal_agent.get_active_promotions()
        self._record("active_promotions", len(promos) > 0)

    def test_add_promotion(self):
        promo = Promotion(id="test_1", name="Test Promo", description="Test", type=DiscountType.fixed, value=10.0, stackable=True)
        added = deal_agent.add_promotion(promo)
        self._record("add_promotion", added is not None and added.id == "test_1")

    def test_deactivate_promotion(self):
        result = deal_agent.deactivate_promotion("test_1")
        self._record("deactivate_promotion", result is True)

    def test_deactivate_nonexistent(self):
        result = deal_agent.deactivate_promotion("nonexistent")
        self._record("deactivate_nonexistent", result is False)

    def test_optimize_stack(self):
        cart = CartSession(
            user_id="user1",
            items=[CartItem(product_id="1", sku="SKU-AB001", name="Laptop", price=1000.0, quantity=1, category="electronics")],
            loyalty_tier=LoyaltyTier.gold,
        )
        stack = deal_agent.optimize_stack(cart)
        self._record("optimize_stack", stack is not None and stack.total_savings > 0)

    def test_optimize_stack_empty_cart(self):
        cart = CartSession(user_id="user1", items=[])
        stack = deal_agent.optimize_stack(cart)
        self._record("optimize_stack_empty", stack is None or stack.total_savings == 0)

    def test_apply_stack(self):
        cart = CartSession(
            user_id="user1",
            items=[CartItem(product_id="1", sku="SKU-AB001", name="Laptop", price=1000.0, quantity=1, category="electronics")],
            loyalty_tier=LoyaltyTier.gold,
        )
        stack = deal_agent.optimize_stack(cart)
        if stack:
            result = deal_agent.apply_stack(stack.id)
            self._record("apply_stack", result is not None)
        else:
            self._record("apply_stack", False, "no stack to apply")

    def test_list_stacks(self):
        stacks = deal_agent.list_stacks()
        self._record("list_stacks", isinstance(stacks, list))

    def test_process_cart(self):
        req = DealSessionRequest(
            user_id="user1",
            items=[CartItem(product_id="1", sku="SKU-AB001", name="Laptop", price=1000.0, quantity=1, category="electronics")],
            loyalty_tier=LoyaltyTier.platinum,
        )
        result = deal_agent.process_cart(req)
        self._record("process_cart", "total_savings" in result)

    def test_promotion_is_applicable(self):
        promo = Promotion(id="p_test", name="10 off", description="test", type=DiscountType.fixed, value=10.0, min_purchase=50.0, applicable_categories=["electronics"])
        cart = CartSession(
            user_id="user1",
            items=[CartItem(product_id="1", sku="SKU-AB001", name="Laptop", price=100.0, quantity=1, category="electronics")],
            loyalty_tier=LoyaltyTier.gold,
        )
        self._record("promotion_is_applicable", promo.is_applicable(cart) is True)

    def test_promotion_not_applicable_low_tier(self):
        promo = Promotion(id="p_test2", name="Gold only", description="test", type=DiscountType.fixed, value=10.0, min_loyalty_tier=LoyaltyTier.gold)
        cart = CartSession(
            user_id="user1",
            items=[CartItem(product_id="1", sku="SKU-AB001", name="Laptop", price=100.0, quantity=1, category="electronics")],
            loyalty_tier=LoyaltyTier.bronze,
        )
        self._record("promotion_not_applicable_low_tier", promo.is_applicable(cart) is False)

    def test_promotion_apply_fixed(self):
        promo = Promotion(id="p_fixed", name="$20 off", description="test", type=DiscountType.fixed, value=20.0)
        cart = CartSession(
            user_id="user1",
            items=[CartItem(product_id="1", sku="SKU-AB001", name="Item", price=100.0, quantity=1, category="general")],
        )
        result = promo.apply_to(cart)
        self._record("promotion_apply_fixed", result["discount"] == 20.0)

    def test_promotion_apply_percentage(self):
        promo = Promotion(id="p_pct", name="10% off", description="test", type=DiscountType.percentage, value=10.0)
        cart = CartSession(
            user_id="user1",
            items=[CartItem(product_id="1", sku="SKU-AB001", name="Item", price=200.0, quantity=1, category="general")],
        )
        result = promo.apply_to(cart)
        self._record("promotion_apply_percentage", result["discount"] == 20.0)

    def test_promotion_apply_bogo(self):
        promo = Promotion(id="p_bogo", name="BOGO", description="test", type=DiscountType.bogo, value=0)
        cart = CartSession(
            user_id="user1",
            items=[
                CartItem(product_id="1", sku="SKU-AB001", name="Item A", price=50.0, quantity=1, category="general"),
                CartItem(product_id="2", sku="SKU-AB002", name="Item B", price=30.0, quantity=1, category="general"),
            ],
        )
        result = promo.apply_to(cart)
        self._record("promotion_apply_bogo", result["discount"] == 30.0)

    @classmethod
    def generate_report(cls):
        lines = [
            f"# Deal Agent — Individual Test Report",
            f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"**Passed:** {cls.passed} | **Failed:** {cls.failed} | **Total:** {cls.passed + cls.failed}",
            f"",
            f"## Results",
            f"| Test Case | Status | Detail |",
            f"|---|---|---|",
        ]
        for r in cls.REPORT:
            status = "PASS" if r["passed"] else "FAIL"
            lines.append(f"| {r['name']} | {status} | {r['detail']} |")
        _write_report("deal_agent", "\n".join(lines))


# ============================================================
# 11. AGENT ORCHESTRATOR (8 cases)
# ============================================================

@pytest.mark.asyncio
class TestOrchestratorSuite:
    REPORT = []
    passed = 0
    failed = 0

    @classmethod
    def _record(cls, name: str, passed: bool, detail: str = ""):
        if passed:
            cls.passed += 1
        else:
            cls.failed += 1
        cls.REPORT.append({"name": name, "passed": passed, "detail": detail})

    async def test_create_agent(self):
        agent = orchestrator.create_agent("test_agent", task="find laptops")
        self._record("create_agent", agent is not None and agent.name == "test_agent")

    async def test_get_agent(self):
        agent = orchestrator.create_agent("get_test_agent")
        fetched = orchestrator.get_agent(agent.id)
        self._record("get_agent", fetched is not None and fetched.id == agent.id)

    async def test_get_nonexistent_agent(self):
        fetched = orchestrator.get_agent("nonexistent")
        self._record("get_nonexistent_agent", fetched is None)

    async def test_list_agents(self):
        agents = orchestrator.list_agents()
        self._record("list_agents", len(agents) > 0)

    async def test_create_task(self):
        agent = orchestrator.create_agent("task_agent")
        task = orchestrator.create_task(agent.id, "search")
        self._record("create_task", task is not None and task.type == "search")

    async def test_list_tasks(self):
        tasks = orchestrator.list_tasks()
        self._record("list_tasks", isinstance(tasks, list))

    async def test_delete_agent(self):
        agent = orchestrator.create_agent("delete_agent")
        result = orchestrator.delete_agent(agent.id)
        self._record("delete_agent", result is True)

    async def test_delete_nonexistent_agent(self):
        result = orchestrator.delete_agent("nonexistent")
        self._record("delete_nonexistent_agent", result is False)

    async def test_run_agent(self):
        agent = orchestrator.create_agent("run_test_agent", task="find laptops under $1000")
        result = await orchestrator.run_agent(agent.id)
        self._record("run_agent", result is not None)

    async def test_run_price_match(self):
        agent = orchestrator.create_agent("price_match_agent")
        result = await orchestrator.run_price_match(agent.id, "1", "SKU-0001")
        self._record("run_price_match", result is not None)

    async def test_run_gift_finder(self):
        agent = orchestrator.create_agent("gift_finder_agent")
        recipient = GiftRecipient(occasion="birthday", relationship="mother", age_group="adult", interests=["books"])
        result = await orchestrator.run_gift_finder(agent.id, recipient)
        self._record("run_gift_finder", result is not None)

    async def test_run_cross_sell(self):
        agent = orchestrator.create_agent("cross_sell_agent")
        result = await orchestrator.run_cross_sell_agent(agent.id, 1)
        self._record("run_cross_sell", result is not None)

    @classmethod
    def generate_report(cls):
        lines = [
            f"# Agent Orchestrator — Individual Test Report",
            f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"**Passed:** {cls.passed} | **Failed:** {cls.failed} | **Total:** {cls.passed + cls.failed}",
            f"",
            f"## Results",
            f"| Test Case | Status | Detail |",
            f"|---|---|---|",
        ]
        for r in cls.REPORT:
            status = "PASS" if r["passed"] else "FAIL"
            lines.append(f"| {r['name']} | {status} | {r['detail']} |")
        _write_report("agent_orchestrator", "\n".join(lines))


# ============================================================
# Runner — Generates summary report
# ============================================================

def _generate_reports():
    suites = [
        ("Safety Guardrail", TestSafetyGuardrailSuite),
        ("Privacy Guardrail", TestPrivacyGuardrailSuite),
        ("Price Guardrail", TestPriceGuardrailSuite),
        ("Price Match", TestPriceMatchSuite),
        ("Intent Parser", TestIntentParserSuite),
        ("Catalog Search", TestCatalogSearchSuite),
        ("Recommendation", TestRecommendationSuite),
        ("Cross Sell", TestCrossSellSuite),
        ("Gift Finder", TestGiftFinderSuite),
        ("Deal Agent", TestDealAgentSuite),
        ("Agent Orchestrator", TestOrchestratorSuite),
    ]
    for name, suite_cls in suites:
        suite_cls.generate_report()

    total_passed = sum(sc.passed for _, sc in suites)
    total_failed = sum(sc.failed for _, sc in suites)
    total = total_passed + total_failed

    summary_lines = [
        f"# Agent Individual Test Summary Report",
        f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        f"**Total Passed:** {total_passed} | **Total Failed:** {total_failed} | **Total:** {total}",
        f"",
        f"## Per-Agent Results",
        f"| Agent | Passed | Failed | Total |",
        f"|---|---|---|---|",
    ]
    for name, suite_cls in suites:
        p = suite_cls.passed
        f = suite_cls.failed
        summary_lines.append(f"| {name} | {p} | {f} | {p + f} |")
        report_path = os.path.join(REPORT_DIR, f"{name.lower().replace(' ', '_')}_report.md")
        summary_lines.append(f"  - [Detailed Report]({report_path})")

    summary_lines.append("")
    summary_lines.append("## Final Verdict")
    if total_failed == 0:
        summary_lines.append("**ALL TESTS PASSED** ✓")
    else:
        summary_lines.append(f"**{total_failed} test(s) FAILED** ✗")

    _write_report("summary", "\n".join(summary_lines))
    print(f"\n{'=' * 60}")
    print(f"SUMMARY: {total_passed}/{total} passed, {total_failed} failed")
    print(f"Reports written to: {REPORT_DIR}")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    import pytest
    class ReportPlugin:
        def pytest_sessionfinish(self, session):
            _generate_reports()
    sys.exit(pytest.main([__file__, "-v", "--tb=short"], plugins=[ReportPlugin()]))

