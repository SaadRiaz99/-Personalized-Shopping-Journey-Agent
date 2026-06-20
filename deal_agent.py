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

TIER_BENEFITS = {
    "platinum": "PLAT50 coupon (25% off $100+), free shipping, priority support, gift wrap, 2.0x-3.0x points",
    "gold": "LOYAL20 coupon (20% off $50+), free shipping, birthday reward, double points days, 1.5x-2.0x points",
    "silver": "Free shipping, early sale access, birthday reward, 1.0x-1.5x points",
    "bronze": "WELCOME10 coupon (10% off $20+), birthday reward, standard points, 0.5x-1.0x points",
}
import random; random.seed(42)
_names = ["Alice","Bob","Charlie","Diana","Eve","Frank","Grace","Henry","Ivy","Jack","Kate","Leo","Mia","Noah","Olivia","Pete","Quinn","Rose","Sam","Tina","Uma","Vince","Wendy","Xander","Yara","Zack",
          "Aiden","Bella","Carter","Daisy","Eli","Faith","Gabe","Hazel","Ian","Jade","Kai","Luna","Milo","Nora","Owen","Piper","Rex","Sage","Theo","Violet","Wade","Xena","Yuki","Zara",
          "Adam","Beth","Cole","Drew","Elle","Finn","Gia","Hank","Iris","Jake","Kara","Liam","Maya","Nash","Olive","Paul","Raya","Seth","Tess","Uriel","Vera","Wyatt","Xia","Yves","Zion",
          "Aria","Blake","Cora","Duke","Eden","Finnick","Gemma","Hugo","Isla","Jude","Kira","Luke","Maeve","Nick","Opal","Pace","Romy","Shane","Tori","Ulric","Vega","Wren","Xiomara","Yosef","Zuri",
          "Alec","Brie","Cade","Demi","Ewan","Faye","Gino","Hana","Ivan","Juno","Kurt","Lana","Mack","Nina","Ozzy","Pia","Rico","Suki","Troy","Una","Vic","Wylie","Xylo","Zoya","Zeke"]
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

SYSTEM_PROMPT = """You are a deal agent. Answer questions about deals, cart items, coupons, promotions, bundles, loyalty, discounts, and pricing.

RESPONSE RULES:
- Use ONLY plain text. No markdown, no stars, no dashes, no bullets, no emojis.
- Only letters, numbers, spaces, $, and new lines allowed.
- Always greet known users by name when they provide a valid user ID.
- Do NOT recalculate. Use the savings values already provided.
- State the best deal and explain why (highest savings, best value).
- Do NOT repeat the user message. Do NOT say "Customer message:" or "User said:".
- Be concise. Use short lines.

EXAMPLES:

User: "write me a poem"
You: I am a deal agent. My task is to help you find the best deals and checkout savings. I cannot help with this.

User: "any deals for me?" (cart empty)
You: Your cart is empty. Add some items first and I will find the best deals for you.

User: "user_001, what tier am I"
Cart: Alice (Gold tier, 3200 points, 1.5x multiplier)
You: Alice, you are Gold tier with 3200 points and a 1.5x multiplier.

User: "user_002, my cart has Protein Powder and Wireless Earbuds"
Deals: PLAT50 saves $26.25 (final $78.73), LOYAL20 saves $21.00 (final $83.98), WELCOME10 saves $10.50 (final $94.48)
Best deal: PLAT50
You: Bob, the best deal is PLAT50 which saves you $26.25 and brings your total to $78.73. That is more than LOYAL20 at $21.00 or WELCOME10 at $10.50.

User: "I have Running Shoes and Yoga Mat" (guest)
Deals: Runner's Pack saves $17.25 (final $97.73), WELCOME10 saves $11.50 (final $103.48), SAVE5 saves $5.00 (final $109.98)
Best deal: Runner's Pack
You: As a guest your best option is Runner's Pack saving you $17.25 with a final of $97.73. WELCOME10 saves $11.50 and SAVE5 saves $5.00.

User: "what is my loyalty tier" (guest)
You: Sorry, you are a guest. You don't have a loyalty account. Sign up to earn rewards.

User: "what deals do you have"
Promotions: Summer Sale 15% off, Free Shipping, BOGO Sneakers, $10 Off
Coupons: WELCOME10 10% off, LOYAL20 20% off, FREESHIP free shipping, SAVE5 $5 off, PLAT50 25% off
Bundles: Starter Fitness 10% off, Runner's Pack 15% off, Recovery Kit 12% off
You: Here are the current deals.
Promotions: Summer Sale 15% off on orders over $50, Free Shipping on orders over $30, BOGO Sneakers 50% off on orders over $100, $10 Off on orders over $40.
Coupons: WELCOME10 10% off minimum $20 bronze+, LOYAL20 20% off minimum $50 gold+, FREESHIP free shipping minimum $25, SAVE5 $5 off minimum $30, PLAT50 25% off minimum $100 platinum+.
Bundles: Starter Fitness 10% off (Yoga Mat, Water Bottle, Resistance Bands), Runner's Pack 15% off (Running Shoes, Protein Powder, Wireless Earbuds), Recovery Kit 12% off (Resistance Bands, Foam Roller, Water Bottle).
Add items to your cart and I will find the best deal for you.

User: "help me"
You: I can help you save money. Tell me your user ID and cart items, ask about your loyalty tier, or name some items and I will find deals for you. What would you like?

User: "what are my loyalty benefits" (Gold tier)
Cart: Alice, Gold tier, 3338 points, 1.9x multiplier
Benefits: LOYAL20 coupon (20% off $50+), free shipping, birthday reward, double points days, 1.5x-2.0x points
You: Alice, as a Gold member you get LOYAL20 (20% off $50+), free shipping, birthday reward, and double points days. You earn points at 1.9x and have 3338 points.

User: "what perks do I get" (Platinum tier)
Cart: Bob, Platinum tier, 7721 points, 2.8x multiplier
Benefits: PLAT50 coupon (25% off $100+), free shipping, priority support, gift wrap, 2.0x-3.0x points
You: Bob, your Platinum perks include PLAT50 (25% off $100+), free shipping, priority support, gift wrap, and 2.8x points. You have 7721 points.

Now respond to the user below. Follow the patterns above exactly."""



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


NAME_TO_USER = {v["name"].lower(): k for k, v in LOYALTY_DB.items()}

def parse_user_message(msg: str) -> dict:
    info: dict[str, Any] = {"user_id": None, "name": None, "name_mentioned": False, "invalid_user_id": False, "cart_item_ids": [], "items": [], "subtotal": 0.0}
    msg_lower = msg.lower()

    # Detect user ID attempt: user_XXX, user XXX, or userXXX
    uid_attempt = re.search(r'user_\w+|\buser \d+|\buser\d{3}\b', msg_lower)
    if uid_attempt:
        uid_raw = uid_attempt.group(0)
        uid = uid_raw.replace(" ", "_")
        info["user_id"] = uid
        valid_format = bool(re.match(r'user_\d{3}$', uid))
        if valid_format:
            num = int(uid.split("_")[1])
            if num < 1 or num > 450:
                info["invalid_user_id"] = True
            elif uid in LOYALTY_DB:
                info["name"] = LOYALTY_DB[uid]["name"]
        else:
            info["invalid_user_id"] = True
    for name, uid in NAME_TO_USER.items():
        if name in msg_lower:
            info["name_mentioned"] = True
            break
    found_items = []
    for name, item_id in NAME_TO_ITEM.items():
        if name in msg_lower:
            found_items.append(item_id)
    info["cart_item_ids"] = found_items
    info["items"] = [CATALOG[i] for i in found_items]
    info["subtotal"] = round(sum(CATALOG[i]["price"] for i in found_items), 2)
    return info


def format_currency(amount: float) -> str:
    return f"${amount:.2f}"


def compute_all_deals(coupons: list, bund: list, subtotal: float) -> dict:
    """Pre-compute all deal savings. Returns sorted list + best deal."""
    deals = []
    for c in coupons:
        if c["type"] == "free_shipping":
            deals.append({"name": c["code"], "savings": 0.0, "final": subtotal, "desc": "free shipping"})
        elif c["type"] == "percent_off":
            sav = round(subtotal * c["value"] / 100, 2)
            deals.append({"name": c["code"], "savings": sav, "final": round(subtotal - sav, 2), "desc": f"{c['value']}% off"})
        elif c["type"] == "flat_off":
            sav = min(float(c["value"]), subtotal)
            deals.append({"name": c["code"], "savings": sav, "final": round(subtotal - sav, 2), "desc": f"${c['value']} off"})
    for b in bund:
        if b.get("cart_overlap_pct", 0) > 0:
            sav = round(subtotal * b["discount"] / 100, 2)
            deals.append({"name": b["name"], "savings": sav, "final": round(subtotal - sav, 2), "desc": f"{b['discount']}% off"})
    deals.sort(key=lambda x: x["savings"], reverse=True)
    best = deals[0] if deals else None
    return {"deals": deals, "best": best}


def build_prompt(parsed: dict, data: dict, user_message: str = "") -> dict:
    """Build prompt with pre-computed deals. Model explains the best choice."""

    items = parsed.get("items", [])
    subtotal = parsed.get("subtotal", 0.0)
    uid = parsed.get("user_id")

    lines = [f"Cart: {' + '.join(it['name'] for it in items) or '(empty)'}"]
    lines.append(f"Subtotal: ${subtotal:.2f}")

    loyalty = data.get("loyalty")
    if loyalty and loyalty.get("user"):
        u = loyalty["user"]
        lines.append(f"User: {u['name']}, {u['tier'].title()} tier, {u['points']} points, {u['multiplier']}x multiplier")
        lines.append(f"Always greet this user by their name ({u['name']}) in your response.")
    elif uid:
        lines.append("User: Unknown")
    else:
        lines.append("User: Guest")

    is_loyalty_q = any(w in user_message.lower() for w in ["loyalty", "tier", "level", "points", "status", "member", "rank", "benefits", "perks", "bronze", "silver", "gold", "platinum"])
    if is_loyalty_q and loyalty and loyalty.get("user"):
        u = loyalty["user"]
        benefits = TIER_BENEFITS.get(u["tier"], "")
        if benefits:
            lines.append(f"Benefits of {u['tier'].title()} tier: {benefits}")
    if not items:
        if is_loyalty_q and loyalty and loyalty.get("user"):
            lines.append("\nCart is empty. Answer their loyalty question including the benefits. Then mention the cart is empty.")
        else:
            lines.append("\nCart is empty. Do not list any coupons or deals. Just tell the user their cart is empty.")
    else:
        coupons = data.get("coupons", {}).get("available_coupons", [])
        bund = data.get("bundles", {}).get("bundles", [])
        deals_info = compute_all_deals(coupons, bund, subtotal)
        has_deals = bool(deals_info["deals"])

        if deals_info["deals"]:
            lines.append("\nDeals (sorted by savings, highest first):")
            for i, d in enumerate(deals_info["deals"], 1):
                lines.append(f"  {i}. {d['name']}: {d['desc']}, saves ${d['savings']:.2f}, final ${d['final']:.2f}")
            lines.append(f"\nBest deal: {deals_info['best']['name']} saves ${deals_info['best']['savings']:.2f}.")
            lines.append("Your response MUST use the savings values above exactly. Do not calculate anything.")
        else:
            lines.append("\nNo deals or coupons apply to this cart. Do not say best deal. Do not list any options.")
        lines.append("STRICT: Plain text only. No markdown, stars, dashes, bullets, emojis, or special chars.")

    return {"prompt": "\n".join(lines)}


class DealAgent:
    """LLM-driven agent. Python handles I/O, model decides the best deal."""

    def __init__(self, api_key: str = "ollama", model: str = "minimax-m2.5:cloud", base_url: str | None = "http://localhost:11434/v1"):
        self.model = model
        self.client = OpenAI(api_key=api_key, base_url=base_url) if base_url else None

    def run(self, user_message: str, accumulated_cart: dict | None = None, history: list | None = None) -> dict:
        parsed = parse_user_message(user_message)

        if accumulated_cart:
            existing_ids = set(parsed["cart_item_ids"])
            for item_id in accumulated_cart.get("cart_item_ids", []):
                if item_id not in existing_ids and item_id in CATALOG:
                    parsed["cart_item_ids"].append(item_id)
                    parsed["items"].append(CATALOG[item_id])
            parsed["subtotal"] = round(sum(CATALOG[i]["price"] for i in parsed["cart_item_ids"]), 2)

        uid = parsed["user_id"]
        item_ids = parsed["cart_item_ids"]
        subtotal = parsed["subtotal"]
        collected: dict[str, Any] = {}

        tasks = []
        tasks.append(("promotions", lambda: query_promotions(subtotal or None)))
        tasks.append(("bundles", lambda: optimize_bundles(item_ids)))
        if uid and not parsed["invalid_user_id"]:
            tasks.append(("loyalty", lambda: check_loyalty_tier(uid)))
            tasks.append(("coupons", lambda: apply_coupons(uid, subtotal)))
        elif subtotal > 0:
            tasks.append(("coupons", lambda: apply_coupons(None, subtotal)))

        with ThreadPoolExecutor(max_workers=4) as pool:
            fut = {pool.submit(fn): key for key, fn in tasks}
            for f in as_completed(fut):
                collected[fut[f]] = f.result()

        is_loyalty_query = any(w in user_message.lower() for w in ["loyalty", "tier", "level", "points", "status", "member", "rank", "guest", "benefits", "perks", "bronze", "silver", "gold", "platinum"])

        off_topic_keywords = [
            "poem", "poetry", "weather", "temperature", "forecast", "rain", "sunny",
            "code", "python", "javascript", "java", "rust", "cpp",
            "cooking", "recipe", "bake", "dinner", "lunch", "breakfast",
            "movie", "film", "song", "music", "album", "artist",
            "joke", "funny", "humor", "comedy",
            "math", "physics", "chemistry", "biology",
            "football", "soccer", "basketball", "tennis",
            "travel", "hotel", "flight", "vacation", "trip",
            "doctor", "hospital", "medicine",
            "how to", "tutorial", "guide",
            "hello", "hi", "hey", "how are you", "what is your name",
            "who made you", "who created you",
            "meaning of life", "philosophy", "religion",
            "age", "birthday", "date", "time",
            "news", "current events", "politics", "election",
            "vehicle", "driver license",
            "love", "relationship", "advice",
            "email", "phone", "address", "contact",
            "write", "essay", "story", "article",
            "translate", "language", "spanish", "french",
            "draw", "design", "photo", "picture",
            "homework", "assignment", "school", "college", "exam",
            "salary", "job", "career", "resume", "interview",
            "stock", "investment", "crypto", "bitcoin",
            "fact", "did you know", "trivia", "random",
        ]
        is_off_topic = not parsed["items"] and not is_loyalty_query and any(w in user_message.lower() for w in off_topic_keywords)

        suppress_cards = False
        msg_lower = user_message.lower()
        if re.search(r'\b(image|\.png|\.jpg|\.jpeg|\.gif|\.svg|\.webp)\b', msg_lower) or 'cannot read' in msg_lower:
            prompt = f"User: \"{user_message}\". They referenced an image file. This model only supports text. Say exactly: \"I can only process text. Please describe your cart or question in words.\" Do not add anything else."
            suppress_cards = True
        elif is_loyalty_query and not uid:
            prompt = f"User: \"{user_message}\". They want to know about loyalty but did not provide a user ID. Say exactly: \"Please provide your user ID (e.g., user_001, user_002) to check your loyalty status.\" Do not add anything else."
            suppress_cards = True
        elif parsed["invalid_user_id"]:
            prompt = f"User: \"{user_message}\". They provided a user ID that does not exist. Say exactly: \"Please provide a valid user ID (e.g., user_001, user_002, user_003, user_004).\" Do not add anything else."
            suppress_cards = True
        elif not parsed["items"] and not is_loyalty_query and any(w in msg_lower for w in ["deal", "promotion", "coupon", "offer", "sale", "discount"]) and any(w in msg_lower for w in ["available", "current", "list", "show", "tell me about"]):
            proms = collected.get("promotions", {}).get("promotions", [])
            bndls = collected.get("bundles", {}).get("bundles", [])
            def pfmt(p):
                if p["type"] == "free_shipping": return f"{p['name']} free shipping on orders over ${p['min_spend']:.0f}"
                if p["type"] == "flat_off": return f"{p['name']}: ${p['value']} off on orders over ${p['min_spend']:.0f}"
                return f"{p['name']}: {p['value']}% off on orders over ${p['min_spend']:.0f}"
            p_str = ", ".join(pfmt(p) for p in proms) if proms else "None active"
            c_lines = []
            for c in COUPONS_DB:
                tier = c.get("min_tier", "bronze")
                if c["type"] == "percent_off":
                    c_lines.append(f"{c['code']} {c['value']}% off min ${c['min_spend']:.0f} {tier}+")
                elif c["type"] == "flat_off":
                    c_lines.append(f"{c['code']} ${c['value']} off min ${c['min_spend']:.0f}")
                elif c["type"] == "free_shipping":
                    c_lines.append(f"{c['code']} free shipping min ${c['min_spend']:.0f}")
            c_str = ", ".join(c_lines)
            b_str = ", ".join(f"{b['name']} {b['discount']}% off ({', '.join(CATALOG[i]['name'] for i in b['items'])})" for b in bndls) if bndls else "None"
            prompt = f"User: \"{user_message}\". They want to know what deals are available. Say exactly: \"Here are the current deals.\" then list each promotion, coupon, and bundle below. Do NOT calculate anything. Do NOT ask for cart items.\n\nPromotions: {p_str}\nCoupons: {c_str}\nBundles: {b_str}"
        elif msg_lower.strip() in ("help", "help me", "what can you do", "what can you do for me"):
            prompt = f"User: \"{user_message}\". Say exactly: \"I can help you save money. Tell me your user ID and cart items, ask about your loyalty tier, or name some items and I will find deals for you. What would you like?\""
        elif is_off_topic:
            prompt = f"User: \"{user_message}\". Say exactly: \"I am a deal agent. My task is to help you find the best deals and checkout savings. I cannot help with this.\" Do not add anything else."
            suppress_cards = True
        else:
            result_data = build_prompt(parsed, collected, user_message)
            prompt = f"User: \"{user_message}\"\n\n{result_data['prompt']}\n\nYour response should start immediately with the answer. Do NOT repeat the user message or the prompt. Just state the best deal."

        if self.client:
            try:
                msgs = [{"role": "system", "content": SYSTEM_PROMPT}]
                if history:
                    for h in history[-6:]:
                        msgs.append(h)
                msgs.append({"role": "user", "content": prompt})
                resp = self.client.chat.completions.create(
                    model=self.model,
                    messages=msgs,
                    temperature=0.4,
                    max_tokens=500,
                )
                summary = self._clean_text(resp.choices[0].message.content.strip())
                return {"response": summary, "data": collected, "suppress_cards": suppress_cards, "cart_state": {"cart_item_ids": parsed["cart_item_ids"]}}
            except Exception as e:
                err = str(e).lower()
                if "image" in err or "cannot read" in err or "not support" in err or "unsupported" in err:
                    return {"response": "I can only process text. Please describe your cart or question in words.", "data": collected, "suppress_cards": True, "cart_state": {"cart_item_ids": parsed["cart_item_ids"]}}

        return {"response": self._clean_text(self._fallback_summary(parsed, collected)), "data": collected, "suppress_cards": suppress_cards, "cart_state": {"cart_item_ids": parsed["cart_item_ids"]}}

    @staticmethod
    def _clean_text(text: str) -> str:
        text = re.sub(r'\*{1,2}(.*?)\*{1,2}', r'\1', text)
        text = re.sub(r'__([^_]+)__', r'\1', text)
        text = re.sub(r'^[\s]*[-][\s]', '  ', text, flags=re.MULTILINE)
        text = re.sub(r'[→×•▪▸✦]', '', text)
        text = re.sub(r'#{1,6}\s*', '', text)
        text = re.sub(r'\\\(|\\\)', '', text)
        text = re.sub(r'\\\[|\\\]', '', text)
        return text.strip()

    def _fallback_summary(self, parsed: dict, data: dict) -> str:
        lines = []
        lines.append("Deal Optimization Report")
        lines.append("=" * 40)
        items = parsed.get("items", [])
        subtotal = parsed.get("subtotal", 0.0)
        if items:
            lines.append(f"\nCart: {len(items)} items, {format_currency(subtotal)}")
            for it in items:
                lines.append(f"  {it['name']}: {format_currency(it['price'])}")
        loyalty = data.get("loyalty")
        if loyalty and loyalty.get("user"):
            u = loyalty["user"]
            lines.append(f"User: {u['name']} ({u['tier'].title()})")
        coupons = data.get("coupons", {}).get("available_coupons", [])
        if coupons:
            best = coupons[0]
            if best["type"] == "percent_off":
                saved = round(subtotal * best["value"] / 100, 2)
            elif best["type"] == "flat_off":
                saved = min(float(best["value"]), subtotal)
            else:
                saved = 0
            final = round(subtotal - saved, 2)
            lines.append(f"Best: {best['code']} saves {format_currency(saved)}, final {format_currency(final)}")
        return "\n".join(lines)


WELCOME = """
--------------------------------------------
  Deal Agent - LLM-Driven (qwen2.5:1.5b)
  The model decides the best deal for you
--------------------------------------------
"""

SAMPLE_SCENARIOS = [
    "I'm user_001 (Alice), and I have Running Shoes, a Yoga Mat, and a Water Bottle in my cart. Find me the best deals.",
    "I'm user_002 (Bob, Platinum tier). My cart has a Gym Bag and Protein Powder. Get me the best checkout deal.",
    "I'm user_003 (Charlie). My cart has Resistance Bands, a Foam Roller, and a Water Bottle. Optimize my checkout.",
]


def main():
    import os as _os
    print(WELCOME)
    model = _os.environ.get("MODEL", "qwen2.5:1.5b")
    base_url = _os.environ.get("OLLAMA_URL", "http://localhost:11434/v1")
    agent = DealAgent(model=model, base_url=base_url)
    print(f"Model: {model} @ {base_url}")
    print(f"\nSample scenarios:")
    for i, s in enumerate(SAMPLE_SCENARIOS, 1):
        print(f"  [{i}] {s[:70]}...")
    print("\nOr type your own request.")

    while True:
        try:
            choice = input("\n> ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not choice:
            continue
        if choice.lower() in ("exit", "quit", "q"):
            break
        if choice in ("1", "2", "3"):
            prompt = SAMPLE_SCENARIOS[int(choice) - 1]
        else:
            prompt = choice

        print(f"\n{'-' * 60}")
        start = time.time()
        result = agent.run(prompt)
        elapsed = time.time() - start
        print(f"\n{result['response']}")
        print(f"\n{'-' * 60}")
        print(f"Completed in {elapsed:.1f}s")


if __name__ == "__main__":
    main()
