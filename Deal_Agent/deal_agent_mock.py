"""
Deal Agent - MOCK MODE (No API Key Needed)
Bilkul same agent, bina internet ke.
Run: python deal_agent_mock.py
"""

import json
import re

with open("promotions.json") as f:
    DATA = json.load(f)

PROMOTIONS = DATA["promotions"]
USERS      = DATA["users"]


def search_promotions(category, cart_total):
    results = [
        p for p in PROMOTIONS
        if (p["category"] == "all" or p["category"] == category.lower())
        and cart_total >= p["min_order"]
    ]
    return results


def get_loyalty(user_id):
    return next((u for u in USERS if u["user_id"] == user_id), None)


def apply_best_discount(cart_total, promos, user, points_to_use=0):
    price = cart_total
    applied = []
    total_saved = 0.0

    non_stack = [p for p in promos if not p["stackable"]]
    stackable  = [p for p in promos if p["stackable"]]

    if non_stack:
        def savings(p):
            if p["type"] == "percentage":
                return price * p["value"] / 100
            return p["value"]
        best = max(non_stack, key=savings)
        if best["type"] == "percentage":
            amt = price * best["value"] / 100
        else:
            amt = best["value"]
        price -= amt
        total_saved += amt
        applied.append(f"{best['code']}: {best['description']} = -Rs. {amt:.0f}")

    for p in stackable:
        if price >= p["min_order"]:
            if p["type"] == "fixed":
                price -= p["value"]
                total_saved += p["value"]
                applied.append(f"{p['code']}: {p['description']} = -Rs. {p['value']:.0f}")
            elif p["type"] in ("percentage", "bundle"):
                amt = price * p["value"] / 100
                price -= amt
                total_saved += amt
                applied.append(f"{p['code']}: {p['description']} = -Rs. {amt:.0f}")

    if user and points_to_use > 0 and user["points"] >= points_to_use:
        discount = points_to_use * user["value_per_point"]
        price -= discount
        total_saved += discount
        applied.append(f"Loyalty ({points_to_use} pts) = -Rs. {discount:.0f}")

    return {
        "original": cart_total,
        "applied": applied,
        "final": round(max(price, 0), 2),
        "saved": round(total_saved, 2),
        "saved_pct": round((total_saved / cart_total) * 100, 1) if cart_total > 0 else 0,
    }


def handle_input(user_input, category, cart_total, user_id):
    text = user_input.lower()

    if any(w in text for w in ["list", "show all", "all deals", "all promo", "kya deals"]):
        lines = ["\nAll Available Promotions:"]
        for p in PROMOTIONS:
            lines.append(f"  {p['code']}: {p['description']} (min Rs. {p['min_order']})")
        return "\n".join(lines)

    if any(w in text for w in ["loyalty", "points", "mera point", "mere points"]):
        user = get_loyalty(user_id)
        if user:
            val = user["points"] * user["value_per_point"]
            return (f"Your Loyalty Account:\n"
                    f"  Tier   : {user['tier'].upper()}\n"
                    f"  Points : {user['points']}\n"
                    f"  Worth  : Rs. {val:.0f}")
        return "No loyalty account found for your user ID."

    if any(w in text for w in ["best deal", "apply", "discount", "saving", "save", "calculate", "kitna bachega"]):
        promos = search_promotions(category, cart_total)
        user   = get_loyalty(user_id)
        points_to_use = user["points"] if user else 0

        result = apply_best_discount(cart_total, promos, user, points_to_use)

        lines = ["\nBest Deal Applied:"]
        lines.append(f"  Original Price : Rs. {result['original']:.0f}")
        if result["applied"]:
            for a in result["applied"]:
                lines.append(f"  (-) {a}")
        else:
            lines.append("  No promotions applicable")
        lines.append(f"  Final Price    : Rs. {result['final']:.0f}")
        lines.append(f"  Total Saved    : Rs. {result['saved']:.0f} ({result['saved_pct']}% off)")
        if result["saved_pct"] >= 20:
            lines.append("\n  Great savings! Well done!")
        return "\n".join(lines)

    if any(w in text for w in ["promo", "promotion", "deal", "offer", "koi deal"]):
        promos = search_promotions(category, cart_total)
        if not promos:
            return "No promotions available for your cart right now."
        lines = [f"\n{len(promos)} Promotion(s) found for {category} (Rs. {cart_total:.0f}):"]
        for p in promos:
            lines.append(f"  {p['code']}: {p['description']}")
        return "\n".join(lines)

    return ("I can help you with:\n"
            "  - 'show all deals'     : list every promotion\n"
            "  - 'check my points'    : see loyalty balance\n"
            "  - 'apply best deal'    : calculate max savings\n"
            "  - 'show promotions'    : deals for your cart\n"
            "  Type 'exit' to quit.")


def main():
    print("=" * 60)
    print("  DEAL AGENT - MOCK MODE (No API Key)")
    print("  Built by Hashir | SMIT Batch")
    print("=" * 60)
    print("\nSetup your cart:\n")

    user_id    = input("  User ID (U001 - U020)                     : ").strip() or "U001"
    category   = input("  Category (electronics/fashion/books/home) : ").strip() or "electronics"
    cart_total = float(input("  Cart Total in Rs.                         : ").strip() or "1500")

    print("\n" + "=" * 60)
    print("  Deal Agent ready! Ask me about deals & savings.")
    print("  Type 'exit' to quit.")
    print("=" * 60 + "\n")

    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break

        if not user_input:
            continue
        if user_input.lower() in ("exit", "quit", "bye"):
            print("Deal Agent: Goodbye! Happy saving!")
            break

        response = handle_input(user_input, category, cart_total, user_id)
        print(f"\nDeal Agent: {response}\n")


if __name__ == "__main__":
    main()
