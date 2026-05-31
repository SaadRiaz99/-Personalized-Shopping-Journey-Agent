"""
Post-Purchase Loyalty & Retention Agent - MOCK MODE (No API Key Needed)
Bilkul same agent, bina internet ke.
Run: python post_purchase_agent_mock.py
"""

import json
from datetime import datetime

with open("customers.json") as f:
    DATA = json.load(f)

CUSTOMERS = DATA["customers"]
ORDERS = DATA["orders"]
TIER_RULES = DATA["tier_rules"]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _find_customer(customer_id):
    return next((c for c in CUSTOMERS if c["customer_id"] == customer_id), None)


def _find_order(order_id):
    return next((o for o in ORDERS if o["order_id"] == order_id), None)


def _get_tier_benefits(tier):
    return TIER_RULES.get(tier, TIER_RULES["bronze"])["benefits"]


def _get_next_tier_info(tier, points):
    tiers = ["bronze", "silver", "gold", "platinum"]
    idx = tiers.index(tier)
    if idx >= len(tiers) - 1:
        return None, 0
    next_tier = tiers[idx + 1]
    return next_tier, max(0, TIER_RULES[next_tier]["min_points"] - points)


def _detect_milestones(customer):
    existing = set(customer.get("milestones", []))
    new_ms = []
    orders = [o for o in ORDERS if o["customer_id"] == customer["customer_id"]]
    delivered = [o for o in orders if o["status"] == "delivered"]
    total = len(delivered)

    if total >= 1 and "first_purchase" not in existing:
        new_ms.append("first_purchase")
    if total >= 2 and "second_purchase" not in existing:
        new_ms.append("second_purchase")
    if total >= 5 and "5_orders" not in existing:
        new_ms.append("5_orders")
    if total >= 10 and "10_orders" not in existing:
        new_ms.append("10_orders")
    if customer["tier"] in ("gold", "platinum") and "vip_eligible" not in existing:
        new_ms.append("vip_eligible")
    if customer["tier"] == "platinum" and "platinum" not in existing:
        new_ms.append("platinum")
    return new_ms


def _sentiment_from_text(text):
    if not text:
        return "neutral"
    t = text.lower()
    pos = sum(1 for w in ["amazing", "great", "love", "perfect", "beautiful", "happy",
                           "excellent", "wonderful", "impressed", "comfortable", "fast",
                           "good", "nice", "satisfied"] if w in t)
    neg = sum(1 for w in ["disappointed", "stopped working", "broken", "poor", "worst",
                          "terrible", "defective", "damaged", "issue", "waste",
                          "bad", "different", "wrong", "problem"] if w in t)
    mixed_signals = any(s in t for s in ["but", "however", "slightly", "overall", "although"])
    if mixed_signals and pos > 0 and neg > 0:
        return "mixed"
    if pos > neg:
        return "positive"
    if neg > pos:
        return "negative"
    return "neutral"


# ---------------------------------------------------------------------------
# Command handlers
# ---------------------------------------------------------------------------

def cmd_profile(customer_id):
    c = _find_customer(customer_id)
    if not c:
        return "\n  Unknown customer. Please check the ID."

    new_ms = _detect_milestones(c)
    next_tier, pts_needed = _get_next_tier_info(c["tier"], c["points"])
    benefits = ", ".join(_get_tier_benefits(c["tier"]))

    lines = [
        f"\n  {'=' * 56}",
        f"  CUSTOMER PROFILE — {c['name']}",
        f"  {'=' * 56}",
        f"  Customer ID : {c['customer_id']}",
        f"  Tier        : {c['tier'].upper()}",
        f"  Points      : {c['points']} (worth Rs. {c['points'] * TIER_RULES[c['tier']]['value_per_point']:.0f})",
        f"  Orders      : {c['total_orders']}",
        f"  Total Spent : Rs. {c['total_spent']:,.0f}",
        f"  Benefits    : {benefits}",
    ]
    if next_tier:
        lines.append(f"  Next Tier   : {next_tier.upper()} ({pts_needed} more points needed)")
    if new_ms:
        lines.append(f"  New Milestones: {', '.join(new_ms)}")

    # milestone message
    if new_ms:
        if "platinum" in new_ms:
            lines.append(f"\n  >>> Welcome to Platinum, {c['name']}! You now have a dedicated manager.")
        elif "vip_eligible" in new_ms:
            lines.append(f"\n  >>> {c['name']}, you're VIP-eligible! Keep shopping to unlock Platinum.")
        elif "first_purchase" in new_ms:
            lines.append(f"\n  >>> Welcome to the family, {c['name']}! Your first order is on its way.")
        elif "second_purchase" in new_ms:
            lines.append(f"\n  >>> Thanks for coming back, {c['name']}! Loyalty starts here.")
        elif "5_orders" in new_ms:
            lines.append(f"\n  >>> 5 orders strong, {c['name']}! Keep going for Silver tier.")
        elif "10_orders" in new_ms:
            lines.append(f"\n  >>> 10 orders, {c['name']}! VIP perks await.")

    return "\n".join(lines)


def cmd_track(order_id):
    o = _find_order(order_id)
    if not o:
        return f"\n  Order {order_id} not found."

    c = _find_customer(o["customer_id"])
    name = c["name"] if c else "Customer"

    status_icons = {
        "confirmed": "ORDER CONFIRMED",
        "shipped": "SHIPPED",
        "in_transit": "IN TRANSIT",
        "delivered": "DELIVERED",
        "delayed": "! DELAYED",
    }

    lines = [
        f"\n  {'=' * 56}",
        f"  ORDER STATUS — {o['order_id']}",
        f"  {'=' * 56}",
        f"  Customer    : {name} ({o['customer_id']})",
        f"  Status      : {status_icons.get(o['status'], o['status'].upper())}",
        f"  Date Ordered: {o['order_date']}",
        f"  Est. Delivery: {o['estimated_delivery']}",
        f"  Carrier     : {o['carrier']}",
        f"  Tracking    : {o['tracking']}",
        f"  Total       : Rs. {o['total']:,.0f}",
        f"  Address     : {o['delivery_address']}",
    ]

    if o["status"] == "delayed" and o.get("delay_reason"):
        lines.append(f"  Delay Reason: {o['delay_reason']}")
        lines.append(f"  Resolution By: {o.get('delay_expected_resolution', 'TBD')}")

    lines.append(f"\n  Items:")
    for item in o["items"]:
        lines.append(f"    x{item['qty']} {item['product']} — Rs. {item['price']:,.0f}")

    # update message
    if o["status"] == "delayed":
        lines.append(f"\n  >>> Hi {name}, we apologise — your order is delayed due to "
                     f"{o.get('delay_reason', 'operational issues')}. "
                     f"We expect to resolve by {o.get('delay_expected_resolution', 'soon')}.")
    elif o["status"] == "confirmed":
        lines.append(f"\n  >>> Hi {name}, order confirmed! We're preparing your items.")
    elif o["status"] == "shipped":
        lines.append(f"\n  >>> Great news {name}, your order has shipped via {o['carrier']}!")
    elif o["status"] == "in_transit":
        lines.append(f"\n  >>> Your order is on the way, {name}! Tracking: {o['tracking']}")
    elif o["status"] == "delivered":
        lines.append(f"\n  >>> Delivered! We'd love your feedback, {name}.")

    if o.get("feedback"):
        lines.append(f"\n  Feedback: \"{o['feedback']}\"")
        lines.append(f"  Sentiment: {o.get('sentiment', 'N/A').upper()}")

    return "\n".join(lines)


def cmd_feedback(order_id, text, rating=None):
    o = _find_order(order_id)
    if not o:
        return f"\n  Order {order_id} not found."
    o["feedback"] = text
    sentiment = _sentiment_from_text(text)
    o["sentiment"] = sentiment

    rating_note = f"Rating: {rating}/5. " if rating else ""
    sent_labels = {"positive": "[POS]", "negative": "[NEG]", "mixed": "[MIX]", "neutral": "[NEU]"}
    icon = sent_labels.get(sentiment, "")

    return (
        f"\n  Feedback recorded for {order_id}. {rating_note}"
        f"Sentiment: {sentiment.upper()} {icon}"
    )


def cmd_sentiment(text):
    sentiment = _sentiment_from_text(text)
    sent_icons = {"positive": "[POS]", "negative": "[NEG]", "mixed": "[MIX]", "neutral": "[NEU]"}
    tones = {
        "positive": "warm and grateful",
        "negative": "empathetic and urgent",
        "mixed": "appreciative and problem-solving",
        "neutral": "helpful and neutral",
    }
    return (
        f"\n  Sentiment Analysis:"
        f"\n    Sentiment : {sentiment.upper()} {sent_icons.get(sentiment, '')}"
        f"\n    Tone      : {tones.get(sentiment, 'neutral')}"
    )


def cmd_retention(customer_id):
    c = _find_customer(customer_id)
    if not c:
        return "\n  Unknown customer."

    orders = [o for o in ORDERS if o["customer_id"] == customer_id]
    active = [o for o in orders if o["status"] in ("confirmed", "shipped", "in_transit", "delayed")]
    delivered = [o for o in orders if o["status"] == "delivered"]

    lines = [f"\n  {'=' * 56}", f"  RETENTION PLAN — {c['name']}", f"  {'=' * 56}"]

    # Check delays
    delayed = [o for o in active if o["status"] == "delayed"]
    if delayed:
        o = delayed[0]
        lines.append(f"  URGENT: Delay on {o['order_id']} — send apology + Rs. 200 off coupon")
        lines.append(f"  >>> We apologise for the delay! Here's Rs. 200 off your next order.")
        return "\n".join(lines)

    # Check negative feedback
    for o in delivered:
        if o.get("sentiment") == "negative":
            lines.append(f"  URGENT: Negative feedback on {o['order_id']} — send 15% discount code")
            lines.append(f"  >>> We're sorry about your experience. Here's 15% off your next order (WEARE15).")
            return "\n".join(lines)

    # Check mixed feedback
    for o in delivered:
        if o.get("sentiment") == "mixed":
            lines.append(f"  ACTION: Mixed feedback on {o['order_id']} — send 200 bonus points")
            lines.append(f"  >>> Thanks for your honest feedback! Here's 200 bonus points.")
            return "\n".join(lines)

    # Second purchase milestone
    new_ms = _detect_milestones(c)
    if "second_purchase" in new_ms:
        lines.append(f"  ACTION: 2nd purchase milestone — 500 bonus points!")
        lines.append(f"  >>> Congratulations on your 2nd purchase! 500 bonus points added.")
        return "\n".join(lines)

    # VIP eligible
    if "vip_eligible" in c.get("milestones", []):
        lines.append(f"  ACTION: VIP-eligible — nudge toward Platinum")
        lines.append(f"  >>> You're VIP-eligible! Rs. 5000 more to unlock Platinum with a dedicated manager.")
        return "\n".join(lines)

    # High-value recent order
    if orders and max(o["total"] for o in orders) > 10000:
        lines.append(f"  ACTION: High-value customer — recommend accessories")
        lines.append(f"  >>> Check out accessories that pair with your recent purchase!")
        return "\n".join(lines)

    # New buyer
    if c["total_orders"] <= 2:
        lines.append(f"  ACTION: Welcome offer — 10% off next order (WELCOME10)")
        lines.append(f"  >>> Welcome! Use WELCOME10 for 10% off your next order.")
        return "\n".join(lines)

    lines.append(f"  ACTION: Regular engagement — maintain relationship")
    lines.append(f"  >>> Thank you for being a valued {c['tier'].upper()} member!")
    return "\n".join(lines)


def cmd_help():
    return (
        "\n  Available commands:"
        "\n    profile <C_ID>        — View customer loyalty profile"
        "\n    track <ORDER_ID>      — Track an order's status"
        "\n    feedback <ORDER_ID> \"<text>\" [rating] — Record feedback (sentiment auto-detected)"
        "\n    sentiment \"<text>\"     — Analyze sentiment of any text"
        "\n    retain <C_ID>         — Generate personalized retention action"
        "\n    help                  — Show this help"
        "\n    exit                  — Quit"
        "\n"
        "\n  Sample IDs: C001 (new buyer), C002 (returning), C003 (gold, mixed feedback),"
        "\n              C004 (platinum, negative feedback), C006 (delayed order)"
    )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    print("=" * 60)
    print("  POST-PURCHASE LOYALTY & RETENTION AGENT")
    print("  MOCK MODE (No API Key) — Built by Hashir | SMIT Batch")
    print("=" * 60)
    print(cmd_help())
    print("=" * 60)

    while True:
        try:
            user_input = input("\nYou: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break

        if not user_input:
            continue
        if user_input.lower() in ("exit", "quit"):
            print("\nRetention Agent: Goodbye! We'll keep taking care of your experience.")
            break

        parts = user_input.split(maxsplit=1)
        cmd = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ""

        if cmd == "profile":
            print(cmd_profile(args.strip() or "C001"))
        elif cmd == "track":
            print(cmd_track(args.strip() or "ORD001"))
        elif cmd == "feedback":
            # feedback ORD001 "text" [rating]
            rest = args.strip()
            if not rest:
                print("\n  Usage: feedback ORD001 \"your feedback text\" [rating]")
                continue
            inner = rest.split(None, 1)
            oid = inner[0]
            rest2 = inner[1] if len(inner) > 1 else ""
            import shlex
            try:
                parsed = shlex.split(rest2)
            except ValueError:
                parsed = rest2.split(None, 1)
            text = parsed[0] if parsed else ""
            rating = int(parsed[1]) if len(parsed) > 1 and parsed[1].isdigit() else None
            print(cmd_feedback(oid, text, rating))
        elif cmd == "sentiment":
            print(cmd_sentiment(args.strip(' "')))
        elif cmd == "retain":
            print(cmd_retention(args.strip() or "C001"))
        elif cmd == "help":
            print(cmd_help())
        else:
            print("\n  Unknown command. Type 'help' for available commands.")


if __name__ == "__main__":
    main()
