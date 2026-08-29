import os
import sys
from unittest.mock import AsyncMock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest

from app.models import GuardrailAction, PrivacyConsent, PrivacyLevel, PrivacyRegion, UserPrivacyProfile
from app.services.privacy_guardrail import (
    PrivacyGuardrailService,
    _rule_based_agent_access,
    _rule_based_redact,
)


@pytest.fixture
def service():
    svc = PrivacyGuardrailService()
    yield svc


@pytest.fixture
def strict_profile():
    return UserPrivacyProfile(privacy_level=PrivacyLevel.strict)


@pytest.mark.asyncio
class TestInputGuardrail:
    async def test_no_pii_passes_through(self, service):
        result = await service.check_input("I need a gift for my wife")
        assert result.action == GuardrailAction.allowed
        assert result.sanitized_text == "I need a gift for my wife"

    async def test_email_redacted_rule_based(self, service):
        service.get_or_create_profile("default").privacy_level = PrivacyLevel.strict
        result = await service.check_input("Send info to john.doe@example.com")
        assert result.action == GuardrailAction.sanitized
        assert "[REDACTED_EMAIL]" in result.sanitized_text
        assert "email" in result.redacted_fields

    async def test_phone_redacted_rule_based(self, service):
        service.get_or_create_profile("default").privacy_level = PrivacyLevel.strict
        result = await service.check_input("Call me at 555-123-4567")
        assert result.action == GuardrailAction.sanitized
        assert "[REDACTED_PHONE]" in result.sanitized_text
        assert "phone" in result.redacted_fields

    async def test_ssn_redacted_rule_based(self, service):
        service.get_or_create_profile("default").privacy_level = PrivacyLevel.strict
        result = await service.check_input("My SSN is 123-45-6789")
        assert result.action == GuardrailAction.sanitized
        assert "[REDACTED_SSN]" in result.sanitized_text
        assert "ssn" in result.redacted_fields

    async def test_multiple_pii_redacted(self, service):
        service.get_or_create_profile("default").privacy_level = PrivacyLevel.strict
        result = await service.check_input("Email: alice@test.com, Phone: 555-000-1111")
        assert result.action == GuardrailAction.sanitized
        assert "email" in result.redacted_fields
        assert "phone" in result.redacted_fields

    async def test_empty_text(self, service):
        result = await service.check_input("")
        assert result.action == GuardrailAction.allowed

    async def test_whitespace_text(self, service):
        result = await service.check_input("   ")
        assert result.action == GuardrailAction.allowed


class TestAgentAccessGuardrail:
    def test_strict_blocks_sensitive_fields(self):
        allowed, violations = _rule_based_agent_access(
            "discovery", ["email", "name"], UserPrivacyProfile(privacy_level=PrivacyLevel.strict)
        )
        assert not allowed
        assert len(violations) > 0

    def test_open_allows_access(self):
        profile = UserPrivacyProfile(
            privacy_level=PrivacyLevel.open,
            consents=PrivacyConsent(third_party_sharing=True),
        )
        allowed, violations = _rule_based_agent_access(
            "discovery", ["email", "preferences"], profile
        )
        assert allowed

    def test_balanced_blocks_phone(self):
        profile = UserPrivacyProfile(privacy_level=PrivacyLevel.balanced)
        allowed, violations = _rule_based_agent_access(
            "discovery", ["phone"], profile
        )
        assert not allowed

    def test_balanced_allows_email(self):
        profile = UserPrivacyProfile(privacy_level=PrivacyLevel.balanced)
        allowed, violations = _rule_based_agent_access(
            "discovery", ["email"], profile
        )
        assert allowed

    @pytest.mark.asyncio
    async def test_llm_fallback_to_rules(self, service):
        profile = UserPrivacyProfile(
            privacy_level=PrivacyLevel.open,
            consents=PrivacyConsent(third_party_sharing=True),
        )
        service.update_profile("test_user", profile)
        result = await service.check_agent_access("discovery", ["email", "preferences"], "test_user")
        assert result.action == GuardrailAction.allowed

    @pytest.mark.asyncio
    async def test_blocked_third_party_no_consent(self, service):
        profile = UserPrivacyProfile(
            privacy_level=PrivacyLevel.open,
            consents=PrivacyConsent(third_party_sharing=False),
        )
        service.update_profile("test_user", profile)
        result = await service.check_agent_access("discovery", ["external_id"], "test_user")
        assert result.action == GuardrailAction.blocked


@pytest.mark.asyncio
class TestOutputGuardrail:
    async def test_strict_blocks_personal_data(self, service):
        profile = UserPrivacyProfile(privacy_level=PrivacyLevel.strict)
        service.update_profile("test_user", profile)
        recs = [{"id": "p1", "name": "Product", "user_location": "New York"}]
        result = await service.check_output(recs, "test_user")
        assert result.action == GuardrailAction.flagged

    async def test_strict_allows_safe_output(self, service):
        profile = UserPrivacyProfile(privacy_level=PrivacyLevel.strict)
        service.update_profile("test_user", profile)
        recs = [{"id": "p1", "name": "Product", "price": 100}]
        result = await service.check_output(recs, "test_user")
        assert result.action == GuardrailAction.allowed

    async def test_balanced_blocks_precise_location(self, service):
        profile = UserPrivacyProfile(privacy_level=PrivacyLevel.balanced)
        service.update_profile("test_user", profile)
        recs = [{"id": "p1", "name": "Product", "precise_location": "40.7128,-74.0060"}]
        result = await service.check_output(recs, "test_user")
        assert result.action == GuardrailAction.flagged


class TestGDPRActions:
    @pytest.mark.asyncio
    async def test_forget_user_deletes_profile(self, service):
        service.get_or_create_profile("user1")
        await service.forget_user("user1")
        assert service.export_profile("user1") is None

    @pytest.mark.asyncio
    async def test_forget_nonexistent_user(self, service):
        result = await service.forget_user("nonexistent")
        assert result is False

    def test_export_profile_exists(self, service):
        service.get_or_create_profile("user1")
        data = service.export_profile("user1")
        assert data is not None
        assert data["user_id"] == "user1"

    def test_export_profile_not_found(self, service):
        data = service.export_profile("nonexistent")
        assert data is None


class TestCCPAActions:
    def test_opt_out_of_sale(self, service):
        profile = service.get_or_create_profile("user1")
        assert profile.opted_out_of_sale is False
        updated = service.opt_out_of_sale("user1")
        assert updated is not None
        assert updated.opted_out_of_sale is True
        assert updated.consents.third_party_sharing is False

    def test_opt_out_nonexistent_user(self, service):
        result = service.opt_out_of_sale("nonexistent")
        assert result is None


class TestConsentManagement:
    def test_update_consent(self, service):
        service.get_or_create_profile("user1")
        new_consents = PrivacyConsent(marketing=True, third_party_sharing=True)
        updated = service.update_consent("user1", new_consents)
        assert updated is not None
        assert updated.consents.marketing is True
        assert updated.consents.third_party_sharing is True

    def test_update_consent_nonexistent_user(self, service):
        new_consents = PrivacyConsent(marketing=True)
        result = service.update_consent("nonexistent", new_consents)
        assert result is None


class TestProfileManagement:
    def test_get_or_create_creates_new(self, service):
        profile = service.get_or_create_profile("new_user")
        assert profile.privacy_level == PrivacyLevel.strict

    def test_get_or_create_returns_existing(self, service):
        p1 = service.get_or_create_profile("user1")
        p2 = service.get_or_create_profile("user1")
        assert p1 == p2

    def test_update_profile(self, service):
        new_profile = UserPrivacyProfile(
            privacy_level=PrivacyLevel.open,
            region=PrivacyRegion.gdpr,
        )
        updated = service.update_profile("user1", new_profile)
        assert updated.privacy_level == PrivacyLevel.open
        assert updated.region == PrivacyRegion.gdpr

    def test_delete_profile(self, service):
        service.get_or_create_profile("user1")
        assert service.delete_profile("user1") is True
        assert service.delete_profile("user1") is False


class TestRuleBasedRedact:
    def test_email_pattern(self):
        sanitized, fields = _rule_based_redact("test@example.com")
        assert "email" in fields
        assert "[REDACTED_EMAIL]" in sanitized

    def test_phone_pattern(self):
        sanitized, fields = _rule_based_redact("Call 555-123-4567 now")
        assert "phone" in fields
        assert "[REDACTED_PHONE]" in sanitized

    def test_ssn_pattern(self):
        sanitized, fields = _rule_based_redact("SSN: 123-45-6789")
        assert "ssn" in fields
        assert "[REDACTED_SSN]" in sanitized

    def test_clean_text_no_pii(self):
        sanitized, fields = _rule_based_redact("I need a new laptop")
        assert fields == []
        assert sanitized == "I need a new laptop"

    def test_multiple_redactions(self):
        sanitized, fields = _rule_based_redact("Email: a@b.com, Phone: 555-111-2222")
        assert "email" in fields
        assert "phone" in fields
