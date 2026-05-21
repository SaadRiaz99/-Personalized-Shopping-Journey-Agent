import json
import os
from typing import Optional

import httpx

from app.models import QueryIntent

LLM_API_KEY = os.getenv("LLM_API_KEY", "")
LLM_ENDPOINT = os.getenv("LLM_ENDPOINT", "https://api.openai.com/v1/chat/completions")
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")


SYSTEM_PROMPT = """You are a shopping intent parser. Extract structured information from the user's shopping query.

Respond with ONLY valid JSON (no markdown, no backticks) in this exact format:
{
  "category": "product category or null if unclear",
  "budget": null or a number (numeric value only, no currency symbols),
  "budget_currency": "USD" (default if not specified),
  "occasion": "the occasion like birthday, wedding, holiday, etc. or null",
  "style_preferences": ["list", "of", "style", "keywords"],
  "urgency": "immediate" or "soon" or "not_urgent" or null
}

Interpret ambiguous language intelligently. For example:
- "not too expensive" → budget under 100
- "something nice for wife's birthday" → occasion: birthday, category: gifts
- "need it ASAP" → urgency: immediate
- "formal wear for a wedding" → occasion: wedding, style_preferences: ["formal"]
- "budget is around 50 bucks" → budget: 50, budget_currency: USD

If the query is vague, use your best judgment rather than returning nulls."""


async def parse_intent(query: str) -> QueryIntent:
    if not query or not query.strip():
        return QueryIntent(raw_query=query)

    if not LLM_API_KEY:
        return _rule_based_fallback(query)

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
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": query},
                    ],
                    "temperature": 0.1,
                    "max_tokens": 300,
                },
            )
            resp.raise_for_status()
            data = resp.json()
            content = data["choices"][0]["message"]["content"].strip()
            content = content.removeprefix("```json").removeprefix("```").removesuffix("```").strip()
            parsed = json.loads(content)
            return QueryIntent(
                category=parsed.get("category"),
                budget=parsed.get("budget"),
                budget_currency=parsed.get("budget_currency", "USD"),
                occasion=parsed.get("occasion"),
                style_preferences=parsed.get("style_preferences", []),
                urgency=parsed.get("urgency"),
                raw_query=query,
            )
    except Exception:
        return _rule_based_fallback(query)


def _rule_based_fallback(query: str) -> QueryIntent:
    q = query.lower()

    categories = {
        "electronics": ["electronics", "gadget", "phone", "laptop", "computer", "tablet", "headphone", "speaker", "tv", "camera", "smartwatch"],
        "clothing": ["clothing", "clothes", "dress", "shirt", "pants", "jeans", "jacket", "coat", "sweater", "hoodie", "t-shirt", "outfit", "wear", "apparel", "fashion"],
        "footwear": ["shoes", "sneakers", "boots", "sandals", "footwear"],
        "accessories": ["accessories", "watch", "belt", "bag", "wallet", "jewelry", "necklace", "ring", "bracelet", "earrings", "sunglasses"],
        "home": ["home", "furniture", "decor", "kitchen", "bedding", "towel", "lamp", "couch", "sofa", "table", "chair"],
        "beauty": ["beauty", "skincare", "makeup", "cosmetics", "perfume", "fragrance", "lotion", "cream", "shampoo"],
        "sports": ["sports", "fitness", "gym", "exercise", "yoga", "running", "outdoor", "camping", "hiking"],
        "books": ["book", "books", "novel", "magazine"],
        "toys": ["toy", "toys", "game", "board game", "puzzle", "lego"],
        "food": ["food", "snack", "chocolate", "gourmet", "wine", "coffee", "tea"],
        "gifts": ["gift", "present", "surprise"],
    }

    occasions = {
        "birthday": ["birthday", "bday", "birth day"],
        "wedding": ["wedding", "anniversary", "marriage"],
        "holiday": ["christmas", "xmas", "holiday", "new year", "easter", "thanksgiving", "halloween", "valentine"],
        "graduation": ["graduation", "grad"],
        "housewarming": ["housewarming", "new home"],
        "baby_shower": ["baby shower", "new baby", "newborn"],
    }

    urgencies = {
        "immediate": ["asap", "urgent", "immediate", "right away", "quick", "fast", "today", "now", "need it soon", "hurry"],
        "soon": ["soon", "this week", "within", "next few days", "in a hurry"],
        "not_urgent": ["no rush", "not urgent", "whenever", "browsing", "just looking", "eventually"],
    }

    category = None
    for cat, keywords in categories.items():
        if any(kw in q for kw in keywords):
            category = cat
            break

    occasion = None
    for occ, keywords in occasions.items():
        if any(kw in q for kw in keywords):
            occasion = occ
            break

    urgency = None
    for urg, keywords in urgencies.items():
        if any(kw in q for kw in keywords):
            urgency = urg
            break

    budget = None
    import re
    money_patterns = [
        r"(?:under|below|less than|max|budget|around|about|roughly|~)\s*\$?(\d+(?:\.\d{1,2})?)",
        r"\$?(\d+(?:\.\d{1,2})?)\s*(?:dollars?|bucks?|usd)",
        r"(?:price|cost|spend|budget).{0,20}\$?(\d+(?:\.\d{1,2})?)",
    ]
    for pat in money_patterns:
        match = re.search(pat, q)
        if match:
            try:
                budget = float(match.group(1))
            except ValueError:
                pass
            break

    style_preferences = []
    style_keywords = {
        "casual": ["casual", "everyday", "comfy", "comfortable", "relaxed"],
        "formal": ["formal", "professional", "business", "office", "suit", "tie", "elegant"],
        "modern": ["modern", "contemporary", "sleek", "minimalist", "trendy"],
        "vintage": ["vintage", "retro", "classic", "old school", "antique"],
        "luxury": ["luxury", "premium", "high-end", "expensive", "designer", "luxurious"],
        "budget": ["budget", "cheap", "affordable", "inexpensive", "economical", "value", "bargain", "discount", "sale"],
        "colorful": ["colorful", "bright", "vibrant", "color"],
        "neutral": ["neutral", "monochrome", "black", "white", "gray", "beige"],
        "outdoor": ["outdoor", "nature", "camping", "garden", "patio"],
        "techy": ["tech", "smart", "digital", "wireless", "bluetooth", "gadget"],
    }
    for style, keywords in style_keywords.items():
        if any(kw in q for kw in keywords):
            style_preferences.append(style)

    return QueryIntent(
        category=category,
        budget=budget,
        budget_currency="USD",
        occasion=occasion,
        style_preferences=style_preferences,
        urgency=urgency,
        raw_query=query,
    )
