"""
Deal Agent - The LLM drives all decisions.
- Python: parses user message, calls tools in parallel
- LLM (qwen2.5:1.5b): receives ALL tool data, analyzes, decides best deal, explains why
"""
import json
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any
from openai import OpenAI

PROMOTIONS_DB = {
    "promo_001": {"id": "promo_001", "name": "Summer Sale", "type": "percent_off", "value": 15, "min_spend": 50, "active": True},
    "promo_002": {"id": "promo_002", "name": "Free Shipping", "type": "free_shipping", "value": 0, "min_spend": 30, "active": True},
    "promo_003": {"id": "promo_003", "name": "BOGO Sneakers", "type": "bogo", "value": 50, "min_spend": 100, "active": True},
    "promo_004": {"id": "promo_004", "name": "Flash 20%", "type": "percent_off", "value": 20, "min_spend": 75, "active": False},
    "promo_005": {"id": "promo_005", "name": "$10 Off", "type": "flat_off", "value": 10, "min_spend": 40, "active": True},
}

LOYALTY_DB = {}
_tier_config = {"platinum": {"count": 50, "points_range": (5000, 10000), "mult_range": (2.0, 3.0)},
                "gold": {"count": 100, "points_range": (2000, 5000), "mult_range": (1.5, 2.0)},
                "silver": {"count": 150, "points_range": (500, 2000), "mult_range": (1.0, 1.5)},
                "bronze": {"count": 150, "points_range": (0, 500), "mult_range": (0.5, 1.0)}}
import random; random.seed(42)
_names = ["Alice","Bob","Charlie","Diana","Eve","Frank","Grace","Henry","Ivy","Jack","Kate","Leo","Mia","Noah","Olivia","Pete","Quinn","Rose","Sam","Tina","Uma","Vince","Wendy","Xander","Yara","Zack",
          "Aiden","Bella","Carter","Daisy","Eli","Faith","Gabe","Hazel","Ian","Jade","Kai","Luna","Milo","Nora","Owen","Piper","Rex","Sage","Theo","Violet","Wade","Xena","Yuki","Zara",
          "Adam","Beth","Cole","Drew","Elle","Finn","Gia","Hank","Iris","Jake","Kara","Liam","Maya","Nash","Olive","Paul","Raya","Seth","Tess","Uriel","Vera","Wyatt","Xia","Yves","Zion",
          "Aria","Blake","Cora","Duke","Eden","Finnick","Gemma","Hugo","Isla","Jude","Kira","Luke","Maeve","Nick","Opal","Pace","Romy","Shane","Tori","Ulric","Vega","Wren","Xiomara","Yosef","Zuri",
          "Alec","Brie","Cade","Demi","Ewan","Faye","Gino","Hana","Ivan","Juno","Kurt","Lana","Mack","Nina","Ozzy","Pia","Rico","Suki","Troy","Una","Vic","Wylie","Xylo","Yara","Zeke"]
_tiers_order = []
for t, c in _tier_config.items():
    _tiers_order.extend([t] * c["count"])
random.shuffle(_tiers_order)
for i in range(1, 451):
    uid = f"user_{i:03d}"
    tier = _tiers_order[i - 1]
    cfg = _tier_config[tier]
    pts = random.randint(*cfg["points_range"])
    mult = round(random.uniform(*cfg["mult_range"]), 1)
    n = _names[(i - 1) % len(_names)]
    LOYALTY_DB[uid] = {"user_id": uid, "name": n, "tier": tier, "points": pts, "multiplier": mult}

CATALOG = {
    "item_001": {"id": "item_001", "name": "Running Shoes", "category": "footwear", "price": 89.99},
    "item_002": {"id": "item_002", "name": "Yoga Mat", "category": "fitness", "price": 24.99},
    "item_003": {"id": "item_003", "name": "Water Bottle", "category": "accessories", "price": 14.99},
    "item_004": {"id": "item_004", "name": "Gym Bag", "category": "accessories", "price": 39.99},
    "item_005": {"id": "item_005", "name": "Protein Powder", "category": "nutrition", "price": 44.99},
    "item_006": {"id": "item_006", "name": "Resistance Bands", "category": "fitness", "price": 19.99},
    "item_007": {"id": "item_007", "name": "Foam Roller", "category": "fitness", "price": 29.99},
    "item_008": {"id": "item_008", "name": "Wireless Earbuds", "category": "electronics", "price": 59.99},
}

BUNDLE_DB = [
    {"id": "bundle_001", "name": "Starter Fitness", "items": ["item_002", "item_003", "item_006"], "discount": 10},
    {"id": "bundle_002", "name": "Runner's Pack", "items": ["item_001", "item_005", "item_008"], "discount": 15},
    {"id": "bundle_003", "name": "Recovery Kit", "items": ["item_006", "item_007", "item_003"], "discount": 12},
]

COUPONS_DB = [
    {"code": "WELCOME10", "type": "percent_off", "value": 10, "min_spend": 20, "max_uses": 100, "used": 45},
    {"code": "LOYAL20", "type": "percent_off", "value": 20, "min_spend": 50, "max_uses": 50, "used": 12, "min_tier": "gold"},
    {"code": "FREESHIP", "type": "free_shipping", "value": 0, "min_spend": 25, "max_uses": 200, "used": 88},
    {"code": "SAVE5", "type": "flat_off", "value": 5, "min_spend": 30, "max_uses": 500, "used": 312},
    {"code": "PLAT50", "type": "percent_off", "value": 25, "min_spend": 100, "max_uses": 20, "used": 3, "min_tier": "platinum"},
]

NAME_TO_ITEM = {v["name"].lower(): k for k, v in CATALOG.items()}

def query_promotions(min_spend: float | None = None, active_only: bool = True) -> dict:
    results = [p for p in PROMOTIONS_DB.values() if not active_only or p["active"]]
    if min_spend is not None:
        results = [p for p in results if p["min_spend"] <= min_spend]
    return {"promotions": results, "count": len(results)}

def check_loyalty_tier(user_id: str) -> dict:
    user = LOYALTY_DB.get(user_id)
    return {"user": user} if user else {"error": "User not found"}

def optimize_bundles(cart_items: list[str] | None = None) -> dict:
    if not cart_items:
        return {"bundles": BUNDLE_DB, "note": "All available bundles"}
    cart_set = set(cart_items)
    matches = []
    for b in BUNDLE_DB:
        overlap = cart_set & set(b["items"])
        match_pct = len(overlap) / len(b["items"]) * 100 if b["items"] else 0
        matches.append({**b, "cart_overlap_pct": round(match_pct, 1)})
    matches.sort(key=lambda x: x["cart_overlap_pct"], reverse=True)
    return {"bundles": matches}

def apply_coupons(user_id: str, subtotal: float) -> dict:
    user = LOYALTY_DB.get(user_id)
    user_tier = user["tier"] if user else "bronze"
    valid = []
    for c in COUPONS_DB:
        if c["used"] >= c["max_uses"]:
            continue
        if subtotal < c["min_spend"]:
            continue
        min_tier = c.get("min_tier", "bronze")
        tier_rank = {"bronze": 0, "silver": 1, "gold": 2, "platinum": 3}
        if tier_rank.get(user_tier, 0) < tier_rank.get(min_tier, 0):
            continue
        valid.append(c)
    valid.sort(key=lambda x: x["value"], reverse=True)
    return {"available_coupons": valid, "count": len(valid)}

