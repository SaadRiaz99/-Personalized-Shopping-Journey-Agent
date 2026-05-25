import re
from typing import Optional

from app.models import PrivacyRegion, SafetyCheckResult

RESTRICTED_CATEGORIES = {
    "weapons": ["weapon", "gun", "firearm", "rifle", "pistol", "shotgun", "ammo", "ammunition", "knife", "blade", "sword", "explosive", "bomb"],
    "drugs": ["drug", "cocaine", "heroin", "mdma", "ecstasy", "meth", "amphetamine", "lsd", "weed", "marijuana", "cannabis", "opioid", "narcotic", "pill", "substance abuse"],
    "adult": ["adult", "porn", "xxx", "explicit", "nsfw", "sex toy", "dildo", "vibrator", "adult content"],
    "alcohol_tobacco": ["alcohol", "beer", "wine", "liquor", "vodka", "whiskey", "cigarette", "tobacco", "vape", "nicotine", "cigar", "smoking"],
    "gambling": ["gambling", "casino", "lottery", "bet", "betting", "poker", "roulette", "slot machine"],
    "counterfeit": ["counterfeit", "fake", "replica", "knockoff", "forged", "illegal copy", "bootleg"],
    "hacking": ["hack", "hacker", "malware", "virus", "ransomware", "phishing", "cracked", "jailbreak"],
}

RESTRICTED_CATEGORIES_GDPR = {
    "prescription": ["prescription", "medicine", "medication", "pharmaceutical", "antibiotic", "painkiller", "sedative", "antidepressant", "controlled substance"],
}


async def check_safety(
    query: str,
    region: PrivacyRegion = PrivacyRegion.none,
) -> SafetyCheckResult:
    if not query or not query.strip():
        return SafetyCheckResult(allowed=True)

    q = query.lower()

    for category, keywords in RESTRICTED_CATEGORIES.items():
        for kw in keywords:
            if re.search(rf'\b{re.escape(kw)}\b', q):
                return SafetyCheckResult(
                    allowed=False,
                    blocked_category=category,
                    blocked_reason=f"Query contains restricted category: {category}",
                )

    if region in (PrivacyRegion.gdpr, PrivacyRegion.ccpa):
        for category, keywords in RESTRICTED_CATEGORIES_GDPR.items():
            for kw in keywords:
                if re.search(rf'\b{re.escape(kw)}\b', q):
                    return SafetyCheckResult(
                        allowed=False,
                        blocked_category=category,
                        blocked_reason=f"Query contains region-restricted category: {category} (enforced by {region.value.upper()})",
                    )

    return SafetyCheckResult(allowed=True)
