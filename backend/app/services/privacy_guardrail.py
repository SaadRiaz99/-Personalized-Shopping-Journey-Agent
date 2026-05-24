import json
import os
import re
from typing import Optional

import httpx

from app.models import (
    GuardrailAction,
    GuardrailResult,
    PrivacyConsent,
    PrivacyLevel,
    PrivacyRegion,
    UserPrivacyProfile,
)

LLM_API_KEY = os.getenv("LLM_API_KEY", "")
LLM_ENDPOINT = os.getenv("LLM_ENDPOINT", "https://api.openai.com/v1/chat/completions")
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")
GUARDRAIL_ENABLED = os.getenv("GUARDRAIL_ENABLED", "true").lower() == "true"


SYSTEM_PROMPT_INPUT = """You are a privacy guardrail for a shopping assistant. Your job is to identify and redact personally identifiable information (PII) from user queries.

Identify and redact ALL of the following if present:
- Email addresses
- Phone numbers
- Social Security Numbers (or any national ID)
- Physical addresses (street, city, state, zip)
- Full names (first + last name combinations)
- Precise GPS coordinates
- Credit card numbers
- Passport numbers
- Date of birth (full DOB)

Replace each redacted value with a placeholder like [REDACTED_EMAIL], [REDACTED_PHONE], [REDACTED_NAME], etc.

Respond with ONLY valid JSON (no markdown, no backticks):
{
  "sanitized_text": "the cleaned query with redactions applied",
  "redacted_fields": ["email", "phone"],
  "has_pii": true or false
}

If no PII is found, return the original text unchanged and has_pii: false."""


SYSTEM_PROMPT_AGENT_ACCESS = """You are a data access guardrail for a multi-agent shopping system. Determine whether an agent should be allowed access to specific user data fields based on the user's privacy profile.

Consider:
1. Privacy level (strict = minimal data, balanced = pseudonymized, open = full personalization)
2. Explicit consents (marketing, third_party_sharing, biometric_data, profiling)
3. Regional law requirements (GDPR requires explicit consent for each purpose; CCPA allows opt-out of sale)
4. Whether the agent genuinely needs this data to function

Respond with ONLY valid JSON (no markdown, no backticks):
{
  "allowed": true or false,
  "explanation": "brief reason for the decision",
  "violations": ["list of any violated policies or laws"]
}"""


SYSTEM_PROMPT_OUTPUT = """You are a compliance guardrail for a shopping assistant. Review the recommendations being returned to the user for privacy compliance.

Flag issues such as:
- Recommendations that reveal sensitive inferred data (health conditions, religion, political views, sexual orientation)
- Personal details that were collected without proper consent being visible in the output
- Any data that suggests profiling without user consent
- Content that references specific user location without anonymization

Respond with ONLY valid JSON (no markdown, no backticks):
{
  "compliant": true or false,
  "issues": ["list of compliance issues found, empty if compliant"],
  "explanation": "brief summary of compliance check"
}"""


async def _call_llm(system_prompt: str, user_message: str, max_tokens: int = 500) -> Optional[str]:
    if not LLM_API_KEY:
        return None
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                LLM_ENDPOINT,
                headers={
                    "Authorization": f"Bearer {LLM_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": LLM_MODEL,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_message},
                    ],
                    "temperature": 0.1,
                    "max_tokens": max_tokens,
                },
            )
            resp.raise_for_status()
            data = resp.json()
            content = data["choices"][0]["message"]["content"].strip()
            content = content.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
            return content
    except Exception:
        return None


def _rule_based_redact(text: str) -> tuple[str, list[str]]:
    redacted_fields = []
    sanitized = text

    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    if re.search(email_pattern, sanitized):
        sanitized = re.sub(email_pattern, "[REDACTED_EMAIL]", sanitized)
        redacted_fields.append("email")

    phone_pattern = r'\b(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b'
    if re.search(phone_pattern, sanitized):
        sanitized = re.sub(phone_pattern, "[REDACTED_PHONE]", sanitized)
        redacted_fields.append("phone")

    ssn_pattern = r'\b\d{3}-\d{2}-\d{4}\b'
    if re.search(ssn_pattern, sanitized):
        sanitized = re.sub(ssn_pattern, "[REDACTED_SSN]", sanitized)
        redacted_fields.append("ssn")

    address_pattern = r'\b\d{1,5}\s+[A-Za-z0-9\s.,]+(?:street|st|avenue|ave|road|rd|drive|dr|lane|ln|blvd|boulevard|way|court|ct|circle|cir)\b'
    if re.search(address_pattern, sanitized, re.IGNORECASE):
        sanitized = re.sub(address_pattern, "[REDACTED_ADDRESS]", sanitized, flags=re.IGNORECASE)
        redacted_fields.append("address")

    cc_pattern = r'\b(?:\d[ -]*?){13,16}\b'
    cc_matches = re.findall(cc_pattern, sanitized)
    for match in cc_matches:
        cleaned = match.replace(" ", "").replace("-", "")
        if len(cleaned) >= 13 and len(cleaned) <= 16:
            sanitized = sanitized.replace(match, "[REDACTED_CC]")
            if "credit_card" not in redacted_fields:
                redacted_fields.append("credit_card")

    return sanitized, list(set(redacted_fields))


def _rule_based_agent_access(agent_name: str, data_fields: list[str], profile: UserPrivacyProfile) -> tuple[bool, list[str]]:
    violations = []
    sensitive_fields = {"email", "phone", "precise_location", "real_name", "ssn", "credit_card"}

    if profile.privacy_level == PrivacyLevel.strict:
        if any(f in data_fields for f in sensitive_fields):
            violations.append(f"Strict mode: access to sensitive fields blocked for {agent_name}")
            return False, violations
        return True, violations

    if profile.privacy_level == PrivacyLevel.balanced:
        blocked = sensitive_fields - {"email"}
        if any(f in data_fields for f in blocked):
            violations.append(f"Balanced mode: {agent_name} cannot access {blocked & set(data_fields)}")
            return False, violations
        return True, violations

    if not profile.consents.third_party_sharing:
        if agent_name in {"discovery", "search", "analytics"}:
            violations.append(f"Third-party sharing not consented: {agent_name} blocked")
            return False, violations

    return True, violations


class PrivacyGuardrailService:
    def __init__(self):
        self._profiles: dict[str, UserPrivacyProfile] = {}

    def get_or_create_profile(self, user_id: str) -> UserPrivacyProfile:
        if user_id not in self._profiles:
            self._profiles[user_id] = UserPrivacyProfile()
        return self._profiles[user_id]

    def update_profile(self, user_id: str, profile: UserPrivacyProfile) -> UserPrivacyProfile:
        self._profiles[user_id] = profile
        return self._profiles[user_id]

    def delete_profile(self, user_id: str) -> bool:
        return bool(self._profiles.pop(user_id, None))

    def export_profile(self, user_id: str) -> Optional[dict]:
        profile = self._profiles.get(user_id)
        if not profile:
            return None
        return {
            "user_id": user_id,
            "profile": profile.model_dump(),
            "exported_at": __import__("datetime").datetime.now().isoformat(),
        }

    async def check_input(self, text: str, user_id: str = "default") -> GuardrailResult:
        if not GUARDRAIL_ENABLED:
            return GuardrailResult(action=GuardrailAction.allowed, sanitized_text=text)

        if not text or not text.strip():
            return GuardrailResult(action=GuardrailAction.allowed, sanitized_text=text)

        profile = self.get_or_create_profile(user_id)

        if profile.privacy_level == PrivacyLevel.strict:
            sanitized, redacted = _rule_based_redact(text)
            if redacted:
                return GuardrailResult(
                    action=GuardrailAction.sanitized,
                    sanitized_text=sanitized,
                    redacted_fields=redacted,
                    explanation=f"PII redacted: {', '.join(redacted)}",
                )
            return GuardrailResult(action=GuardrailAction.allowed, sanitized_text=text)

        llm_result = await _call_llm(SYSTEM_PROMPT_INPUT, text)
        if llm_result:
            try:
                parsed = json.loads(llm_result)
                sanitized = parsed.get("sanitized_text", text)
                redacted = parsed.get("redacted_fields", [])
                if parsed.get("has_pii"):
                    return GuardrailResult(
                        action=GuardrailAction.sanitized,
                        sanitized_text=sanitized,
                        redacted_fields=redacted,
                        explanation=f"LLM detected and redacted: {', '.join(redacted)}",
                    )
                return GuardrailResult(action=GuardrailAction.allowed, sanitized_text=text)
            except (json.JSONDecodeError, KeyError):
                pass

        sanitized, redacted = _rule_based_redact(text)
        if redacted:
            return GuardrailResult(
                action=GuardrailAction.sanitized,
                sanitized_text=sanitized,
                redacted_fields=redacted,
                explanation=f"PII redacted (fallback): {', '.join(redacted)}",
            )
        return GuardrailResult(action=GuardrailAction.allowed, sanitized_text=text)

    async def check_agent_access(
        self,
        agent_name: str,
        data_fields: list[str],
        user_id: str = "default",
    ) -> GuardrailResult:
        if not GUARDRAIL_ENABLED:
            return GuardrailResult(action=GuardrailAction.allowed)

        profile = self.get_or_create_profile(user_id)

        allowed_rule, violations_rule = _rule_based_agent_access(agent_name, data_fields, profile)
        if not allowed_rule:
            return GuardrailResult(
                action=GuardrailAction.blocked,
                violations=violations_rule,
                explanation=violations_rule[0] if violations_rule else "Access denied by rules",
            )

        if profile.privacy_level == PrivacyLevel.open and LLM_API_KEY:
            user_message = (
                f"Agent: {agent_name}\n"
                f"Requested data fields: {', '.join(data_fields)}\n"
                f"Privacy level: {profile.privacy_level.value}\n"
                f"Consents: {profile.consents.model_dump_json()}\n"
                f"Region: {profile.region.value}\n"
            )
            llm_result = await _call_llm(SYSTEM_PROMPT_AGENT_ACCESS, user_message)
            if llm_result:
                try:
                    parsed = json.loads(llm_result)
                    if not parsed.get("allowed", True):
                        return GuardrailResult(
                            action=GuardrailAction.blocked,
                            violations=parsed.get("violations", []),
                            explanation=parsed.get("explanation", "Access denied by LLM"),
                        )
                except (json.JSONDecodeError, KeyError):
                    pass

        return GuardrailResult(action=GuardrailAction.allowed)

    async def check_output(
        self,
        recommendations: list[dict],
        user_id: str = "default",
    ) -> GuardrailResult:
        if not GUARDRAIL_ENABLED:
            return GuardrailResult(action=GuardrailAction.allowed)

        profile = self.get_or_create_profile(user_id)

        if profile.privacy_level == PrivacyLevel.strict:
            for rec in recommendations:
                if any(k in rec for k in ("user_location", "user_name", "inferred_interest")):
                    return GuardrailResult(
                        action=GuardrailAction.flagged,
                        violations=["Strict mode: personal data in recommendations"],
                        explanation="Output contains user personal data in strict mode",
                    )
            return GuardrailResult(action=GuardrailAction.allowed)

        if profile.privacy_level == PrivacyLevel.balanced and "precise_location" in {
            k for rec in recommendations for k in rec
        }:
            return GuardrailResult(
                action=GuardrailAction.flagged,
                violations=["Balanced mode: precise location in output"],
                explanation="Balanced mode prohibits precise location in recommendations",
            )

        if profile.privacy_level == PrivacyLevel.open and LLM_API_KEY:
            recs_text = json.dumps(recommendations, indent=2)
            user_message = f"User privacy level: {profile.privacy_level.value}\nUser consents: {profile.consents.model_dump_json()}\nRecommendations:\n{recs_text}"
            llm_result = await _call_llm(SYSTEM_PROMPT_OUTPUT, user_message)
            if llm_result:
                try:
                    parsed = json.loads(llm_result)
                    if not parsed.get("compliant", True):
                        return GuardrailResult(
                            action=GuardrailAction.flagged,
                            violations=parsed.get("issues", []),
                            explanation=parsed.get("explanation", "Output flagged"),
                        )
                except (json.JSONDecodeError, KeyError):
                    pass

        return GuardrailResult(action=GuardrailAction.allowed)

    async def forget_user(self, user_id: str) -> bool:
        return self.delete_profile(user_id)

    def update_consent(self, user_id: str, consents: PrivacyConsent) -> Optional[UserPrivacyProfile]:
        profile = self._profiles.get(user_id)
        if not profile:
            return None
        profile.consents = consents
        return profile

    def opt_out_of_sale(self, user_id: str) -> Optional[UserPrivacyProfile]:
        profile = self._profiles.get(user_id)
        if not profile:
            return None
        profile.opted_out_of_sale = True
        profile.consents.third_party_sharing = False
        return profile


privacy_guardrail = PrivacyGuardrailService()
