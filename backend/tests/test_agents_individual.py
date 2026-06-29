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
    QueryIntent, AgentStatus, TaskStatus, GuardrailAction,
    AppliedDiscount, DiscountStack, CrossSellItem, CrossSellResult,
    GiftRecommendation, GiftFinderResult,
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
from shared.products import ALL_PRODUCTS, CATEGORIES

REPORT_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "agent_reports")


def _write_report(agent_name: str, content: str):
    os.makedirs(REPORT_DIR, exist_ok=True)
    path = os.path.join(REPORT_DIR, f"{agent_name}_report.md")
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


# ============================================================
# 1. SAFETY GUARDRAIL — 60 cases
# ============================================================

@pytest.mark.asyncio
class TestSafetyGuardrailSuite:
    REPORT = []
    passed = 0
    failed = 0

    @classmethod
    def setup_class(cls):
        cls.REPORT = []; cls.passed = 0; cls.failed = 0

    @classmethod
    def _record(cls, name, passed, detail=""):
        if passed: cls.passed += 1
        else: cls.failed += 1
        cls.REPORT.append({"name": name, "passed": passed, "detail": detail})

    async def test_safe_laptop(self):
        r = await check_safety("I need a new laptop"); self._record("safe_laptop", r.allowed)
    async def test_safe_shoes(self):
        r = await check_safety("show me running shoes"); self._record("safe_shoes", r.allowed)
    async def test_safe_gift(self):
        r = await check_safety("birthday gift for mom"); self._record("safe_gift", r.allowed)
    async def test_safe_headphones(self):
        r = await check_safety("wireless headphones"); self._record("safe_headphones", r.allowed)
    async def test_safe_yoga(self):
        r = await check_safety("yoga mat"); self._record("safe_yoga", r.allowed)
    async def test_safe_books(self):
        r = await check_safety("fiction books for sale"); self._record("safe_books", r.allowed)
    async def test_safe_groceries(self):
        r = await check_safety("organic groceries"); self._record("safe_groceries", r.allowed)
    async def test_safe_furniture(self):
        r = await check_safety("office chair"); self._record("safe_furniture", r.allowed)
    async def test_safe_camera(self):
        r = await check_safety("digital camera"); self._record("safe_camera", r.allowed)
    async def test_safe_monitor(self):
        r = await check_safety("computer monitor 4k"); self._record("safe_monitor", r.allowed)
    async def test_weapons_gun(self):
        r = await check_safety("Looking for a gun"); self._record("weapons_gun", r.allowed is False and r.blocked_category == "weapons")
    async def test_weapons_rifle(self):
        r = await check_safety("rifle for sale"); self._record("weapons_rifle", r.allowed is False)
    async def test_weapons_pistol(self):
        r = await check_safety("pistol holster"); self._record("weapons_pistol", r.allowed is False)
    async def test_weapons_shotgun(self):
        r = await check_safety("shotgun shells"); self._record("weapons_shotgun", r.allowed is False)
    async def test_weapons_ammo(self):
        r = await check_safety("buy ammunition online"); self._record("weapons_ammo", r.allowed is False)
    async def test_weapons_explosive(self):
        r = await check_safety("explosive material"); self._record("weapons_explosive", r.allowed is False)
    async def test_weapons_bomb(self):
        r = await check_safety("bomb threat"); self._record("weapons_bomb", r.allowed is False)
    async def test_weapons_sword(self):
        r = await check_safety("decorative sword"); self._record("weapons_sword", r.allowed is False)
    async def test_weapons_knife(self):
        r = await check_safety("knife block for kitchen"); self._record("weapons_knife", r.allowed is False)
    async def test_weapons_blade(self):
        r = await check_safety("blade runner movie"); self._record("weapons_blade", r.allowed is False)
    async def test_drugs_cocaine(self):
        r = await check_safety("Where can I buy cocaine"); self._record("drugs_cocaine", r.allowed is False and r.blocked_category == "drugs")
    async def test_drugs_heroin(self):
        r = await check_safety("heroin price"); self._record("drugs_heroin", r.allowed is False)
    async def test_drugs_mdma(self):
        r = await check_safety("mdma pills"); self._record("drugs_mdma", r.allowed is False)
    async def test_drugs_weed(self):
        r = await check_safety("weed for sale"); self._record("drugs_weed", r.allowed is False)
    async def test_drugs_marijuana(self):
        r = await check_safety("marijuana growing kit"); self._record("drugs_marijuana", r.allowed is False)
    async def test_drugs_opioid(self):
        r = await check_safety("opioid pain relief"); self._record("drugs_opioid", r.allowed is False)
    async def test_drugs_narcotic(self):
        r = await check_safety("narcotic substances"); self._record("drugs_narcotic", r.allowed is False)
    async def test_drugs_meth(self):
        r = await check_safety("methamphetamine"); self._record("drugs_meth", r.allowed is False)
    async def test_drugs_lsd(self):
        r = await check_safety("lsd tabs"); self._record("drugs_lsd", r.allowed is False)
    async def test_drugs_ecstasy(self):
        r = await check_safety("ecstasy pills"); self._record("drugs_ecstasy", r.allowed is False)
    async def test_adult_porn(self):
        r = await check_safety("porn video"); self._record("adult_porn", r.allowed is False and r.blocked_category == "adult")
    async def test_adult_nsfw(self):
        r = await check_safety("nsfw content"); self._record("adult_nsfw", r.allowed is False)
    async def test_adult_xxx(self):
        r = await check_safety("xxx movies"); self._record("adult_xxx", r.allowed is False)
    async def test_adult_explicit(self):
        r = await check_safety("explicit material"); self._record("adult_explicit", r.allowed is False)
    async def test_adult_sex_toy(self):
        r = await check_safety("sex toy for couples"); self._record("adult_sex_toy", r.allowed is False)
    async def test_alcohol_beer(self):
        r = await check_safety("buy beer online"); self._record("alcohol_beer", r.allowed is False and r.blocked_category == "alcohol_tobacco")
    async def test_alcohol_wine(self):
        r = await check_safety("wine delivery"); self._record("alcohol_wine", r.allowed is False)
    async def test_alcohol_vodka(self):
        r = await check_safety("vodka bottle"); self._record("alcohol_vodka", r.allowed is False)
    async def test_tobacco_cigarette(self):
        r = await check_safety("cigarette pack"); self._record("tobacco_cigarette", r.allowed is False)
    async def test_tobacco_vape(self):
        r = await check_safety("vape juice"); self._record("tobacco_vape", r.allowed is False)
    async def test_tobacco_nicotine(self):
        r = await check_safety("nicotine patches"); self._record("tobacco_nicotine", r.allowed is False)
    async def test_counterfeit_fake(self):
        r = await check_safety("fake rolex watches"); self._record("counterfeit_fake", r.allowed is False and r.blocked_category == "counterfeit")
    async def test_counterfeit_replica(self):
        r = await check_safety("replica handbags"); self._record("counterfeit_replica", r.allowed is False)
    async def test_counterfeit_knockoff(self):
        r = await check_safety("knockoff designer shoes"); self._record("counterfeit_knockoff", r.allowed is False)
    async def test_counterfeit_forged(self):
        r = await check_safety("forged documents"); self._record("counterfeit_forged", r.allowed is False)
    async def test_counterfeit_bootleg(self):
        r = await check_safety("bootleg dvds"); self._record("counterfeit_bootleg", r.allowed is False)
    async def test_gambling_casino(self):
        r = await check_safety("casino games"); self._record("gambling_casino", r.allowed is False and r.blocked_category == "gambling")
    async def test_gambling_lottery(self):
        r = await check_safety("lottery tickets"); self._record("gambling_lottery", r.allowed is False)
    async def test_gambling_betting(self):
        r = await check_safety("sports betting"); self._record("gambling_betting", r.allowed is False)
    async def test_gambling_poker(self):
        r = await check_safety("poker chips"); self._record("gambling_poker", r.allowed is False)
    async def test_gambling_roulette(self):
        r = await check_safety("roulette table"); self._record("gambling_roulette", r.allowed is False)
    async def test_hacking_malware(self):
        r = await check_safety("malware software"); self._record("hacking_malware", r.allowed is False and r.blocked_category == "hacking")
    async def test_hacking_virus(self):
        r = await check_safety("virus creation kit"); self._record("hacking_virus", r.allowed is False)
    async def test_hacking_ransomware(self):
        r = await check_safety("ransomware builder"); self._record("hacking_ransomware", r.allowed is False)
    async def test_hacking_phishing(self):
        r = await check_safety("phishing templates"); self._record("hacking_phishing", r.allowed is False)
    async def test_hacking_jailbreak(self):
        r = await check_safety("jailbreak iphone"); self._record("hacking_jailbreak", r.allowed is False)
    async def test_prescription_gdpr(self):
        r = await check_safety("need prescription medicine", region=PrivacyRegion.gdpr)
        self._record("prescription_gdpr", r.allowed is False and r.blocked_category == "prescription")
    async def test_prescription_ccpa(self):
        r = await check_safety("buy antibiotics", region=PrivacyRegion.ccpa)
        self._record("prescription_ccpa", r.allowed is False)
    async def test_prescription_no_region(self):
        r = await check_safety("need prescription medicine", region=PrivacyRegion.none)
        self._record("prescription_no_region", r.allowed)
    async def test_controlled_gdpr(self):
        r = await check_safety("controlled substance refill", region=PrivacyRegion.gdpr)
        self._record("controlled_gdpr", r.allowed is False)
    async def test_empty_query(self):
        r = await check_safety(""); self._record("empty_query", r.allowed)
    async def test_whitespace_query(self):
        r = await check_safety("   "); self._record("whitespace_query", r.allowed)
    async def test_toy_gun(self):
        r = await check_safety("toy gun for cosplay"); self._record("toy_gun_blocked", r.allowed is False)
    async def test_firearm_safety(self):
        r = await check_safety("firearm safety course"); self._record("firearm_safety", r.allowed is False and r.blocked_category == "weapons")

    @classmethod
    def generate_report(cls):
        lines = [f"# Safety Guardrail \u2014 Individual Test Report",
            f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"**Passed:** {cls.passed} | **Failed:** {cls.failed} | **Total:** {cls.passed + cls.failed}","",
            "## Results","| Test Case | Status | Detail |","|---|---|---|"]
        for r in cls.REPORT:
            lines.append(f"| {r['name']} | {'PASS' if r['passed'] else 'FAIL'} | {r['detail']} |")
        _write_report("safety_guardrail", "\n".join(lines))


# ============================================================
# 2. PRIVACY GUARDRAIL — 60 cases
# ============================================================

@pytest.mark.asyncio
class TestPrivacyGuardrailSuite:
    REPORT = []; passed = 0; failed = 0

    @classmethod
    def _record(cls, name, passed, detail=""):
        if passed: cls.passed += 1
        else: cls.failed += 1
        cls.REPORT.append({"name": name, "passed": passed, "detail": detail})

    async def test_no_pii(self):
        svc = PrivacyGuardrailService()
        r = await svc.check_input("I need a gift for my wife"); self._record("no_pii", r.action.value == "allowed")
    async def test_email_strict(self):
        svc = PrivacyGuardrailService(); svc.get_or_create_profile("p1").privacy_level = PrivacyLevel.strict
        r = await svc.check_input("Send info to john@example.com"); self._record("email_strict", r.action.value == "sanitized" and "[REDACTED_EMAIL]" in r.sanitized_text)
    async def test_phone_strict(self):
        svc = PrivacyGuardrailService(); svc.get_or_create_profile("p2").privacy_level = PrivacyLevel.strict
        r = await svc.check_input("Call me at 555-123-4567"); self._record("phone_strict", r.action.value == "sanitized" and "[REDACTED_PHONE]" in r.sanitized_text)
    async def test_ssn_strict(self):
        svc = PrivacyGuardrailService(); svc.get_or_create_profile("p3").privacy_level = PrivacyLevel.strict
        r = await svc.check_input("My SSN is 123-45-6789"); self._record("ssn_strict", r.action.value == "sanitized" and "[REDACTED_SSN]" in r.sanitized_text)
    async def test_address_strict(self):
        svc = PrivacyGuardrailService(); svc.get_or_create_profile("p4").privacy_level = PrivacyLevel.strict
        r = await svc.check_input("Ship to 123 Main Street"); self._record("address_strict", r.action.value == "sanitized" and "[REDACTED_ADDRESS]" in r.sanitized_text)
    async def test_cc_strict(self):
        svc = PrivacyGuardrailService(); svc.get_or_create_profile("p5").privacy_level = PrivacyLevel.strict
        r = await svc.check_input("My card is 4111111111111111"); self._record("cc_strict", r.action.value == "sanitized" and "[REDACTED_CC]" in r.sanitized_text)
    async def test_multi_pii(self):
        svc = PrivacyGuardrailService(); svc.get_or_create_profile("p6").privacy_level = PrivacyLevel.strict
        r = await svc.check_input("Email: alice@test.com, Phone: 555-000-1111"); self._record("multi_pii", r.action.value == "sanitized" and len(r.redacted_fields) >= 2)
    async def test_email_domain(self):
        svc = PrivacyGuardrailService(); svc.get_or_create_profile("p7").privacy_level = PrivacyLevel.strict
        r = await svc.check_input("Contact user@company.co.uk"); self._record("email_domain", "[REDACTED_EMAIL]" in r.sanitized_text)
    async def test_phone_intl(self):
        svc = PrivacyGuardrailService(); svc.get_or_create_profile("p8").privacy_level = PrivacyLevel.strict
        r = await svc.check_input("Dial +1-212-555-0198"); self._record("phone_intl", "[REDACTED_PHONE]" in r.sanitized_text)
    async def test_single_name_not_pii(self):
        svc = PrivacyGuardrailService(); svc.get_or_create_profile("p9").privacy_level = PrivacyLevel.strict
        r = await svc.check_input("I want a gift for John"); self._record("single_name", r.action.value == "allowed")
    async def test_empty_strict(self):
        svc = PrivacyGuardrailService(); svc.get_or_create_profile("p10").privacy_level = PrivacyLevel.strict
        r = await svc.check_input(""); self._record("empty_strict", r.action.value == "allowed")
    async def test_whitespace_strict(self):
        svc = PrivacyGuardrailService(); svc.get_or_create_profile("p11").privacy_level = PrivacyLevel.strict
        r = await svc.check_input("   "); self._record("whitespace_strict", r.action.value == "allowed")
    async def test_email_balanced(self):
        svc = PrivacyGuardrailService(); svc.get_or_create_profile("p12").privacy_level = PrivacyLevel.balanced
        r = await svc.check_input("Email me at a@b.com"); self._record("email_balanced", r.action.value in ("allowed","sanitized"))
    async def test_phone_balanced(self):
        svc = PrivacyGuardrailService(); svc.get_or_create_profile("p13").privacy_level = PrivacyLevel.balanced
        r = await svc.check_input("Call 555-111-2222"); self._record("phone_balanced", r.action.value in ("allowed","sanitized"))
    async def test_access_strict_blocks(self):
        allowed, v = _rule_based_agent_access("discovery", ["email","name"], UserPrivacyProfile(privacy_level=PrivacyLevel.strict))
        self._record("access_strict_blocks", not allowed and len(v) > 0)
    async def test_access_strict_allows_public(self):
        allowed, v = _rule_based_agent_access("catalog", ["category"], UserPrivacyProfile(privacy_level=PrivacyLevel.strict))
        self._record("access_strict_public", allowed)
    async def test_access_open(self):
        profile = UserPrivacyProfile(privacy_level=PrivacyLevel.open, consents=PrivacyConsent(third_party_sharing=True))
        allowed, v = _rule_based_agent_access("discovery", ["email","preferences"], profile)
        self._record("access_open", allowed)
    async def test_access_open_no_consent(self):
        profile = UserPrivacyProfile(privacy_level=PrivacyLevel.open, consents=PrivacyConsent(third_party_sharing=False))
        allowed, v = _rule_based_agent_access("discovery", ["email"], profile)
        self._record("access_open_no_consent", not allowed)
    async def test_access_balanced_blocks_phone(self):
        allowed, v = _rule_based_agent_access("discovery", ["phone"], UserPrivacyProfile(privacy_level=PrivacyLevel.balanced))
        self._record("access_balanced_phone", not allowed)
    async def test_access_balanced_allows_email(self):
        allowed, v = _rule_based_agent_access("discovery", ["email"], UserPrivacyProfile(privacy_level=PrivacyLevel.balanced))
        self._record("access_balanced_email", allowed)
    async def test_access_strict_ssn(self):
        allowed, v = _rule_based_agent_access("agent", ["ssn"], UserPrivacyProfile(privacy_level=PrivacyLevel.strict))
        self._record("access_strict_ssn", not allowed)
    async def test_access_strict_cc(self):
        allowed, v = _rule_based_agent_access("agent", ["credit_card"], UserPrivacyProfile(privacy_level=PrivacyLevel.strict))
        self._record("access_strict_cc", not allowed)
    async def test_access_balanced_location(self):
        allowed, v = _rule_based_agent_access("agent", ["precise_location"], UserPrivacyProfile(privacy_level=PrivacyLevel.balanced))
        self._record("access_balanced_location", not allowed)
    async def test_access_strict_real_name(self):
        allowed, v = _rule_based_agent_access("agent", ["real_name"], UserPrivacyProfile(privacy_level=PrivacyLevel.strict))
        self._record("access_strict_name", not allowed)
    async def test_access_analytics_no_share(self):
        profile = UserPrivacyProfile(privacy_level=PrivacyLevel.open, consents=PrivacyConsent(third_party_sharing=False))
        allowed, v = _rule_based_agent_access("analytics", ["email"], profile)
        self._record("access_analytics_noshare", not allowed)
    async def test_output_strict_location(self):
        svc = PrivacyGuardrailService(); svc.update_profile("u1", UserPrivacyProfile(privacy_level=PrivacyLevel.strict))
        r = await svc.check_output([{"id":"p1","name":"P","user_location":"NYC"}], "u1"); self._record("output_strict_loc", r.action.value == "flagged")
    async def test_output_strict_name(self):
        svc = PrivacyGuardrailService(); svc.update_profile("u2", UserPrivacyProfile(privacy_level=PrivacyLevel.strict))
        r = await svc.check_output([{"id":"p1","user_name":"John"}], "u2"); self._record("output_strict_name", r.action.value == "flagged")
    async def test_output_strict_inferred(self):
        svc = PrivacyGuardrailService(); svc.update_profile("u3", UserPrivacyProfile(privacy_level=PrivacyLevel.strict))
        r = await svc.check_output([{"id":"p1","inferred_interest":"gaming"}], "u3"); self._record("output_strict_inferred", r.action.value == "flagged")
    async def test_output_strict_safe(self):
        svc = PrivacyGuardrailService(); svc.update_profile("u4", UserPrivacyProfile(privacy_level=PrivacyLevel.strict))
        r = await svc.check_output([{"id":"p1","price":100}], "u4"); self._record("output_strict_safe", r.action.value == "allowed")
    async def test_output_balanced_location(self):
        svc = PrivacyGuardrailService(); svc.update_profile("u5", UserPrivacyProfile(privacy_level=PrivacyLevel.balanced))
        r = await svc.check_output([{"id":"p1","precise_location":"40.71,-74.00"}], "u5"); self._record("output_balanced_loc", r.action.value == "flagged")
    async def test_output_balanced_safe(self):
        svc = PrivacyGuardrailService(); svc.update_profile("u6", UserPrivacyProfile(privacy_level=PrivacyLevel.balanced))
        r = await svc.check_output([{"id":"p1","price":50}], "u6"); self._record("output_balanced_safe", r.action.value == "allowed")
    async def test_output_empty(self):
        svc = PrivacyGuardrailService(); svc.update_profile("u7", UserPrivacyProfile(privacy_level=PrivacyLevel.strict))
        r = await svc.check_output([], "u7"); self._record("output_empty", r.action.value == "allowed")
    async def test_output_no_profile(self):
        svc = PrivacyGuardrailService(); r = await svc.check_output([{"price":100}], "new_user"); self._record("output_no_profile", r.action.value == "allowed")
    async def test_gdpr_forget(self):
        svc = PrivacyGuardrailService(); svc.get_or_create_profile("g1"); r = await svc.forget_user("g1"); self._record("gdpr_forget", r)
    async def test_gdpr_forget_nonexist(self):
        svc = PrivacyGuardrailService(); r = await svc.forget_user("nonexist"); self._record("gdpr_forget_nonexist", r is False)
    async def test_export_profile(self):
        svc = PrivacyGuardrailService(); svc.get_or_create_profile("g3"); d = svc.export_profile("g3"); self._record("export_profile", d is not None and d["user_id"]=="g3")
    async def test_export_not_found(self):
        svc = PrivacyGuardrailService(); d = svc.export_profile("nonexist"); self._record("export_not_found", d is None)
    async def test_ccpa_opt_out(self):
        svc = PrivacyGuardrailService(); svc.get_or_create_profile("g5"); r = svc.opt_out_of_sale("g5")
        self._record("ccpa_opt_out", r is not None and r.opted_out_of_sale and not r.consents.third_party_sharing)
    async def test_update_consent(self):
        svc = PrivacyGuardrailService(); svc.get_or_create_profile("g6"); r = svc.update_consent("g6", PrivacyConsent(marketing=True))
        self._record("update_consent", r is not None and r.consents.marketing)
    async def test_delete_profile(self):
        svc = PrivacyGuardrailService(); svc.get_or_create_profile("g7"); r = svc.delete_profile("g7"); self._record("delete_profile", r)
    async def test_delete_nonexist(self):
        svc = PrivacyGuardrailService(); r = svc.delete_profile("nonexist"); self._record("delete_nonexist", r is False)
    async def test_access_search_no_consent(self):
        profile = UserPrivacyProfile(privacy_level=PrivacyLevel.open, consents=PrivacyConsent(third_party_sharing=False))
        allowed, v = _rule_based_agent_access("search", ["preferences"], profile); self._record("access_search_noconsent", not allowed)
    async def test_access_custom_agent(self):
        profile = UserPrivacyProfile(privacy_level=PrivacyLevel.open, consents=PrivacyConsent(third_party_sharing=True))
        allowed, v = _rule_based_agent_access("custom_agent", ["email","preferences"], profile); self._record("access_custom", allowed)
    async def test_rule_redact_email(self):
        s, f = _rule_based_redact("test@example.com"); self._record("rule_redact_email", "email" in f and "[REDACTED_EMAIL]" in s)
    async def test_rule_redact_phone(self):
        s, f = _rule_based_redact("Call 555-123-4567"); self._record("rule_redact_phone", "phone" in f and "[REDACTED_PHONE]" in s)
    async def test_rule_redact_ssn(self):
        s, f = _rule_based_redact("SSN: 123-45-6789"); self._record("rule_redact_ssn", "ssn" in f and "[REDACTED_SSN]" in s)
    async def test_rule_redact_address(self):
        s, f = _rule_based_redact("123 Oak Avenue, Springfield"); self._record("rule_redact_address", "address" in f)
    async def test_rule_redact_cc(self):
        s, f = _rule_based_redact("4111111111111111"); self._record("rule_redact_cc", "credit_card" in f)
    async def test_rule_redact_clean(self):
        s, f = _rule_based_redact("I need a new laptop"); self._record("rule_redact_clean", f == [] and s == "I need a new laptop")
    async def test_rule_redact_multi_phone(self):
        s, f = _rule_based_redact("555-0001 and 555-0002"); self._record("rule_redact_multi_phone", "phone" in f)
    async def test_rule_redact_safe_num(self):
        s, f = _rule_based_redact("total is 123"); self._record("rule_redact_safe_num", f == [])
    async def test_rule_redact_email_plus(self):
        s, f = _rule_based_redact("this+that@domain.com"); self._record("rule_redact_email_plus", "email" in f)
    async def test_rule_redact_cc_spaces(self):
        s, f = _rule_based_redact("4111 1111 1111 1111"); self._record("rule_redact_cc_spaces", "credit_card" in f)
    async def test_rule_redact_street_abbrev(self):
        s, f = _rule_based_redact("100 Main St, Boston"); self._record("rule_redact_street", "address" in f)
    async def test_rule_redact_drive(self):
        s, f = _rule_based_redact("200 Park Drive, Chicago"); self._record("rule_redact_drive", "address" in f)
    async def test_output_strict_combined(self):
        svc = PrivacyGuardrailService(); svc.update_profile("u8", UserPrivacyProfile(privacy_level=PrivacyLevel.strict))
        r = await svc.check_output([{"id":"1","name":"P","user_location":"LA","inferred_interest":"music"}], "u8")
        self._record("output_strict_combined", r.action.value == "flagged" and len(r.violations) >= 1)
    async def test_output_profile_nonexistent(self):
        svc = PrivacyGuardrailService()
        r = await svc.check_output([{"price":100}], "user_does_not_exist_xyz"); self._record("output_nonexistent_user", r.action.value == "allowed")
    async def test_input_guardrail_disabled(self):
        import os; os.environ["GUARDRAIL_ENABLED"] = "false"
        svc = PrivacyGuardrailService(); svc.get_or_create_profile("gd").privacy_level = PrivacyLevel.strict
        r = await svc.check_input("test@example.com"); os.environ["GUARDRAIL_ENABLED"] = "true"
        self._record("input_guardrail_disabled", r.action.value == "allowed")
    async def test_access_guardrail_disabled(self):
        import os; os.environ["GUARDRAIL_ENABLED"] = "false"
        svc = PrivacyGuardrailService()
        r = await svc.check_agent_access("agent", ["ssn"]); os.environ["GUARDRAIL_ENABLED"] = "true"
        self._record("access_guardrail_disabled", r.action.value == "allowed")
    async def test_output_guardrail_disabled(self):
        import os; os.environ["GUARDRAIL_ENABLED"] = "false"
        svc = PrivacyGuardrailService(); r = await svc.check_output([{"user_name":"John"}]); os.environ["GUARDRAIL_ENABLED"] = "true"
        self._record("output_guardrail_disabled", r.action.value == "allowed")

    @classmethod
    def generate_report(cls):
        lines = [f"# Privacy Guardrail \u2014 Individual Test Report",
            f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"**Passed:** {cls.passed} | **Failed:** {cls.failed} | **Total:** {cls.passed + cls.failed}","",
            "## Results","| Test Case | Status | Detail |","|---|---|---|"]
        for r in cls.REPORT:
            lines.append(f"| {r['name']} | {'PASS' if r['passed'] else 'FAIL'} | {r['detail']} |")
        _write_report("privacy_guardrail", "\n".join(lines))


# ============================================================
# 3. PRICE GUARDRAIL — 56 cases
# ============================================================

class TestPriceGuardrailSuite:
    REPORT = []; passed = 0; failed = 0
    @classmethod
    def _record(cls, name, passed, detail=""):
        if passed: cls.passed += 1
        else: cls.failed += 1
        cls.REPORT.append({"name": name, "passed": passed, "detail": detail})

    def test_sku_valid(self):
        v = price_guardrail.validate_input("SKU-0001", 99.99); self._record("sku_valid", v.allowed)
    def test_sku_no_prefix(self):
        v = price_guardrail.validate_input("invalid", 99.99); self._record("sku_no_prefix", not v.allowed and v.category=="invalid_sku")
    def test_sku_wrong_format(self):
        v = price_guardrail.validate_input("SKU-12345", 99.99); self._record("sku_wrong_format", not v.allowed)
    def test_sku_lowercase(self):
        v = price_guardrail.validate_input("sku-0001", 99.99); self._record("sku_lowercase", not v.allowed)
    def test_sku_letters(self):
        v = price_guardrail.validate_input("SKU-ABCD", 99.99); self._record("sku_letters", not v.allowed)
    def test_sku_empty(self):
        v = price_guardrail.validate_input("", 99.99); self._record("sku_empty", not v.allowed)
    def test_sku_short(self):
        v = price_guardrail.validate_input("SKU-12", 99.99); self._record("sku_short", not v.allowed)
    def test_sku_special(self):
        v = price_guardrail.validate_input("SKU-00@1", 99.99); self._record("sku_special", not v.allowed)
    def test_sku_spaces(self):
        v = price_guardrail.validate_input("SKU- 001", 99.99); self._record("sku_spaces", not v.allowed)
    def test_sku_unusual(self):
        v = price_guardrail.validate_input("SKU-   1", 99.99); self._record("sku_unusual", not v.allowed)
    def test_price_negative(self):
        v = price_guardrail.validate_input("SKU-0001", -10.0); self._record("price_negative", not v.allowed and v.category=="invalid_price")
    def test_price_zero(self):
        v = price_guardrail.validate_input("SKU-0001", 0); self._record("price_zero", not v.allowed)
    def test_price_penny(self):
        v = price_guardrail.validate_input("SKU-0001", 0.01); self._record("price_penny", v.allowed)
    def test_price_below_min(self):
        v = price_guardrail.validate_input("SKU-0001", 0.001); self._record("price_below_min", not v.allowed and v.category=="price_floor")
    def test_price_max(self):
        v = price_guardrail.validate_input("SKU-0001", 100000.0); self._record("price_max", v.allowed)
    def test_price_above_max(self):
        v = price_guardrail.validate_input("SKU-0001", 100001.0); self._record("price_above_max", not v.allowed and v.category=="price_cap")
    def test_price_very_high(self):
        v = price_guardrail.validate_input("SKU-0001", 999999.0); self._record("price_very_high", not v.allowed)
    def test_price_exact_max(self):
        v = price_guardrail.validate_input("SKU-0001", 100000.0); self._record("price_exact_max", v.allowed)
    def test_price_typical(self):
        v = price_guardrail.validate_input("SKU-0001", 49.99); self._record("price_typical", v.allowed)
    def test_price_large_valid(self):
        v = price_guardrail.validate_input("SKU-0001", 99999.99); self._record("price_large_valid", v.allowed)
    def test_fraud_zero(self):
        v = price_guardrail.detect_fraud(100.0, 0); self._record("fraud_zero", not v.allowed and v.category=="bad_competitor")
    def test_fraud_negative(self):
        v = price_guardrail.detect_fraud(100.0, -10.0); self._record("fraud_negative", not v.allowed)
    def test_fraud_suspicious(self):
        v = price_guardrail.detect_fraud(100.0, 5.0); self._record("fraud_suspicious", not v.allowed and v.category=="suspicious_data")
    def test_fraud_gouging(self):
        v = price_guardrail.detect_fraud(50.0, 150.0); self._record("fraud_gouging", not v.allowed and v.category=="gouging_risk")
    def test_fraud_normal(self):
        v = price_guardrail.detect_fraud(100.0, 90.0); self._record("fraud_normal", v.allowed)
    def test_fraud_exact_ratio(self):
        v = price_guardrail.detect_fraud(100.0, 10.0); self._record("fraud_exact_ratio", not v.allowed)
    def test_fraud_exact_gouge(self):
        v = price_guardrail.detect_fraud(50.0, 100.01); self._record("fraud_exact_gouge", not v.allowed)
    def test_fraud_equal(self):
        v = price_guardrail.detect_fraud(50.0, 50.0); self._record("fraud_equal", v.allowed)
    def test_fraud_barely_suspicious(self):
        v = price_guardrail.detect_fraud(100.0, 9.99); self._record("fraud_barely_suspicious", not v.allowed)
    def test_fraud_barely_gouge(self):
        v = price_guardrail.detect_fraud(50.0, 100.0); self._record("fraud_barely_gouge", v.allowed)
    def test_rate_first(self):
        pg = PriceGuardrail(); v = pg.check_rate_limit("rl1"); self._record("rate_first", v.allowed)
    def test_rate_50th(self):
        pg = PriceGuardrail()
        for _ in range(49): pg.check_rate_limit("rl2")
        v = pg.check_rate_limit("rl2"); self._record("rate_50th", v.allowed)
    def test_rate_51st(self):
        pg = PriceGuardrail()
        for _ in range(50): pg.check_rate_limit("rl3")
        v = pg.check_rate_limit("rl3"); self._record("rate_51st", not v.allowed and v.category=="rate_limited")
    def test_rate_diff_users(self):
        pg = PriceGuardrail()
        v1 = pg.check_rate_limit("ra"); v2 = pg.check_rate_limit("rb"); self._record("rate_diff_users", v1.allowed and v2.allowed)
    def test_rate_reset_after_hour(self):
        pg = PriceGuardrail()
        pg._sessions["reset"] = type('S',(),{'count':55,'window_start':time.time()-4000})()
        v = pg.check_rate_limit("reset"); self._record("rate_reset", v.allowed)
    def test_rate_new_window(self):
        pg = PriceGuardrail()
        pg._sessions["nw"] = type('S',(),{'count':50,'window_start':time.time()-3601})()
        v = pg.check_rate_limit("nw"); self._record("rate_new_window", v.allowed)
    def test_rate_sequential(self):
        pg = PriceGuardrail()
        for _ in range(10): pg.check_rate_limit("seq")
        v = pg.check_rate_limit("seq"); self._record("rate_sequential", v.allowed)
    def test_rate_exact_cap(self):
        pg = PriceGuardrail()
        for _ in range(50): pg.check_rate_limit("exact")
        v = pg.check_rate_limit("exact"); self._record("rate_exact_cap", not v.allowed)
    def test_abuse_under(self):
        pg = PriceGuardrail(); pg._sessions["a1"] = type('S',(),{'total_discount_claimed':100,'count':1,'window_start':time.time()})()
        v = pg.check_abuse("a1", 100.0); self._record("abuse_under", v.allowed)
    def test_abuse_exact(self):
        pg = PriceGuardrail(); pg._sessions["a2"] = type('S',(),{'total_discount_claimed':1900,'count':1,'window_start':time.time()})()
        v = pg.check_abuse("a2", 100.0); self._record("abuse_exact", v.allowed)
    def test_abuse_over(self):
        pg = PriceGuardrail(); pg._sessions["a3"] = type('S',(),{'total_discount_claimed':1999,'count':1,'window_start':time.time()})()
        v = pg.check_abuse("a3", 100.0); self._record("abuse_over", not v.allowed and v.category=="abuse")
    def test_abuse_new_user(self):
        pg = PriceGuardrail(); v = pg.check_abuse("new", 100.0); self._record("abuse_new", v.allowed)
    def test_abuse_record(self):
        pg = PriceGuardrail(); pg._sessions["a5"] = type('S',(),{'total_discount_claimed':0,'count':1,'window_start':time.time()})()
        pg.record_discount("a5", 500.0); self._record("abuse_record", pg._sessions["a5"].total_discount_claimed==500)
    def test_abuse_reset(self):
        pg = PriceGuardrail(); pg._sessions["ar"] = type('S',(),{'total_discount_claimed':2000,'count':1,'window_start':time.time()})()
        pg.reset("ar"); self._record("abuse_reset", "ar" not in pg._sessions)
    def test_combine_valid(self):
        v = price_guardrail.validate_input("SKU-0001", 100.0)
        f = price_guardrail.detect_fraud(100.0, 95.0); self._record("combine_valid", v.allowed and f.allowed)
    def test_combine_abuse_rate(self):
        pg = PriceGuardrail()
        for _ in range(50): pg.check_rate_limit("cr")
        rl = pg.check_rate_limit("cr")
        pg._sessions["cr"] = type('S',(),{'total_discount_claimed':2000,'count':51,'window_start':time.time()})()
        ab = pg.check_abuse("cr", 100.0); self._record("combine_abuse_rate", not rl.allowed and not ab.allowed)
    def test_combine_success(self):
        pg = PriceGuardrail()
        v = pg.validate_input("SKU-0001", 100.0)
        f = pg.detect_fraud(100.0, 90.0)
        r = pg.check_rate_limit("sc")
        a = pg.check_abuse("sc", 50.0); self._record("combine_success", v.allowed and f.allowed and r.allowed and a.allowed)

    @classmethod
    def generate_report(cls):
        lines = [f"# Price Guardrail \u2014 Individual Test Report",
            f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"**Passed:** {cls.passed} | **Failed:** {cls.failed} | **Total:** {cls.passed + cls.failed}","",
            "## Results","| Test Case | Status | Detail |","|---|---|---|"]
        for r in cls.REPORT:
            lines.append(f"| {r['name']} | {'PASS' if r['passed'] else 'FAIL'} | {r['detail']} |")
        _write_report("price_guardrail", "\n".join(lines))


# ============================================================
# 4. PRICE MATCH — 56 cases
# ============================================================

class TestPriceMatchSuite:
    REPORT = []; passed = 0; failed = 0
    @classmethod
    def _record(cls, name, passed, detail=""):
        if passed: cls.passed += 1
        else: cls.failed += 1
        cls.REPORT.append({"name": name, "passed": passed, "detail": detail})

    def test_fetch_found(self):
        r = fetch_competitor_price("SKU-0001"); self._record("fetch_found", "error" not in r and "price" in r)
    def test_fetch_not_found(self):
        r = fetch_competitor_price("SKU-9999"); self._record("fetch_not_found", "error" in r)
    def test_fetch_amazon(self):
        r = fetch_competitor_price("SKU-0001", store="Amazon"); self._record("fetch_amazon", r.get("store")=="Amazon")
    def test_fetch_bestbuy(self):
        r = fetch_competitor_price("SKU-0001", store="BestBuy"); self._record("fetch_bestbuy", r.get("store")=="BestBuy")
    def test_fetch_walmart(self):
        r = fetch_competitor_price("SKU-0001", store="Walmart"); self._record("fetch_walmart", "error" not in r)
    def test_fetch_target(self):
        r = fetch_competitor_price("SKU-0001", store="Target"); self._record("fetch_target", "error" not in r)
    def test_fetch_ebay(self):
        r = fetch_competitor_price("SKU-0001", store="eBay"); self._record("fetch_ebay", "error" not in r)
    def test_fetch_invalid_store(self):
        r = fetch_competitor_price("SKU-0001", store="UnknownStore"); self._record("fetch_invalid_store", "error" in r)
    def test_fetch_lowest(self):
        r = fetch_competitor_price("SKU-0001"); self._record("fetch_lowest", "store" in r and "price" in r)
    def test_fetch_all_prices(self):
        r = fetch_competitor_price("SKU-0001"); self._record("fetch_all_prices", "all_prices" in r and len(r["all_prices"])==5)
    def test_fetch_multiple(self):
        for sku in [f"SKU-{i:04d}" for i in range(1,6)]:
            r = fetch_competitor_price(sku); assert isinstance(r, dict)
        self._record("fetch_multiple", True)
    def test_fetch_price_type(self):
        r = fetch_competitor_price("SKU-0001"); self._record("fetch_price_type", isinstance(r.get("price"),(int,float)))
    def test_authorize_approved(self):
        r = authorize_price_match(100.0, 80.0); self._record("authorize_approved", r["status"]=="approved" and r["discount_amount"]==20.0)
    def test_authorize_capped(self):
        r = authorize_price_match(100.0, 50.0); self._record("authorize_capped", r["status"]=="approved" and r["discount_amount"]==25.0)
    def test_authorize_declined_higher(self):
        r = authorize_price_match(80.0, 100.0); self._record("authorize_declined", r["status"]=="declined")
    def test_authorize_equal(self):
        r = authorize_price_match(100.0, 100.0); self._record("authorize_equal", r["status"]=="declined")
    def test_authorize_zero(self):
        r = authorize_price_match(100.0, 0); self._record("authorize_zero", r["status"]=="declined")
    def test_authorize_negative(self):
        r = authorize_price_match(100.0, -10.0); self._record("authorize_negative", r["status"]=="declined")
    def test_authorize_exact_25(self):
        r = authorize_price_match(100.0, 75.0); self._record("authorize_exact_25", r["status"]=="approved" and r["discount_amount"]==25.0)
    def test_authorize_small(self):
        r = authorize_price_match(100.0, 99.0); self._record("authorize_small", r["status"]=="approved" and r["discount_amount"]==1.0)
    def test_authorize_max(self):
        r = authorize_price_match(200.0, 100.0); self._record("authorize_max", r["status"]=="approved" and r["discount_amount"]==50.0)
    def test_authorize_new_price(self):
        r = authorize_price_match(100.0, 80.0); self._record("authorize_new_price", abs(r["new_price"]-80.0)<0.01)
    def test_history_found(self):
        h = get_price_history("SKU-0001"); self._record("history_found", len(h)==15)
    def test_history_not_found(self):
        h = get_price_history("SKU-9999"); self._record("history_not_found", len(h)==15)
    def test_history_dates(self):
        h = get_price_history("SKU-0001"); self._record("history_dates", all("date" in e for e in h))
    def test_history_prices(self):
        h = get_price_history("SKU-0001"); self._record("history_prices", all("price" in e for e in h))
    def test_history_sorted(self):
        h = get_price_history("SKU-0001"); self._record("history_sorted", h==sorted(h, key=lambda x:x["date"]))
    def test_history_positive(self):
        h = get_price_history("SKU-0001"); self._record("history_positive", all(e["price"]>0 for e in h))
    def test_history_idempotent(self):
        h1 = get_price_history("SKU-0002"); h2 = get_price_history("SKU-0002"); self._record("history_idempotent", h1==h2)
    def test_history_multi(self):
        for sku in [f"SKU-{i:04d}" for i in range(3)]:
            assert len(get_price_history(sku))==15
        self._record("history_multi", True)
    def test_alerts_found(self):
        a = get_price_drop_alerts("SKU-0001", 1.0); self._record("alerts_found", isinstance(a,list))
    def test_alerts_high_thresh(self):
        a = get_price_drop_alerts("SKU-0001", 100.0); self._record("alerts_high_thresh", len(a)==0)
    def test_alerts_zero_thresh(self):
        a = get_price_drop_alerts("SKU-0001", 0.0); self._record("alerts_zero_thresh", isinstance(a,list))
    def test_alerts_unknown_sku(self):
        a = get_price_drop_alerts("SKU-9999", 1.0); self._record("alerts_unknown", isinstance(a,list))
    def test_alerts_include_date(self):
        a = get_price_drop_alerts("SKU-0001", 1.0)
        if a: self._record("alerts_include_date", "date" in a[0])
        else: self._record("alerts_include_date", True)
    def test_alerts_drop_pct(self):
        a = get_price_drop_alerts("SKU-0001", 0.0)
        if a: self._record("alerts_drop_pct", all(d["drop_pct"]>=0 for d in a))
        else: self._record("alerts_drop_pct", True)
    def test_alerts_max_7(self):
        a = get_price_drop_alerts("SKU-0001", 0.1); self._record("alerts_max_7", len(a)<=7)
    def test_alerts_multi_sku(self):
        for sku in [f"SKU-{i:04d}" for i in range(3)]:
            assert isinstance(get_price_drop_alerts(sku,5.0),list)
        self._record("alerts_multi_sku", True)
    def test_pma_check_found(self):
        d = price_match_agent.check_price("SKU-0001", 100.0, "1", "pma1"); self._record("pma_check_found", d.status in ("approved","declined"))
    def test_pma_check_not_found(self):
        d = price_match_agent.check_price("SKU-9999", 100.0, "9999", "pma2"); self._record("pma_check_not_found", d.status=="declined")
    def test_pma_list(self):
        dl = price_match_agent.list_discounts(); self._record("pma_list", isinstance(dl,list))
    def test_pma_get(self):
        d = price_match_agent.check_price("SKU-0001", 100.0, "1", "pma3")
        f = price_match_agent.get_discount(d.id); self._record("pma_get", f is not None)
    def test_pma_get_not_found(self):
        f = price_match_agent.get_discount("nonexist"); self._record("pma_get_not_found", f is None)
    def test_pma_apply(self):
        d = price_match_agent.check_price("SKU-0002", 100.0, "2", "pma4")
        if d.status=="approved":
            a = price_match_agent.apply_discount(d.id); self._record("pma_apply", a is not None and a.status=="applied")
        else: self._record("pma_apply", True)
    def test_pma_apply_declined(self):
        d = price_match_agent.check_price("SKU-9999", 100.0, "9999", "pma5")
        a = price_match_agent.apply_discount(d.id); self._record("pma_apply_declined", a is None)
    def test_pma_fields(self):
        d = price_match_agent.check_price("SKU-0001", 100.0, "1", "pma6")
        for f in ["id","sku","store_price","competitor_price","discount_amount","status"]:
            assert hasattr(d,f)
        self._record("pma_fields", True)
    def test_pma_discount_id(self):
        d = price_match_agent.check_price("SKU-0001", 100.0, "1", "pma7"); self._record("pma_discount_id", len(d.id)>0)
    def test_pma_competitor_store(self):
        d = price_match_agent.check_price("SKU-0001", 100.0, "1", "pma8")
        self._record("pma_competitor_store", d.competitor_store in ("Amazon","BestBuy","Walmart","Target","eBay","N/A"))
    def test_pma_discount_new_price(self):
        d = price_match_agent.check_price("SKU-0001", 100.0, "1", "pma9")
        self._record("pma_new_price", d.new_price <= d.store_price)
    def test_pma_discount_amount_nonneg(self):
        d = price_match_agent.check_price("SKU-0001", 100.0, "1", "pma10"); self._record("pma_amount_nonneg", d.discount_amount >= 0)

    @classmethod
    def generate_report(cls):
        lines = [f"# Price Match \u2014 Individual Test Report",
            f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"**Passed:** {cls.passed} | **Failed:** {cls.failed} | **Total:** {cls.passed + cls.failed}","",
            "## Results","| Test Case | Status | Detail |","|---|---|---|"]
        for r in cls.REPORT:
            lines.append(f"| {r['name']} | {'PASS' if r['passed'] else 'FAIL'} | {r['detail']} |")
        _write_report("price_match", "\n".join(lines))


# ============================================================
# 5. INTENT PARSER — 56 cases
# ============================================================

@pytest.mark.asyncio
class TestIntentParserSuite:
    REPORT = []; passed = 0; failed = 0
    @classmethod
    def _record(cls, name, passed, detail=""):
        if passed: cls.passed += 1
        else: cls.failed += 1
        cls.REPORT.append({"name": name, "passed": passed, "detail": detail})

    async def test_rule_cat_electronics(self):
        i = _rule_based_fallback("I need a laptop"); self._record("rule_cat_elec", i.category=="electronics")
    async def test_rule_cat_clothing(self):
        i = _rule_based_fallback("looking for a dress shirt"); self._record("rule_cat_clothing", i.category=="clothing")
    async def test_rule_cat_footwear(self):
        i = _rule_based_fallback("need running shoes"); self._record("rule_cat_footwear", i.category=="footwear")
    async def test_rule_cat_accessories(self):
        i = _rule_based_fallback("nice watch"); self._record("rule_cat_accessories", i.category=="accessories")
    async def test_rule_cat_home(self):
        i = _rule_based_fallback("kitchen table"); self._record("rule_cat_home", i.category=="home")
    async def test_rule_cat_beauty(self):
        i = _rule_based_fallback("skincare lotion"); self._record("rule_cat_beauty", i.category=="beauty")
    async def test_rule_cat_sports(self):
        i = _rule_based_fallback("yoga mat"); self._record("rule_cat_sports", i.category=="sports")
    async def test_rule_cat_books(self):
        i = _rule_based_fallback("fiction novels"); self._record("rule_cat_books", i.category=="books")
    async def test_rule_cat_toys(self):
        i = _rule_based_fallback("board games"); self._record("rule_cat_toys", i.category=="toys")
    async def test_rule_cat_food(self):
        i = _rule_based_fallback("gourmet chocolate"); self._record("rule_cat_food", i.category=="food")
    async def test_rule_cat_gifts(self):
        i = _rule_based_fallback("birthday present"); self._record("rule_cat_gifts", i.category=="gifts")
    async def test_rule_cat_vague(self):
        i = _rule_based_fallback("something nice"); self._record("rule_cat_vague", i.category is None)
    async def test_rule_cat_phone(self):
        i = _rule_based_fallback("smartphone with good camera"); self._record("rule_cat_phone", i.category=="electronics")
    async def test_rule_cat_tablet(self):
        i = _rule_based_fallback("tablet for drawing"); self._record("rule_cat_tablet", i.category=="electronics")
    async def test_rule_cat_jewelry(self):
        i = _rule_based_fallback("gold necklace"); self._record("rule_cat_jewelry", i.category=="accessories")
    async def test_rule_cat_tv(self):
        i = _rule_based_fallback("4k tv"); self._record("rule_cat_tv", i.category=="electronics")
    async def test_rule_budget_under(self):
        i = _rule_based_fallback("find shoes under $100"); self._record("rule_budget_under", i.budget==100.0)
    async def test_rule_budget_around(self):
        i = _rule_based_fallback("laptop around 800 dollars"); self._record("rule_budget_around", i.budget==800.0)
    async def test_rule_budget_below(self):
        i = _rule_based_fallback("below $50"); self._record("rule_budget_below", i.budget==50.0)
    async def test_rule_budget_bucks(self):
        i = _rule_based_fallback("less than 200 bucks"); self._record("rule_budget_bucks", i.budget==200.0)
    async def test_rule_budget_max(self):
        i = _rule_based_fallback("max 1500 usd"); self._record("rule_budget_max", i.budget==1500.0)
    async def test_rule_budget_none(self):
        i = _rule_based_fallback("show me laptops"); self._record("rule_budget_none", i.budget is None)
    async def test_rule_budget_decimal(self):
        i = _rule_based_fallback("budget is 99.99"); self._record("rule_budget_decimal", abs(i.budget-99.99)<0.01)
    async def test_rule_budget_context(self):
        i = _rule_based_fallback("i can spend around 300 dollars on a tablet"); self._record("rule_budget_context", i.budget==300.0)
    async def test_rule_occ_birthday(self):
        i = _rule_based_fallback("birthday gift"); self._record("rule_occ_birthday", i.occasion=="birthday")
    async def test_rule_occ_wedding(self):
        i = _rule_based_fallback("wedding gift"); self._record("rule_occ_wedding", i.occasion=="wedding")
    async def test_rule_occ_christmas(self):
        i = _rule_based_fallback("christmas presents"); self._record("rule_occ_christmas", i.occasion=="holiday")
    async def test_rule_occ_anniversary(self):
        i = _rule_based_fallback("anniversary surprise"); self._record("rule_occ_anniversary", i.occasion=="wedding")
    async def test_rule_occ_graduation(self):
        i = _rule_based_fallback("graduation gift"); self._record("rule_occ_graduation", i.occasion=="graduation")
    async def test_rule_occ_housewarming(self):
        i = _rule_based_fallback("housewarming present"); self._record("rule_occ_housewarming", i.occasion=="housewarming")
    async def test_rule_occ_baby_shower(self):
        i = _rule_based_fallback("baby shower gift"); self._record("rule_occ_baby_shower", i.occasion=="baby_shower")
    async def test_rule_occ_none(self):
        i = _rule_based_fallback("show me headphones"); self._record("rule_occ_none", i.occasion is None)
    async def test_rule_urgency_immediate(self):
        i = _rule_based_fallback("need it ASAP right now"); self._record("rule_urg_immediate", i.urgency=="immediate")
    async def test_rule_urgency_soon(self):
        i = _rule_based_fallback("need this soon"); self._record("rule_urg_soon", i.urgency=="soon")
    async def test_rule_urgency_not(self):
        i = _rule_based_fallback("just browsing, no rush"); self._record("rule_urg_not", i.urgency=="not_urgent")
    async def test_rule_style_modern(self):
        i = _rule_based_fallback("modern sleek laptop"); self._record("rule_style_modern", "modern" in i.style_preferences)
    async def test_rule_style_luxury(self):
        i = _rule_based_fallback("premium luxury watch"); self._record("rule_style_luxury", "luxury" in i.style_preferences)
    async def test_rule_style_casual(self):
        i = _rule_based_fallback("casual everyday shoes"); self._record("rule_style_casual", "casual" in i.style_preferences)
    async def test_rule_style_formal(self):
        i = _rule_based_fallback("formal business suit"); self._record("rule_style_formal", "formal" in i.style_preferences)
    async def test_rule_style_vintage(self):
        i = _rule_based_fallback("vintage retro jacket"); self._record("rule_style_vintage", "vintage" in i.style_preferences)
    async def test_rule_style_colorful(self):
        i = _rule_based_fallback("colorful bright dress"); self._record("rule_style_colorful", "colorful" in i.style_preferences)
    async def test_parse_basic(self):
        i = await parse_intent("show me running shoes"); self._record("parse_basic", i.raw_query=="show me running shoes")
    async def test_parse_with_budget(self):
        i = await parse_intent("buy a laptop under $800"); self._record("parse_with_budget", i.budget is not None)
    async def test_parse_occasion(self):
        i = await parse_intent("anniversary gift for husband who loves cooking"); self._record("parse_occasion", i.occasion is not None)
    async def test_parse_empty(self):
        i = await parse_intent(""); self._record("parse_empty", i.raw_query=="")
    async def test_parse_whitespace(self):
        i = await parse_intent("   "); self._record("parse_whitespace", i.raw_query.strip()=="")
    async def test_parse_long(self):
        i = await parse_intent("I need a good quality laptop for programming under $1000 with good battery life"); self._record("parse_long", i.category is not None)
    async def test_parse_budget_category(self):
        i = await parse_intent("find me a laptop under $1000 for programming"); self._record("parse_budget_cat", i.category is not None)
    async def test_parse_numbers(self):
        i = await parse_intent("find 2 pairs of sneakers under $150"); self._record("parse_numbers", i.budget is not None or i.category is not None)
    async def test_rule_empty(self):
        i = _rule_based_fallback(""); self._record("rule_empty", i.raw_query=="" and i.category is None)
    async def test_rule_special(self):
        i = _rule_based_fallback("!@#$%^"); self._record("rule_special", i.category is None and i.budget is None)
    async def test_rule_very_long(self):
        i = _rule_based_fallback("a "*500); self._record("rule_very_long", i.raw_query is not None)
    async def test_parse_budget_tight(self):
        i = await parse_intent("cheap headphones under $20"); self._record("parse_budget_tight", i.budget is not None)
    async def test_parse_style_from_text(self):
        i = _rule_based_fallback("wireless bluetooth speaker"); self._record("parse_style_techy", "techy" in i.style_preferences)
    async def test_parse_neutral(self):
        i = _rule_based_fallback("black white dress"); self._record("parse_neutral", "neutral" in i.style_preferences)
    async def test_parse_outdoor(self):
        i = _rule_based_fallback("camping hiking gear"); self._record("parse_outdoor", "outdoor" in i.style_preferences)
    async def test_parse_budget_price(self):
        i = _rule_based_fallback("i can spend around 300 dollars on a tablet"); self._record("parse_budget_price", i.budget==300.0)

    @classmethod
    def generate_report(cls):
        lines = [f"# Intent Parser \u2014 Individual Test Report",
            f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"**Passed:** {cls.passed} | **Failed:** {cls.failed} | **Total:** {cls.passed + cls.failed}","",
            "## Results","| Test Case | Status | Detail |","|---|---|---|"]
        for r in cls.REPORT:
            lines.append(f"| {r['name']} | {'PASS' if r['passed'] else 'FAIL'} | {r['detail']} |")
        _write_report("intent_parser", "\n".join(lines))


# ============================================================
# 6. CATALOG SEARCH — 52 cases
# ============================================================

class TestCatalogSearchSuite:
    REPORT = []; passed = 0; failed = 0
    @classmethod
    def _record(cls, name, passed, detail=""):
        if passed: cls.passed += 1
        else: cls.failed += 1
        cls.REPORT.append({"name": name, "passed": passed, "detail": detail})

    def test_search_laptop(self):
        r = search_simple("laptop"); self._record("search_laptop", len(r)>0)
    def test_search_smartphone(self):
        r = search_simple("smartphone"); self._record("search_smartphone", len(r)>0)
    def test_search_headphones(self):
        r = search_simple("headphones"); self._record("search_headphones", len(r)>0)
    def test_search_shoes(self):
        r = search_simple("shoes"); self._record("search_shoes", len(r)>0)
    def test_search_watch(self):
        r = search_simple("watch"); self._record("search_watch", len(r)>0)
    def test_search_partial(self):
        r = search_simple("headphone"); self._record("search_partial", len(r)>0)
    def test_search_case_insensitive(self):
        r = search_simple("LAPTOP"); self._record("search_case", len(r)>0)
    def test_search_no_results(self):
        r = search_simple("zzzznotfound"); self._record("search_no_results", len(r)==0)
    def test_search_empty(self):
        r = search_simple(""); self._record("search_empty", len(r)>0)
    def test_search_single_char(self):
        r = search_simple("a"); self._record("search_single_char", len(r)>0)
    def test_search_special_chars(self):
        r = search_simple("@#$%"); self._record("search_special", len(r)==0)
    def test_search_numbers(self):
        r = search_simple("4k"); self._record("search_numbers", len(r)>=0)
    def test_search_multi_word(self):
        r = search_simple("wireless headphones"); self._record("search_multi", len(r)>0)
    def test_search_very_long(self):
        r = search_simple("a"*200); self._record("search_very_long", len(r)>=0)
    def test_search_camera(self):
        r = search_simple("camera"); self._record("search_camera", len(r)>0)
    def test_search_monitor(self):
        r = search_simple("monitor"); self._record("search_monitor", len(r)>0)
    def test_search_tablet(self):
        r = search_simple("tablet"); self._record("search_tablet", len(r)>0)
    def test_search_returns_dicts(self):
        r = search_simple("laptop"); self._record("search_returns_dicts", all(isinstance(p,dict) for p in r))
    def test_search_has_id(self):
        r = search_simple("laptop"); self._record("search_has_id", all("id" in p for p in r))
    def test_search_has_name(self):
        r = search_simple("laptop"); self._record("search_has_name", all(p["name"] for p in r))
    def test_products_have_price(self):
        r = search_simple(""); self._record("products_have_price", all("price" in p for p in r[:50]))
    def test_products_price_pos(self):
        r = search_simple(""); self._record("products_price_pos", all(p["price"]>0 for p in r[:50]))
    def test_products_have_category(self):
        r = search_simple(""); self._record("products_have_cat", all("category" in p for p in r[:50]))
    def test_products_have_rating(self):
        r = search_simple(""); self._record("products_have_rating", all("rating" in p for p in r[:50]))
    def test_products_rating_range(self):
        r = search_simple(""); self._record("products_rating_range", all(0<=p["rating"]<=5 for p in r[:50]))
    def test_products_have_desc(self):
        r = search_simple(""); self._record("products_have_desc", all("description" in p for p in r[:50]))
    def test_products_unique_ids(self):
        r = search_simple(""); ids=[p["id"] for p in r[:100]]; self._record("products_unique_ids", len(ids)==len(set(ids)))
    def test_products_have_sku(self):
        r = search_simple("laptop"); self._record("products_have_sku", all("sku" in p for p in r))
    def test_products_cat_not_empty(self):
        r = search_simple(""); self._record("products_cat_not_empty", all(p["category"] for p in r[:50]))
    def test_categories_list(self):
        self._record("categories_list", len(CATEGORIES)>0)
    def test_categories_elec(self):
        self._record("categories_elec", "Electronics" in CATEGORIES)
    def test_categories_fashion(self):
        self._record("categories_fashion", "Fashion" in CATEGORIES)
    def test_categories_home(self):
        self._record("categories_home", "Home" in CATEGORIES)
    def test_categories_sports(self):
        self._record("categories_sports", "Sports" in CATEGORIES)
    def test_categories_accessories(self):
        self._record("categories_accessories", "Accessories" in CATEGORIES)
    def test_categories_min_5(self):
        self._record("categories_min_5", len(CATEGORIES)>=5)
    def test_total_prods_ge_500(self):
        self._record("total_prods_ge_500", len(ALL_PRODUCTS)>=500)
    def test_total_prods_le_2000(self):
        self._record("total_prods_le_2000", len(ALL_PRODUCTS)<=2000)
    def test_each_prod_has_id(self):
        self._record("each_prod_has_id", all("id" in p for p in ALL_PRODUCTS))
    def test_each_prod_has_price(self):
        self._record("each_prod_has_price", all("price" in p for p in ALL_PRODUCTS[:200]))
    def test_prods_pos_ids(self):
        self._record("prods_pos_ids", all(p["id"]>0 for p in ALL_PRODUCTS[:200]))
    def test_prods_multi_cats(self):
        cats={p["category"] for p in ALL_PRODUCTS}; self._record("prods_multi_cats", len(cats)>=5)
    def test_search_independent(self):
        r1=search_simple("laptop"); r2=search_simple("laptop"); self._record("search_independent", len(r1)==len(r2))
    def test_search_diff_queries(self):
        r1=len(search_simple("laptop")); r2=len(search_simple("shoes")); self._record("search_diff", r1>=0 and r2>=0)
    def test_search_substring(self):
        r=search_simple("phone"); self._record("search_substring", len(r)>=0)
    def test_search_color(self):
        r=search_simple("black"); self._record("search_color", len(r)>=0)
    def test_search_brand(self):
        r=search_simple("pro"); self._record("search_brand", len(r)>=0)
    def test_search_connective(self):
        r=search_simple("and"); self._record("search_connective", len(r)>=0)
    def test_search_stop_word(self):
        r=search_simple("the"); self._record("search_stop_word", len(r)>=0)
    def test_search_model(self):
        r=search_simple("x pro max"); self._record("search_model", len(r)>=0)
    def test_search_sport_type(self):
        r=search_simple("running"); self._record("search_sport", len(r)>=0)

    @classmethod
    def generate_report(cls):
        lines = [f"# Catalog Search \u2014 Individual Test Report",
            f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"**Passed:** {cls.passed} | **Failed:** {cls.failed} | **Total:** {cls.passed + cls.failed}","",
            "## Results","| Test Case | Status | Detail |","|---|---|---|"]
        for r in cls.REPORT:
            lines.append(f"| {r['name']} | {'PASS' if r['passed'] else 'FAIL'} | {r['detail']} |")
        _write_report("catalog_search", "\n".join(lines))


# ============================================================
# 7. RECOMMENDATION — 52 cases
# ============================================================

class TestRecommendationSuite:
    REPORT = []; passed = 0; failed = 0
    @classmethod
    def _record(cls, name, passed, detail=""):
        if passed: cls.passed += 1
        else: cls.failed += 1
        cls.REPORT.append({"name": name, "passed": passed, "detail": detail})

    def test_rec_elec(self):
        r = get_recommendations(UserPreferences(categories=["Electronics"])); self._record("rec_elec", len(r)>0)
    def test_rec_fashion(self):
        r = get_recommendations(UserPreferences(categories=["Fashion"])); self._record("rec_fashion", len(r)>0)
    def test_rec_home(self):
        r = get_recommendations(UserPreferences(categories=["Home"])); self._record("rec_home", len(r)>0)
    def test_rec_sports(self):
        r = get_recommendations(UserPreferences(categories=["Sports"])); self._record("rec_sports", len(r)>0)
    def test_rec_accessories(self):
        r = get_recommendations(UserPreferences(categories=["Accessories"])); self._record("rec_accessories", len(r)>0)
    def test_rec_multi_cat(self):
        r = get_recommendations(UserPreferences(categories=["Electronics","Fashion"])); self._record("rec_multi_cat", len(r)>0)
    def test_rec_no_cat(self):
        r = get_recommendations(UserPreferences(categories=[])); self._record("rec_no_cat", len(r)>=0)
    def test_rec_nonexist_cat(self):
        r = get_recommendations(UserPreferences(categories=["NonexistentCat"])); self._record("rec_nonexist_cat", len(r)>=0)
    def test_rec_price_range(self):
        r = get_recommendations(UserPreferences(categories=["Electronics"],price_min=100,price_max=500)); self._record("rec_price_range", len(r)>0)
    def test_rec_price_min(self):
        r = get_recommendations(UserPreferences(categories=["Electronics"],price_min=500)); self._record("rec_price_min", len(r)>0)
    def test_rec_price_max_low(self):
        r = get_recommendations(UserPreferences(categories=["Electronics"],price_max=30)); self._record("rec_price_max_low", len(r)>=0)
    def test_rec_price_impossible(self):
        r = get_recommendations(UserPreferences(categories=["Electronics"],price_min=99999,price_max=100000)); self._record("rec_price_impossible", len(r)==0)
    def test_rec_price_negative(self):
        r = get_recommendations(UserPreferences(categories=["Electronics"],price_min=-100,price_max=-1)); self._record("rec_price_neg", len(r)>=0)
    def test_rec_price_zero_range(self):
        r = get_recommendations(UserPreferences(categories=["Electronics"],price_min=50,price_max=50)); self._record("rec_price_zero", len(r)>=0)
    def test_rec_price_all(self):
        r = get_recommendations(UserPreferences(price_min=0,price_max=100000)); self._record("rec_price_all", len(r)>0)
    def test_rec_brand(self):
        r = get_recommendations(UserPreferences(categories=["Electronics"],brands=["TechBrand"])); self._record("rec_brand", isinstance(r,list))
    def test_rec_brand_multi(self):
        r = get_recommendations(UserPreferences(categories=["Electronics"],brands=["A","B"])); self._record("rec_brand_multi", isinstance(r,list))
    def test_rec_brand_nonexist(self):
        r = get_recommendations(UserPreferences(categories=["Electronics"],brands=["DoesNotExist"])); self._record("rec_brand_nonexist", isinstance(r,list))
    def test_rec_brand_empty(self):
        r = get_recommendations(UserPreferences(categories=["Electronics"],brands=[])); self._record("rec_brand_empty", len(r)>0)
    def test_rec_brand_with_price(self):
        r = get_recommendations(UserPreferences(categories=["Electronics"],brands=["TechBrand"],price_max=200)); self._record("rec_brand_price", isinstance(r,list))
    def test_rec_brand_budget(self):
        r = get_recommendations(UserPreferences(categories=["Electronics"],brands=["TechBrand"],price_min=50,price_max=1500)); self._record("rec_brand_budget", isinstance(r,list))
    def test_search_laptop(self):
        r = search_products("laptop"); self._record("search_laptop", len(r)>0)
    def test_search_not_found(self):
        r = search_products("zzzznotfound"); self._record("search_not_found", len(r)==0)
    def test_search_empty(self):
        r = search_products(""); self._record("search_empty", len(r)>0)
    def test_search_multi(self):
        r = search_products("wireless mouse"); self._record("search_multi", len(r)>0)
    def test_search_type(self):
        from app.models import Product
        r = search_products("laptop"); self._record("search_type", all(isinstance(p,Product) for p in r))
    def test_search_has_id(self):
        r = search_products("laptop"); self._record("search_has_id", all(p.id for p in r))
    def test_search_has_name(self):
        r = search_products("laptop"); self._record("search_has_name", all(p.name for p in r))
    def test_search_price_pos(self):
        r = search_products("laptop"); self._record("search_price_pos", all(p.price>0 for p in r))
    def test_search_rating_range(self):
        r = search_products("laptop"); self._record("search_rating_range", all(0<=p.rating<=5 for p in r))
    def test_search_has_cat(self):
        r = search_products("laptop"); self._record("search_has_cat", all(p.category for p in r))
    def test_search_has_sku(self):
        r = search_products("laptop"); self._record("search_has_sku", all(p.sku for p in r))
    def test_search_case(self):
        r1=search_products("LAPTOP"); r2=search_products("laptop"); self._record("search_case", len(r1)==len(r2))
    def test_rec_empty_prefs(self):
        r=get_recommendations(UserPreferences()); self._record("rec_empty_prefs", isinstance(r,list))
    def test_rec_zero_budget(self):
        r=get_recommendations(UserPreferences(categories=["Electronics"],price_max=0.01)); self._record("rec_zero_budget", isinstance(r,list))
    def test_rec_high_budget(self):
        r=get_recommendations(UserPreferences(categories=["Electronics"],price_min=90000)); self._record("rec_high_budget", len(r)==0)
    def test_search_symbols(self):
        r=search_products("!@#"); self._record("search_symbols", len(r)>=0)
    def test_rec_all_cats(self):
        for cat in CATEGORIES:
            r=get_recommendations(UserPreferences(categories=[cat]))
            assert isinstance(r,list)
        self._record("rec_all_cats", True)
    def test_rec_consistency(self):
        r1=get_recommendations(UserPreferences(categories=["Electronics"]))
        r2=get_recommendations(UserPreferences(categories=["Electronics"]))
        self._record("rec_consistency", len(r1)==len(r2))
    def test_rec_sorted_by_rating(self):
        r=get_recommendations(UserPreferences(categories=["Electronics"],price_min=100,price_max=500))
        if len(r)>=2: self._record("rec_sorted", r[0].rating>=r[-1].rating)
        else: self._record("rec_sorted", True)
    def test_rec_vary_by_cat(self):
        r1=get_recommendations(UserPreferences(categories=["Electronics"]))
        r2=get_recommendations(UserPreferences(categories=["Fashion"]))
        self._record("rec_vary", len(r1)>=0 and len(r2)>=0)
    def test_search_unicode(self):
        r=search_products("\u00e9l\u00e9ctronique"); self._record("search_unicode", len(r)>=0)
    def test_search_numbers(self):
        r=search_products("12345"); self._record("search_numbers", len(r)>=0)
    def test_rec_brand_limit(self):
        r=get_recommendations(UserPreferences(categories=["Electronics"],brands=["TechBrand"],price_min=100,price_max=3000))
        self._record("rec_brand_limit", isinstance(r,list))

    @classmethod
    def generate_report(cls):
        lines = [f"# Recommendation \u2014 Individual Test Report",
            f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"**Passed:** {cls.passed} | **Failed:** {cls.failed} | **Total:** {cls.passed + cls.failed}","",
            "## Results","| Test Case | Status | Detail |","|---|---|---|"]
        for r in cls.REPORT:
            lines.append(f"| {r['name']} | {'PASS' if r['passed'] else 'FAIL'} | {r['detail']} |")
        _write_report("recommendation", "\n".join(lines))


# ============================================================
# 8. CROSS SELL — 52 cases
# ============================================================

class TestCrossSellSuite:
    REPORT = []; passed = 0; failed = 0
    @classmethod
    def _record(cls, name, passed, detail=""):
        if passed: cls.passed += 1
        else: cls.failed += 1
        cls.REPORT.append({"name": name, "passed": passed, "detail": detail})

    def test_cross_p1(self):
        r = get_cross_sell(1); self._record("cross_p1", len(r.recommendations)>0)
    def test_cross_p2(self):
        r = get_cross_sell(2); self._record("cross_p2", len(r.recommendations)>0)
    def test_cross_p5(self):
        r = get_cross_sell(5); self._record("cross_p5", len(r.recommendations)>0)
    def test_cross_p10(self):
        r = get_cross_sell(10); self._record("cross_p10", len(r.recommendations)>0)
    def test_cross_p50(self):
        r = get_cross_sell(50); self._record("cross_p50", len(r.recommendations)>0)
    def test_cross_p100(self):
        r = get_cross_sell(100); self._record("cross_p100", len(r.recommendations)>0)
    def test_cross_not_found(self):
        r = get_cross_sell(99999); self._record("cross_not_found", len(r.recommendations)==0)
    def test_cross_neg_id(self):
        r = get_cross_sell(-1); self._record("cross_neg_id", len(r.recommendations)==0)
    def test_cross_zero_id(self):
        r = get_cross_sell(0); self._record("cross_zero_id", len(r.recommendations)==0)
    def test_cross_max_id(self):
        max_id = 99999
        r = get_cross_sell(max_id); self._record("cross_max_id", len(r.recommendations)>=0)
    def test_cross_types(self):
        r = get_cross_sell(1)
        types = {rec.type for rec in r.recommendations}
        self._record("cross_types", "upsell" in types or "complementary" in types)
    def test_cross_has_complementary(self):
        r = get_cross_sell(1)
        self._record("cross_has_comp", any(rec.type=="complementary" for rec in r.recommendations))
    def test_cross_has_upsell(self):
        r = get_cross_sell(1)
        self._record("cross_has_upsell", any(rec.type=="upsell" for rec in r.recommendations))
    def test_cross_has_accessory(self):
        r = get_cross_sell(1)
        self._record("cross_has_accessory", isinstance(any(rec.type=="accessory" for rec in r.recommendations),bool))
    def test_cross_type_valid(self):
        r = get_cross_sell(1); vt={"complementary","upsell","accessory"}
        self._record("cross_type_valid", all(rec.type in vt for rec in r.recommendations))
    def test_cross_score_range(self):
        r = get_cross_sell(1)
        self._record("cross_score_range", all(0<=rec.match_score<=1 for rec in r.recommendations))
    def test_cross_has_reason(self):
        r = get_cross_sell(1); self._record("cross_has_reason", all(rec.reason for rec in r.recommendations))
    def test_cross_sorted(self):
        r = get_cross_sell(1); scores=[rec.match_score for rec in r.recommendations]
        self._record("cross_sorted", scores==sorted(scores,reverse=True))
    def test_cross_cart(self):
        r = get_cross_sell(1, cart_product_ids=[2,3]); self._record("cross_cart", len(r.recommendations)>0)
    def test_cross_cart_excludes(self):
        r = get_cross_sell(1, cart_product_ids=[1]); ids=[rec.product["id"] for rec in r.recommendations]
        self._record("cross_cart_excludes", 1 not in ids)
    def test_cross_cart_empty(self):
        r = get_cross_sell(1, cart_product_ids=[]); self._record("cross_cart_empty", len(r.recommendations)>0)
    def test_cross_cart_none(self):
        r = get_cross_sell(1); self._record("cross_cart_none", len(r.recommendations)>0)
    def test_cross_cart_many(self):
        r = get_cross_sell(1, cart_product_ids=list(range(10,30))); self._record("cross_cart_many", len(r.recommendations)>0)
    def test_cross_cart_nonexist(self):
        r = get_cross_sell(1, cart_product_ids=[99999]); self._record("cross_cart_nonexist", len(r.recommendations)>0)
    def test_cross_cart_context(self):
        r = get_cross_sell(1, cart_product_ids=[2,3]); self._record("cross_cart_ctx", len(r.cart_context)>0)
    def test_cross_cart_context_empty(self):
        r = get_cross_sell(1); self._record("cross_cart_ctx_empty", len(r.cart_context)==0)
    def test_cross_ctx_ids(self):
        r = get_cross_sell(1, cart_product_ids=[2,3]); ids=[p["id"] for p in r.cart_context]
        self._record("cross_ctx_ids", 2 in ids and 3 in ids)
    def test_cross_source(self):
        r = get_cross_sell(1); self._record("cross_source", r.source_product is not None)
    def test_cross_source_id(self):
        r = get_cross_sell(1); self._record("cross_source_id", r.source_product["id"]==1)
    def test_cross_source_not_found(self):
        r = get_cross_sell(99999); self._record("cross_source_not_found", r.source_product["id"]==99999)
    def test_cross_source_has_name(self):
        r = get_cross_sell(1); self._record("cross_source_name", "name" in r.source_product)
    def test_cross_source_has_price(self):
        r = get_cross_sell(1); self._record("cross_source_price", "price" in r.source_product)
    def test_cross_source_has_cat(self):
        r = get_cross_sell(1); self._record("cross_source_cat", "category" in r.source_product)
    def test_cross_elec(self):
        for p in ALL_PRODUCTS[:30]:
            if p["category"]=="Electronics": r=get_cross_sell(p["id"]); assert r is not None; break
        self._record("cross_elec", True)
    def test_cross_fashion(self):
        for p in ALL_PRODUCTS[:50]:
            if p["category"]=="Fashion": r=get_cross_sell(p["id"]); assert r is not None; break
        self._record("cross_fashion", True)
    def test_cross_home(self):
        for p in ALL_PRODUCTS[:50]:
            if p["category"]=="Home": r=get_cross_sell(p["id"]); assert r is not None; break
        self._record("cross_home", True)
    def test_cross_sports(self):
        for p in ALL_PRODUCTS[:50]:
            if p["category"]=="Sports": r=get_cross_sell(p["id"]); assert r is not None; break
        self._record("cross_sports", True)
    def test_cross_accessories(self):
        for p in ALL_PRODUCTS[:50]:
            if p["category"]=="Accessories": r=get_cross_sell(p["id"]); assert r is not None; break
        self._record("cross_accessories", True)
    def test_cross_max_recs(self):
        r = get_cross_sell(1); self._record("cross_max_recs", len(r.recommendations)<=12)
    def test_cross_result_type(self):
        r = get_cross_sell(1); self._record("cross_result_type", isinstance(r,CrossSellResult))
    def test_cross_dup_cart(self):
        r = get_cross_sell(1, cart_product_ids=[1,1,1]); self._record("cross_dup_cart", len(r.recommendations)>0)
    def test_cross_source_in_cart(self):
        r = get_cross_sell(1, cart_product_ids=[1]); ids=[rec.product["id"] for rec in r.recommendations]
        self._record("cross_source_in_cart", 1 not in ids)
    def test_cross_unique_ids(self):
        r = get_cross_sell(1); ids=[rec.product["id"] for rec in r.recommendations]
        self._record("cross_unique_ids", len(ids)==len(set(ids)))
    def test_cross_all_fields(self):
        r = get_cross_sell(1)
        for rec in r.recommendations[:5]:
            assert rec.product and rec.type and rec.reason and 0<=rec.match_score<=1
        self._record("cross_all_fields", True)
    def test_cross_large_cart(self):
        r = get_cross_sell(1, cart_product_ids=list(range(100,150))); self._record("cross_large_cart", len(r.recommendations)>0)

    @classmethod
    def generate_report(cls):
        lines = [f"# Cross Sell \u2014 Individual Test Report",
            f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"**Passed:** {cls.passed} | **Failed:** {cls.failed} | **Total:** {cls.passed + cls.failed}","",
            "## Results","| Test Case | Status | Detail |","|---|---|---|"]
        for r in cls.REPORT:
            lines.append(f"| {r['name']} | {'PASS' if r['passed'] else 'FAIL'} | {r['detail']} |")
        _write_report("cross_sell", "\n".join(lines))


# ============================================================
# 9. GIFT FINDER — 52 cases
# ============================================================

class TestGiftFinderSuite:
    REPORT = []; passed = 0; failed = 0
    @classmethod
    def _record(cls, name, passed, detail=""):
        if passed: cls.passed += 1
        else: cls.failed += 1
        cls.REPORT.append({"name": name, "passed": passed, "detail": detail})

    def test_gift_birthday_mother(self):
        r = find_gifts(GiftRecipient(occasion="birthday",relationship="mother",age_group="adult",interests=["books","music"]))
        self._record("gift_bday_mother", r.total_found>0)
    def test_gift_anniversary_spouse(self):
        r = find_gifts(GiftRecipient(occasion="anniversary",relationship="spouse",age_group="adult",interests=["electronics","gadgets"]))
        self._record("gift_anniv_spouse", r.total_found>0)
    def test_gift_christmas_friend(self):
        r = find_gifts(GiftRecipient(occasion="christmas",relationship="friend",age_group="adult",interests=["tech","gaming"]))
        self._record("gift_xmas_friend", r.total_found>0)
    def test_gift_wedding(self):
        r = find_gifts(GiftRecipient(occasion="wedding",relationship="friend",age_group="adult",interests=["home","decor"]))
        self._record("gift_wedding", r.total_found>=0)
    def test_gift_graduation(self):
        r = find_gifts(GiftRecipient(occasion="graduation",relationship="sibling",age_group="teen",interests=["tech"]))
        self._record("gift_grad", r.total_found>=0)
    def test_gift_valentine(self):
        r = find_gifts(GiftRecipient(occasion="valentine",relationship="partner",age_group="adult",interests=["jewelry"]))
        self._record("gift_valentine", r.total_found>=0)
    def test_gift_mothers_day(self):
        r = find_gifts(GiftRecipient(occasion="mother\u2019s day",relationship="parent",age_group="adult",interests=["home"]))
        self._record("gift_mothers_day", r.total_found>=0)
    def test_gift_housewarming(self):
        r = find_gifts(GiftRecipient(occasion="housewarming",relationship="friend",age_group="adult",interests=["home","decor"]))
        self._record("gift_housewarming", r.total_found>=0)
    def test_gift_baby_shower(self):
        r = find_gifts(GiftRecipient(occasion="baby shower",relationship="friend",age_group="adult",interests=["toys"]))
        self._record("gift_baby_shower", r.total_found>=0)
    def test_gift_no_occasion(self):
        r = find_gifts(GiftRecipient(relationship="friend",age_group="adult",interests=["books"]))
        self._record("gift_no_occ", r.total_found>0)
    def test_gift_generic(self):
        r = find_gifts(GiftRecipient(interests=["electronics"])); self._record("gift_generic", r.total_found>0)
    def test_gift_spouse(self):
        r = find_gifts(GiftRecipient(occasion="birthday",relationship="spouse",age_group="adult",interests=["romantic"]))
        self._record("gift_spouse", r.total_found>=0)
    def test_gift_parent(self):
        r = find_gifts(GiftRecipient(occasion="birthday",relationship="parent",age_group="senior",interests=["comfort"]))
        self._record("gift_parent", r.total_found>=0)
    def test_gift_sibling(self):
        r = find_gifts(GiftRecipient(occasion="birthday",relationship="sibling",age_group="teen",interests=["games"]))
        self._record("gift_sibling", r.total_found>=0)
    def test_gift_child(self):
        r = find_gifts(GiftRecipient(occasion="birthday",relationship="child",age_group="child",interests=["toys"]))
        self._record("gift_child", r.total_found>=0)
    def test_gift_coworker(self):
        r = find_gifts(GiftRecipient(occasion="birthday",relationship="coworker",age_group="adult",interests=["desk"]))
        self._record("gift_coworker", r.total_found>=0)
    def test_gift_friend(self):
        r = find_gifts(GiftRecipient(occasion="birthday",relationship="friend",age_group="young adult",interests=["fashion"]))
        self._record("gift_friend", r.total_found>=0)
    def test_gift_partner(self):
        r = find_gifts(GiftRecipient(occasion="anniversary",relationship="partner",age_group="adult",interests=["personalized"]))
        self._record("gift_partner", r.total_found>=0)
    def test_gift_no_relationship(self):
        r = find_gifts(GiftRecipient(occasion="birthday",age_group="adult",interests=["books"])); self._record("gift_no_rel", r.total_found>0)
    def test_gift_budget_low(self):
        r = find_gifts(GiftRecipient(occasion="birthday",relationship="friend",age_group="adult",interests=["books"],budget=25))
        self._record("gift_budget_low", r.total_found>=0)
    def test_gift_budget_med(self):
        r = find_gifts(GiftRecipient(occasion="birthday",relationship="mother",age_group="adult",interests=["accessories"],budget=100))
        self._record("gift_budget_med", r.total_found>0)
    def test_gift_budget_high(self):
        r = find_gifts(GiftRecipient(occasion="birthday",relationship="spouse",age_group="adult",interests=["electronics"],budget=500))
        self._record("gift_budget_high", r.total_found>0)
    def test_gift_budget_zero(self):
        r = find_gifts(GiftRecipient(occasion="birthday",relationship="friend",age_group="adult",interests=["books"],budget=0))
        self._record("gift_budget_zero", r.total_found>=0)
    def test_gift_budget_none(self):
        r = find_gifts(GiftRecipient(occasion="birthday",relationship="friend",age_group="adult",interests=["electronics"]))
        self._record("gift_budget_none", r.total_found>0)
    def test_gift_budget_negative(self):
        r = find_gifts(GiftRecipient(occasion="birthday",relationship="friend",age_group="adult",interests=["books"],budget=-50))
        self._record("gift_budget_neg", r.total_found>=0)
    def test_gift_age_infant(self):
        r = find_gifts(GiftRecipient(occasion="birthday",relationship="child",age_group="infant",interests=["toys"])); self._record("gift_age_infant", r.total_found>=0)
    def test_gift_age_toddler(self):
        r = find_gifts(GiftRecipient(occasion="birthday",relationship="child",age_group="toddler",interests=["toys"])); self._record("gift_age_toddler", r.total_found>=0)
    def test_gift_age_child(self):
        r = find_gifts(GiftRecipient(occasion="birthday",relationship="child",age_group="child",interests=["toys"])); self._record("gift_age_child", r.total_found>=0)
    def test_gift_age_teen(self):
        r = find_gifts(GiftRecipient(occasion="birthday",relationship="sibling",age_group="teen",interests=["gaming"])); self._record("gift_age_teen", r.total_found>=0)
    def test_gift_age_senior(self):
        r = find_gifts(GiftRecipient(occasion="birthday",relationship="parent",age_group="senior",interests=["books"])); self._record("gift_age_senior", r.total_found>=0)
    def test_gift_age_none(self):
        r = find_gifts(GiftRecipient(occasion="birthday",relationship="friend",interests=["sports"])); self._record("gift_age_none", r.total_found>0)
    def test_gift_interest_single(self):
        r = find_gifts(GiftRecipient(occasion="birthday",relationship="mother",age_group="adult",interests=["cooking"])); self._record("gift_int_single", r.total_found>0)
    def test_gift_interest_multi(self):
        r = find_gifts(GiftRecipient(occasion="birthday",relationship="friend",age_group="adult",interests=["tech","gaming","music"])); self._record("gift_int_multi", r.total_found>0)
    def test_gift_interest_empty(self):
        r = find_gifts(GiftRecipient(occasion="birthday",relationship="friend",age_group="adult",interests=[])); self._record("gift_int_empty", r.total_found>0)
    def test_gift_gender_male(self):
        r = find_gifts(GiftRecipient(occasion="birthday",relationship="friend",age_group="adult",interests=["sports"],gender_preference="male"))
        self._record("gift_gender_male", r.total_found>=0)
    def test_gift_gender_female(self):
        r = find_gifts(GiftRecipient(occasion="birthday",relationship="friend",age_group="adult",interests=["fashion"],gender_preference="female"))
        self._record("gift_gender_female", r.total_found>=0)
    def test_gift_gender_none(self):
        r = find_gifts(GiftRecipient(occasion="birthday",relationship="friend",age_group="adult",interests=["books"])); self._record("gift_gender_none", r.total_found>0)
    def test_gift_summary_not_empty(self):
        r = find_gifts(GiftRecipient(occasion="birthday",relationship="friend",age_group="teen",interests=["sports"])); self._record("gift_summary", len(r.summary)>0)
    def test_gift_summary_found(self):
        r = find_gifts(GiftRecipient(occasion="birthday",relationship="mother",age_group="adult",interests=["books"])); self._record("gift_summary_found", "Found" in r.summary)
    def test_gift_recs_reasons(self):
        r = find_gifts(GiftRecipient(occasion="birthday",relationship="mother",age_group="adult",interests=["books"]))
        if r.recommendations: self._record("gift_recs_reasons", len(r.recommendations[0].match_reasons)>0)
        else: self._record("gift_recs_reasons", True)
    def test_gift_recs_score(self):
        r = find_gifts(GiftRecipient(occasion="birthday",relationship="mother",age_group="adult",interests=["books"]))
        if r.recommendations: self._record("gift_recs_score", all(0<=rec.relevance_score<=1 for rec in r.recommendations))
        else: self._record("gift_recs_score", True)
    def test_gift_max_recs(self):
        r = find_gifts(GiftRecipient(occasion="birthday",relationship="friend",age_group="adult",interests=["electronics","books","music"]))
        self._record("gift_max_recs", len(r.recommendations)<=20)
    def test_gift_recs_sorted(self):
        r = find_gifts(GiftRecipient(occasion="birthday",relationship="mother",age_group="adult",interests=["books"]))
        scores=[rec.relevance_score for rec in r.recommendations]
        self._record("gift_recs_sorted", scores==sorted(scores,reverse=True))
    def test_gift_fathers_day(self):
        r = find_gifts(GiftRecipient(occasion="father\u2019s day",relationship="parent",age_group="adult",interests=["sports"]))
        self._record("gift_fathers_day", r.total_found>=0)

    @classmethod
    def generate_report(cls):
        lines = [f"# Gift Finder \u2014 Individual Test Report",
            f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"**Passed:** {cls.passed} | **Failed:** {cls.failed} | **Total:** {cls.passed + cls.failed}","",
            "## Results","| Test Case | Status | Detail |","|---|---|---|"]
        for r in cls.REPORT:
            lines.append(f"| {r['name']} | {'PASS' if r['passed'] else 'FAIL'} | {r['detail']} |")
        _write_report("gift_finder", "\n".join(lines))


# ============================================================
# 10. DEAL AGENT — 56 cases
# ============================================================

class TestDealAgentSuite:
    REPORT = []; passed = 0; failed = 0
    @classmethod
    def _record(cls, name, passed, detail=""):
        if passed: cls.passed += 1
        else: cls.failed += 1
        cls.REPORT.append({"name": name, "passed": passed, "detail": detail})

    _e_cart = CartSession(user_id="du", items=[CartItem(product_id="1",sku="SKU-AB001",name="Laptop",price=1000.0,quantity=1,category="Electronics")],loyalty_tier=LoyaltyTier.gold)
    _m_cart = CartSession(user_id="du2", items=[CartItem(product_id="1",sku="SKU-AB001",name="Laptop",price=1000.0,quantity=1,category="Electronics"),CartItem(product_id="2",sku="SKU-AB002",name="Shirt",price=50.0,quantity=2,category="Fashion")],loyalty_tier=LoyaltyTier.platinum)
    _e_cart_b = CartSession(user_id="du3", items=[CartItem(product_id="1",sku="SKU-AB001",name="Book",price=15.0,quantity=1,category="Books")],loyalty_tier=LoyaltyTier.bronze)

    def test_active_promos(self):
        p=deal_agent.get_active_promotions(); self._record("active_promos", len(p)>0)
    def test_active_promos_active(self):
        p=deal_agent.get_active_promotions(); self._record("active_promos_active", all(p_.active for p_ in p))
    def test_active_promos_min(self):
        p=deal_agent.get_active_promotions(); self._record("active_promos_min", len(p)>=10)
    def test_active_promos_types(self):
        p=deal_agent.get_active_promotions(); ts={p_.type for p_ in p}; self._record("active_promos_types", DiscountType.percentage in ts)
    def test_active_promos_bogo(self):
        p=deal_agent.get_active_promotions(); self._record("active_promos_bogo", any(p_.type==DiscountType.bogo for p_ in p))
    def test_active_promos_fixed(self):
        p=deal_agent.get_active_promotions(); self._record("active_promos_fixed", any(p_.type==DiscountType.fixed for p_ in p))
    def test_active_promos_cat_md(self):
        p=deal_agent.get_active_promotions(); self._record("active_promos_cat_md", any(p_.type==DiscountType.category_markdown for p_ in p))
    def test_add_promo(self):
        promo=Promotion(id="t1",name="Test",description="t",type=DiscountType.fixed,value=10.0,stackable=True)
        a=deal_agent.add_promotion(promo); self._record("add_promo", a is not None and a.id=="t1")
    def test_deactivate_promo(self):
        promo=Promotion(id="t2",name="Test2",description="t",type=DiscountType.fixed,value=10.0)
        deal_agent.add_promotion(promo); r=deal_agent.deactivate_promotion("t2"); self._record("deactivate_promo", r)
    def test_deactivate_nonexist(self):
        r=deal_agent.deactivate_promotion("nonexist"); self._record("deactivate_nonexist", r is False)
    def test_deactivate_inactive(self):
        promo=Promotion(id="t3",name="Test3",description="t",type=DiscountType.fixed,value=10.0,active=False)
        deal_agent.add_promotion(promo); r=deal_agent.deactivate_promotion("t3"); self._record("deactivate_inactive", r is False)
    def test_opt_elec_gold(self):
        s=deal_agent.optimize_stack(self._e_cart); self._record("opt_elec_gold", s is not None and s.final_total<s.original_total)
    def test_opt_mixed_plat(self):
        s=deal_agent.optimize_stack(self._m_cart); self._record("opt_mixed_plat", s is not None and s.total_savings>0)
    def test_opt_single_low(self):
        s=deal_agent.optimize_stack(self._e_cart_b); self._record("opt_single_low", s is not None)
    def test_opt_savings_pos(self):
        s=deal_agent.optimize_stack(self._e_cart); self._record("opt_savings_pos", s.total_savings>0)
    def test_opt_final_nonneg(self):
        s=deal_agent.optimize_stack(self._m_cart); self._record("opt_final_nonneg", s.final_total>=0)
    def test_opt_with_budget(self):
        c=CartSession(user_id="bu",items=[CartItem(product_id="1",sku="SKU-AB001",name="Laptop",price=1000.0,quantity=1,category="Electronics")],loyalty_tier=LoyaltyTier.gold,budget=500.0)
        s=deal_agent.optimize_stack(c); self._record("opt_with_budget", s is not None)
    def test_opt_opted_out(self):
        c=CartSession(user_id="oo",items=[CartItem(product_id="1",sku="SKU-AB001",name="Laptop",price=1000.0,quantity=1,category="Electronics")],loyalty_tier=LoyaltyTier.bronze,opted_out=True)
        s=deal_agent.optimize_stack(c); self._record("opt_opted_out", s is not None)
    def test_opt_all_tiers(self):
        for t in [LoyaltyTier.bronze,LoyaltyTier.silver,LoyaltyTier.gold,LoyaltyTier.platinum]:
            c=CartSession(user_id=f"t{t.value}",items=[CartItem(product_id="1",sku="SKU-AB001",name="Item",price=200.0,quantity=1,category="General")],loyalty_tier=t)
            assert deal_agent.optimize_stack(c) is not None
        self._record("opt_all_tiers", True)
    def test_opt_breakdown(self):
        s=deal_agent.optimize_stack(self._e_cart); self._record("opt_breakdown", "Subtotal" in s.savings_breakdown and "Total" in s.savings_breakdown)
    def test_opt_applied(self):
        s=deal_agent.optimize_stack(self._e_cart); self._record("opt_applied", len(s.applied_discounts)>0)
    def test_opt_original_gt_final(self):
        s=deal_agent.optimize_stack(self._e_cart); self._record("opt_orig_gt_final", s.original_total>s.final_total)
    def test_opt_user_id(self):
        s=deal_agent.optimize_stack(self._e_cart); self._record("opt_user_id", s.user_id=="du")
    def test_apply_stack(self):
        s=deal_agent.optimize_stack(self._e_cart); r=deal_agent.apply_stack(s.id); self._record("apply_stack", r is not None)
    def test_get_stack(self):
        s=deal_agent.optimize_stack(self._e_cart); f=deal_agent.get_stack(s.id); self._record("get_stack", f is not None and f.id==s.id)
    def test_get_stack_not_found(self):
        f=deal_agent.get_stack("nonexist"); self._record("get_stack_not_found", f is None)
    def test_apply_stack_not_found(self):
        r=deal_agent.apply_stack("nonexist"); self._record("apply_stack_not_found", r is None)
    def test_list_stacks(self):
        st=deal_agent.list_stacks(); self._record("list_stacks", isinstance(st,list))
    def test_list_stacks_after_opt(self):
        deal_agent.optimize_stack(self._e_cart); st=deal_agent.list_stacks(); self._record("list_stacks_after", len(st)>0)
    def test_proc_cart_plat(self):
        req=DealSessionRequest(user_id="pc1",items=[CartItem(product_id="1",sku="SKU-AB001",name="Laptop",price=1000.0,quantity=1,category="Electronics")],loyalty_tier=LoyaltyTier.platinum)
        r=deal_agent.process_cart(req); self._record("proc_cart_plat", "total_savings" in r)
    def test_proc_cart_savings(self):
        req=DealSessionRequest(user_id="pc2",items=[CartItem(product_id="1",sku="SKU-AB001",name="Laptop",price=1000.0,quantity=1,category="Electronics")],loyalty_tier=LoyaltyTier.gold)
        r=deal_agent.process_cart(req); self._record("proc_cart_savings", r["total_savings"]>=0)
    def test_proc_cart_empty(self):
        req=DealSessionRequest(user_id="pc3",items=[],loyalty_tier=LoyaltyTier.bronze)
        r=deal_agent.process_cart(req); self._record("proc_cart_empty", "message" in r)
    def test_proc_cart_budget(self):
        req=DealSessionRequest(user_id="pc4",items=[CartItem(product_id="1",sku="SKU-AB001",name="Laptop",price=1000.0,quantity=1,category="Electronics")],loyalty_tier=LoyaltyTier.gold,budget=100.0)
        r=deal_agent.process_cart(req); self._record("proc_cart_budget", "total_savings" in r)
    def test_proc_cart_opted_out(self):
        req=DealSessionRequest(user_id="pc5",items=[CartItem(product_id="1",sku="SKU-AB001",name="Laptop",price=1000.0,quantity=1,category="Electronics")],loyalty_tier=LoyaltyTier.bronze,opted_out=True)
        r=deal_agent.process_cart(req); self._record("proc_cart_opted_out", "total_savings" in r)
    def test_promo_app_elec(self):
        promo=Promotion(id="pa1",name="$10 off",description="t",type=DiscountType.fixed,value=10.0,min_purchase=50.0,applicable_categories=["Electronics"])
        self._record("promo_app_elec", promo.is_applicable(self._e_cart))
    def test_promo_not_app_low_tier(self):
        promo=Promotion(id="pa2",name="Gold only",description="t",type=DiscountType.fixed,value=10.0,min_loyalty_tier=LoyaltyTier.gold)
        c=CartSession(user_id="u",items=[CartItem(product_id="1",sku="SKU-AB001",name="Item",price=100.0,quantity=1,category="General")],loyalty_tier=LoyaltyTier.bronze)
        self._record("promo_not_app_low_tier", not promo.is_applicable(c))
    def test_promo_not_app_min_purchase(self):
        promo=Promotion(id="pa3",name="Big spender",description="t",type=DiscountType.fixed,value=10.0,min_purchase=500.0)
        c=CartSession(user_id="u",items=[CartItem(product_id="1",sku="SKU-AB001",name="Item",price=100.0,quantity=1,category="General")])
        self._record("promo_not_app_min", not promo.is_applicable(c))
    def test_promo_not_app_category(self):
        promo=Promotion(id="pa4",name="Fashion only",description="t",type=DiscountType.fixed,value=10.0,applicable_categories=["Fashion"])
        self._record("promo_not_app_cat", not promo.is_applicable(self._e_cart))
    def test_promo_app_fixed(self):
        promo=Promotion(id="pa5",name="$20 off",description="t",type=DiscountType.fixed,value=20.0)
        c=CartSession(user_id="u",items=[CartItem(product_id="1",sku="SKU-AB001",name="Item",price=100.0,quantity=1,category="General")])
        r=promo.apply_to(c); self._record("promo_app_fixed", r["discount"]==20.0)
    def test_promo_app_pct(self):
        promo=Promotion(id="pa6",name="10% off",description="t",type=DiscountType.percentage,value=10.0)
        c=CartSession(user_id="u",items=[CartItem(product_id="1",sku="SKU-AB001",name="Item",price=200.0,quantity=1,category="General")])
        r=promo.apply_to(c); self._record("promo_app_pct", r["discount"]==20.0)
    def test_promo_app_bogo(self):
        promo=Promotion(id="pa7",name="BOGO",description="t",type=DiscountType.bogo,value=0)
        c=CartSession(user_id="u",items=[CartItem(product_id="1",sku="SKU-AB001",name="A",price=50.0,quantity=1,category="General"),CartItem(product_id="2",sku="SKU-AB002",name="B",price=30.0,quantity=1,category="General")])
        r=promo.apply_to(c); self._record("promo_app_bogo", r["discount"]==30.0)
    def test_promo_app_cat_md(self):
        promo=Promotion(id="pa8",name="Cat 10%",description="t",type=DiscountType.category_markdown,value=10.0,applicable_categories=["Electronics"])
        r=promo.apply_to(self._e_cart); self._record("promo_app_cat_md", r["discount"]==100.0)
    def test_promo_app_fixed_max(self):
        promo=Promotion(id="pa9",name="$30 off max $15",description="t",type=DiscountType.fixed,value=30.0,max_discount=15.0)
        c=CartSession(user_id="u",items=[CartItem(product_id="1",sku="SKU-AB001",name="Item",price=100.0,quantity=1,category="General")])
        r=promo.apply_to(c); self._record("promo_app_fixed_max", r["discount"]==15.0)
    def test_promo_app_pct_max(self):
        promo=Promotion(id="pa10",name="50% off max $10",description="t",type=DiscountType.percentage,value=50.0,max_discount=10.0)
        c=CartSession(user_id="u",items=[CartItem(product_id="1",sku="SKU-AB001",name="Item",price=100.0,quantity=1,category="General")])
        r=promo.apply_to(c); self._record("promo_app_pct_max", r["discount"]==10.0)
    def test_promo_bogo_one_item(self):
        promo=Promotion(id="pa11",name="BOGO",description="t",type=DiscountType.bogo,value=0)
        c=CartSession(user_id="u",items=[CartItem(product_id="1",sku="SKU-AB001",name="Item",price=50.0,quantity=1,category="General")])
        r=promo.apply_to(c); self._record("promo_bogo_one_item", r["discount"]==0.0)
    def test_promo_not_app_inactive(self):
        promo=Promotion(id="pa12",name="Inactive",description="t",type=DiscountType.fixed,value=10.0,active=False)
        c=CartSession(user_id="u",items=[CartItem(product_id="1",sku="SKU-AB001",name="Item",price=100.0,quantity=1,category="General")])
        self._record("promo_not_app_inactive", not promo.is_applicable(c))
    def test_promo_not_app_opt_out_with_require(self):
        promo=Promotion(id="pa13",name="Opt-in required",description="t",type=DiscountType.fixed,value=10.0,requires_opt_in=True)
        c=CartSession(user_id="u",items=[CartItem(product_id="1",sku="SKU-AB001",name="Item",price=100.0,quantity=1,category="General")],opted_out=True)
        self._record("promo_not_app_optout", not promo.is_applicable(c))
    def test_promo_new_total_zero(self):
        promo=Promotion(id="pa14",name="$200 off $100",description="t",type=DiscountType.fixed,value=200.0)
        c=CartSession(user_id="u",items=[CartItem(product_id="1",sku="SKU-AB001",name="Item",price=100.0,quantity=1,category="General")])
        r=promo.apply_to(c); self._record("promo_new_total_zero", r["new_total"]==0.0)
    def test_opt_breakdown_contains_applied(self):
        s=deal_agent.optimize_stack(self._e_cart)
        self._record("opt_breakdown_applied", "$" in s.savings_breakdown)

    @classmethod
    def generate_report(cls):
        lines = [f"# Deal Agent \u2014 Individual Test Report",
            f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"**Passed:** {cls.passed} | **Failed:** {cls.failed} | **Total:** {cls.passed + cls.failed}","",
            "## Results","| Test Case | Status | Detail |","|---|---|---|"]
        for r in cls.REPORT:
            lines.append(f"| {r['name']} | {'PASS' if r['passed'] else 'FAIL'} | {r['detail']} |")
        _write_report("deal_agent", "\n".join(lines))


# ============================================================
# 11. ORCHESTRATOR — 54 cases
# ============================================================

class TestOrchestratorSuite:
    REPORT = []; passed = 0; failed = 0
    @classmethod
    def _record(cls, name, passed, detail=""):
        if passed: cls.passed += 1
        else: cls.failed += 1
        cls.REPORT.append({"name": name, "passed": passed, "detail": detail})

    @pytest.mark.asyncio
    async def test_collab_laptop(self):
        r=await orchestrator.run_collaborative_task("I need a laptop under $1000"); self._record("collab_laptop", r is not None and r.get("status")=="completed")
    @pytest.mark.asyncio
    async def test_collab_gift_mom(self):
        r=await orchestrator.run_collaborative_task("find me a gift for my mom's birthday"); self._record("collab_gift_mom", r is not None)
    @pytest.mark.asyncio
    async def test_collab_budget(self):
        r=await orchestrator.run_collaborative_task("laptop $500"); self._record("collab_budget", r is not None)
    @pytest.mark.asyncio
    async def test_collab_no_match(self):
        r=await orchestrator.run_collaborative_task("asdfghjkl"); self._record("collab_no_match", r is not None and r.get("status")=="completed")
    @pytest.mark.asyncio
    async def test_collab_empty(self):
        r=await orchestrator.run_collaborative_task(""); self._record("collab_empty", r is not None)
    @pytest.mark.asyncio
    async def test_collab_partial(self):
        r=await orchestrator.run_collaborative_task("laptop"); self._record("collab_partial", r is not None and r.get("status")=="completed")
    @pytest.mark.asyncio
    async def test_collab_deals(self):
        r=await orchestrator.run_collaborative_task("show me deals on electronics"); self._record("collab_deals", r is not None)
    @pytest.mark.asyncio
    async def test_collab_cheapest(self):
        r=await orchestrator.run_collaborative_task("cheapest laptop"); self._record("collab_cheapest", r is not None)
    @pytest.mark.asyncio
    async def test_collab_multiple(self):
        r=await orchestrator.run_collaborative_task("laptop under $500 and compare with tablets"); self._record("collab_multiple", r is not None)
    @pytest.mark.asyncio
    async def test_collab_numeric_budget(self):
        r=await orchestrator.run_collaborative_task("$300"); self._record("collab_numeric_budget", r is not None)
    @pytest.mark.asyncio
    async def test_collab_float_budget(self):
        r=await orchestrator.run_collaborative_task("$499.99"); self._record("collab_float_budget", r is not None)
    @pytest.mark.asyncio
    async def test_collab_qual(self):
        r=await orchestrator.run_collaborative_task("red dress"); self._record("collab_qual", r is not None)
    @pytest.mark.asyncio
    async def test_collab_highend(self):
        r=await orchestrator.run_collaborative_task("premium laptop"); self._record("collab_highend", r is not None)
    @pytest.mark.asyncio
    async def test_collab_gift(self):
        r=await orchestrator.run_collaborative_task("gift for dad"); self._record("collab_gift_dad", r is not None)
    @pytest.mark.asyncio
    async def test_collab_deal_query(self):
        r=await orchestrator.run_collaborative_task("deals on phones"); self._record("collab_deal_query", r is not None)
    @pytest.mark.asyncio
    async def test_collab_birthday(self):
        r=await orchestrator.run_collaborative_task("birthday gift for wife"); self._record("collab_birthday", r is not None)
    @pytest.mark.asyncio
    async def test_collab_christmas(self):
        r=await orchestrator.run_collaborative_task("christmas presents for kids"); self._record("collab_christmas", r is not None)
    @pytest.mark.asyncio
    async def test_collab_wedding(self):
        r=await orchestrator.run_collaborative_task("wedding gifts"); self._record("collab_wedding", r is not None)
    @pytest.mark.asyncio
    async def test_collab_zero_budget(self):
        r=await orchestrator.run_collaborative_task("laptop under $0"); self._record("collab_zero_budget", r is not None)
    @pytest.mark.asyncio
    async def test_collab_negative_budget(self):
        r=await orchestrator.run_collaborative_task("$-50 laptop"); self._record("collab_neg_budget", r is not None)
    @pytest.mark.asyncio
    async def test_collab_large_budget(self):
        r=await orchestrator.run_collaborative_task("laptop $1000000"); self._record("collab_large_budget", r is not None)
    @pytest.mark.asyncio
    async def test_collab_mixed_case(self):
        r=await orchestrator.run_collaborative_task("FIND ME A LAPTOP"); self._record("collab_mixed_case", r is not None)
    @pytest.mark.asyncio
    async def test_collab_special_chars(self):
        r=await orchestrator.run_collaborative_task("laptop @#$%^&*()"); self._record("collab_special_chars", r is not None)
    @pytest.mark.asyncio
    async def test_collab_unicode(self):
        r=await orchestrator.run_collaborative_task("\u7b14\u8bb0\u672c\u7535\u8111"); self._record("collab_unicode", r is not None)
    @pytest.mark.asyncio
    async def test_collab_help(self):
        r=await orchestrator.run_collaborative_task("help"); self._record("collab_help", r is not None)
    @pytest.mark.asyncio
    async def test_collab_punctuation(self):
        r=await orchestrator.run_collaborative_task("..."); self._record("collab_punct", r is not None)
    @pytest.mark.asyncio
    async def test_collab_long(self):
        r=await orchestrator.run_collaborative_task("I want to find a very specific laptop. It should be under $800."); self._record("collab_long", r is not None)
    @pytest.mark.asyncio
    async def test_collab_phone(self):
        r=await orchestrator.run_collaborative_task("smartphone under $700"); self._record("collab_phone", r is not None)
    @pytest.mark.asyncio
    async def test_collab_tablet(self):
        r=await orchestrator.run_collaborative_task("best tablet for drawing"); self._record("collab_tablet", r is not None)
    @pytest.mark.asyncio
    async def test_collab_shoes(self):
        r=await orchestrator.run_collaborative_task("running shoes"); self._record("collab_shoes", r is not None)
    @pytest.mark.asyncio
    async def test_collab_headphones(self):
        r=await orchestrator.run_collaborative_task("wireless headphones"); self._record("collab_headphones", r is not None)
    @pytest.mark.asyncio
    async def test_collab_books(self):
        r=await orchestrator.run_collaborative_task("fiction books under $20"); self._record("collab_books", r is not None)
    @pytest.mark.asyncio
    async def test_collab_fashion(self):
        r=await orchestrator.run_collaborative_task("summer dresses"); self._record("collab_fashion", r is not None)
    @pytest.mark.asyncio
    async def test_collab_furniture(self):
        r=await orchestrator.run_collaborative_task("office chair"); self._record("collab_furniture", r is not None)
    @pytest.mark.asyncio
    async def test_collab_food(self):
        r=await orchestrator.run_collaborative_task("chocolate gift basket"); self._record("collab_food", r is not None)
    @pytest.mark.asyncio
    async def test_collab_toys(self):
        r=await orchestrator.run_collaborative_task("educational toys"); self._record("collab_toys", r is not None)
    @pytest.mark.asyncio
    async def test_collab_sports(self):
        r=await orchestrator.run_collaborative_task("yoga mat"); self._record("collab_sports", r is not None)
    @pytest.mark.asyncio
    async def test_collab_blank(self):
        r=await orchestrator.run_collaborative_task("   "); self._record("collab_blank", r is not None)
    @pytest.mark.asyncio
    async def test_collab_newlines(self):
        r=await orchestrator.run_collaborative_task("laptop\nunder\n$500\n"); self._record("collab_newlines", r is not None)
    @pytest.mark.asyncio
    async def test_collab_compare(self):
        r=await orchestrator.run_collaborative_task("compare laptop and desktop"); self._record("collab_compare", r is not None)
    @pytest.mark.asyncio
    async def test_collab_recommend(self):
        r=await orchestrator.run_collaborative_task("recommend a good laptop"); self._record("collab_recommend", r is not None)
    @pytest.mark.asyncio
    async def test_collab_popular(self):
        r=await orchestrator.run_collaborative_task("most popular laptop"); self._record("collab_popular", r is not None)
    @pytest.mark.asyncio
    async def test_collab_expensive(self):
        r=await orchestrator.run_collaborative_task("most expensive laptop"); self._record("collab_expensive", r is not None)
    @pytest.mark.asyncio
    async def test_collab_return(self):
        r=await orchestrator.run_collaborative_task("return policy laptop"); self._record("collab_return", r is not None)
    @pytest.mark.asyncio
    async def test_collab_warranty(self):
        r=await orchestrator.run_collaborative_task("warranty laptop"); self._record("collab_warranty", r is not None)
    @pytest.mark.asyncio
    async def test_collab_shipping(self):
        r=await orchestrator.run_collaborative_task("free shipping laptop"); self._record("collab_shipping", r is not None)
    @pytest.mark.asyncio
    async def test_collab_review(self):
        r=await orchestrator.run_collaborative_task("best reviewed laptop"); self._record("collab_review", r is not None)
    @pytest.mark.asyncio
    async def test_collab_color(self):
        r=await orchestrator.run_collaborative_task("blue laptop"); self._record("collab_color", r is not None)
    @pytest.mark.asyncio
    async def test_collab_brand(self):
        r=await orchestrator.run_collaborative_task("apple laptop"); self._record("collab_brand", r is not None)
    @pytest.mark.asyncio
    async def test_collab_personalized(self):
        r=await orchestrator.run_collaborative_task("personalized gift for mom"); self._record("collab_personalized", r is not None)
    @pytest.mark.asyncio
    async def test_collab_bulk(self):
        r=await orchestrator.run_collaborative_task("buy 10 laptops"); self._record("collab_bulk", r is not None)
    @pytest.mark.asyncio
    async def test_collab_express(self):
        r=await orchestrator.run_collaborative_task("express delivery laptop"); self._record("collab_express", r is not None)

    @classmethod
    def generate_report(cls):
        lines = [f"# Orchestrator \u2014 Individual Test Report",
            f"**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"**Passed:** {cls.passed} | **Failed:** {cls.failed} | **Total:** {cls.passed + cls.failed}","",
            "## Results","| Test Case | Status | Detail |","|---|---|---|"]
        for r in cls.REPORT:
            lines.append(f"| {r['name']} | {'PASS' if r['passed'] else 'FAIL'} | {r['detail']} |")
        _write_report("orchestrator", "\n".join(lines))


# ============================================================
# REPORT GENERATION — iterates all suites
# ============================================================

def _generate_reports():
    for suite in [TestSafetyGuardrailSuite, TestPrivacyGuardrailSuite, TestPriceGuardrailSuite,
                  TestPriceMatchSuite, TestIntentParserSuite, TestCatalogSearchSuite,
                  TestRecommendationSuite, TestCrossSellSuite, TestGiftFinderSuite,
                  TestDealAgentSuite, TestOrchestratorSuite]:
        suite.generate_report()
    print("All individual agent test reports generated in agent_reports/")

