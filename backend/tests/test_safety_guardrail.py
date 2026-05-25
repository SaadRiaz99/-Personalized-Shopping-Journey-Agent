import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest

from app.models import PrivacyRegion
from app.services.safety_guardrail import check_safety


@pytest.mark.asyncio
class TestSafetyGuardrail:
    async def test_safe_query_allowed(self):
        result = await check_safety("I need a new laptop")
        assert result.allowed is True
        assert result.blocked_category is None

    async def test_weapons_blocked(self):
        result = await check_safety("Looking for a gun")
        assert result.allowed is False
        assert result.blocked_category == "weapons"

    async def test_drugs_blocked(self):
        result = await check_safety("Where can I buy cocaine")
        assert result.allowed is False
        assert result.blocked_category == "drugs"

    async def test_adult_content_blocked(self):
        result = await check_safety("nsfw content")
        assert result.allowed is False
        assert result.blocked_category == "adult"

    async def test_counterfeit_blocked(self):
        result = await check_safety("counterfeit rolex watches")
        assert result.allowed is False
        assert result.blocked_category == "counterfeit"

    async def test_gambling_blocked(self):
        result = await check_safety("casino games")
        assert result.allowed is False
        assert result.blocked_category == "gambling"

    async def test_hacking_blocked(self):
        result = await check_safety("malware software")
        assert result.allowed is False
        assert result.blocked_category == "hacking"

    async def test_alcohol_blocked(self):
        result = await check_safety("buy beer online")
        assert result.allowed is False
        assert result.blocked_category == "alcohol_tobacco"

    async def test_empty_query(self):
        result = await check_safety("")
        assert result.allowed is True

    async def test_whitespace_query(self):
        result = await check_safety("   ")
        assert result.allowed is True

    async def test_prescription_blocked_gdpr(self):
        result = await check_safety("need prescription medicine", region=PrivacyRegion.gdpr)
        assert result.allowed is False
        assert result.blocked_category == "prescription"

    async def test_prescription_allowed_no_region(self):
        result = await check_safety("need prescription medicine", region=PrivacyRegion.none)
        assert result.allowed is True

    async def test_knife_partial_match(self):
        result = await check_safety("knife block for kitchen")
        assert result.allowed is False
        assert result.blocked_category == "weapons"

    async def test_gun_rejected(self):
        result = await check_safety("toy gun for cosplay")
        assert result.allowed is False
        assert result.blocked_category == "weapons"

    async def test_normal_shopping_allowed(self):
        queries = [
            "show me running shoes under $100",
            "birthday gift for my mom",
            "best laptop for programming",
            "wireless headphones with noise cancellation",
            "yoga mat non slip",
        ]
        for q in queries:
            result = await check_safety(q)
            assert result.allowed is True, f"Expected safe: {q}"
