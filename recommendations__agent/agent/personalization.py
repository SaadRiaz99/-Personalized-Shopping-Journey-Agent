"""Preference-based re-ranking of product results.
Uses session preferences (category, price range, brand) to boost or filter results."""

import logging
from typing import Optional

logger = logging.getLogger(__name__)


def _match_budget(price, budget: str) -> bool:
    try:
        b = float(budget)
        return price <= b * 1.2
    except (ValueError, TypeError):
        return True


def personalize_results(
    items: list[dict],
    preferences: dict,
) -> list[dict]:
    if not preferences or not items:
        return items

    prefs = preferences
    scored = []
    for item in items:
        score = 0.0
        category = item.get("category", "")
        price = item.get("price")
        title = str(item.get("title", "")).lower()
        brand_field = str(item.get("brand", "")).lower()

        if "category" in prefs and prefs["category"].lower() in category.lower():
            score += 3.0
        if "brand" in prefs and prefs["brand"].lower() in brand_field:
            score += 2.0
        if "brand" in prefs and prefs["brand"].lower() in title:
            score += 1.0
        if "budget" in prefs and price is not None:
            budget_str = prefs["budget"]
            try:
                budget_val = float(budget_str)
                if price <= budget_val:
                    score += 2.0
                elif price <= budget_val * 1.2:
                    score += 0.5
            except (ValueError, TypeError):
                pass

        scored.append((item, score))

    scored.sort(key=lambda x: -x[1])
    return [item for item, _ in scored]


def expand_budget(preferences: dict) -> dict:
    if "budget" not in preferences:
        return preferences
    try:
        b = float(preferences["budget"])
        preferences["budget"] = str(round(b * 1.2, 2))
    except (ValueError, TypeError):
        pass
    return preferences
