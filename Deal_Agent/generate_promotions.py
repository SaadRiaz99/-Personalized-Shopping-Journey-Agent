"""
Run this once to generate promotions.json data file.
python generate_promotions.py
"""

import json
import random

random.seed(42)

promotions = []
promo_id = 1

categories = ["electronics", "fashion", "books", "home", "sports", "beauty", "groceries", "all"]

percentage_deals = [
    ("SAVE5",   5,   0,    "5% off on all orders"),
    ("SAVE10",  10,  500,  "10% off on orders above Rs. 500"),
    ("SAVE15",  15,  1000, "15% off on orders above Rs. 1000"),
    ("SAVE20",  20,  1500, "20% off on orders above Rs. 1500"),
    ("SAVE25",  25,  2000, "25% off on orders above Rs. 2000"),
    ("SAVE30",  30,  3000, "30% off on orders above Rs. 3000"),
]

fixed_deals = [
    ("FLAT100",  100,  500,  "Rs. 100 off on orders above Rs. 500"),
    ("FLAT200",  200,  1000, "Rs. 200 off on orders above Rs. 1000"),
    ("FLAT500",  500,  2500, "Rs. 500 off on orders above Rs. 2500"),
    ("FLAT1000", 1000, 5000, "Rs. 1000 off on orders above Rs. 5000"),
]

category_deals = [
    ("TECH10",    10, 500,  "electronics", "10% off on Electronics"),
    ("FASHION20", 20, 300,  "fashion",     "20% off on Fashion"),
    ("BOOK15",    15, 200,  "books",       "15% off on Books"),
    ("HOME12",    12, 800,  "home",        "12% off on Home items"),
    ("SPORT18",   18, 600,  "sports",      "18% off on Sports"),
    ("BEAUTY25",  25, 400,  "beauty",      "25% off on Beauty"),
    ("FOOD8",     8,  300,  "groceries",   "8% off on Groceries"),
]

bundle_deals = [
    ("BUNDLE10", 10, 0, "all", "10% off when buying 2+ items"),
    ("BUNDLE15", 15, 0, "all", "15% off when buying 3+ items"),
    ("BUNDLE20", 20, 0, "all", "20% off when buying 4+ items"),
]

for code, value, min_order, desc in percentage_deals:
    promotions.append({
        "promo_id": f"P{promo_id:03d}",
        "code": code,
        "type": "percentage",
        "value": value,
        "min_order": min_order,
        "category": "all",
        "description": desc,
        "stackable": value <= 10,
        "expiry": "2026-12-31"
    })
    promo_id += 1

for code, value, min_order, desc in fixed_deals:
    promotions.append({
        "promo_id": f"P{promo_id:03d}",
        "code": code,
        "type": "fixed",
        "value": value,
        "min_order": min_order,
        "category": "all",
        "description": desc,
        "stackable": True,
        "expiry": "2026-12-31"
    })
    promo_id += 1

for code, value, min_order, category, desc in category_deals:
    promotions.append({
        "promo_id": f"P{promo_id:03d}",
        "code": code,
        "type": "percentage",
        "value": value,
        "min_order": min_order,
        "category": category,
        "description": desc,
        "stackable": False,
        "expiry": "2026-12-31"
    })
    promo_id += 1

for code, value, min_order, category, desc in bundle_deals:
    promotions.append({
        "promo_id": f"P{promo_id:03d}",
        "code": code,
        "type": "bundle",
        "value": value,
        "min_order": min_order,
        "category": category,
        "description": desc,
        "stackable": True,
        "expiry": "2026-12-31"
    })
    promo_id += 1

loyalty_tiers = {
    "bronze":   {"min_points": 0,    "max_points": 999,  "points_per_rupee": 1,   "value_per_point": 0.25},
    "silver":   {"min_points": 1000, "max_points": 4999, "points_per_rupee": 2,   "value_per_point": 0.50},
    "gold":     {"min_points": 5000, "max_points": 19999,"points_per_rupee": 3,   "value_per_point": 0.75},
    "platinum": {"min_points": 20000,"max_points": 999999,"points_per_rupee": 5,  "value_per_point": 1.00},
}

users = []
for i in range(1, 21):
    tier = random.choice(["bronze", "silver", "gold", "platinum"])
    tier_info = loyalty_tiers[tier]
    points = random.randint(tier_info["min_points"], min(tier_info["max_points"], tier_info["min_points"] + 5000))
    users.append({
        "user_id": f"U{i:03d}",
        "name": f"Customer {i}",
        "tier": tier,
        "points": points,
        "value_per_point": tier_info["value_per_point"],
    })

data = {
    "promotions": promotions,
    "loyalty_tiers": loyalty_tiers,
    "users": users
}

with open("promotions.json", "w") as f:
    json.dump(data, f, indent=2)

print(f"Generated promotions.json")
print(f"  Total promotions : {len(promotions)}")
print(f"  Total users      : {len(users)}")
print(f"  Loyalty tiers    : {list(loyalty_tiers.keys())}")
