"""
Deal Agent Tools
Mock implementations — replace with real API calls in production.
"""

import json
from agents import function_tool
from .models import Promotion, LoyaltyAccount, BundleOffer, DiscountResult


# ── Mock data store ────────────────────────────────────────────────────────────

MOCK_PROMOTIONS = [
    Promotion(
        promo_id="P001",
        code="SAVE10",
        description="10% off on Electronics",
        discount_type="percentage",
        discount_value=10.0,
        min_order_value=500.0,
        applicable_categories=["electronics"],
        applicable_product_ids=[],
        expiry_date="2026-12-31",
        stackable=False,
    ),
    Promotion(
        promo_id="P002",
        code="FLAT200",
        description="Rs. 200 off on orders above Rs. 1000",
        discount_type="fixed",
        discount_value=200.0,
        min_order_value=1000.0,
        applicable_categories=["all"],
        applicable_product_ids=[],
        expiry_date="2026-06-30",
        stackable=True,
    ),
    Promotion(
        promo_id="P003",
        code="BUNDLE15",
        description="15% off when buying 3+ items",
        discount_type="bundle",
        discount_value=15.0,
        min_order_value=0.0,
        applicable_categories=["all"],
        applicable_product_ids=[],
        expiry_date="2026-12-31",
        stackable=True,
    ),
    Promotion(
        promo_id="P004",
        code="FASHION20",
        description="20% off on Fashion & Clothing",
        discount_type="percentage",
        discount_value=20.0,
        min_order_value=300.0,
        applicable_categories=["fashion", "clothing"],
        applicable_product_ids=[],
        expiry_date="2026-07-15",
        stackable=False,
    ),
]

MOCK_LOYALTY = {
    "U001": LoyaltyAccount(user_id="U001", points_balance=1500, points_value_per_unit=0.5, tier="silver", tier_multiplier=1.5),
    "U002": LoyaltyAccount(user_id="U002", points_balance=5000, points_value_per_unit=0.5, tier="gold", tier_multiplier=2.0),
    "U003": LoyaltyAccount(user_id="U003", points_balance=200, points_value_per_unit=0.5, tier="bronze", tier_multiplier=1.0),
}

MOCK_BUNDLES = [
    BundleOffer(
        bundle_id="B001",
        name="Phone + Earbuds Bundle",
        required_product_ids=["PROD_PHONE", "PROD_EARBUDS"],
        bundle_discount_percentage=18.0,
        description="Buy phone and earbuds together and save 18%",
    ),
    BundleOffer(
        bundle_id="B002",
        name="Laptop Essentials Pack",
        required_product_ids=["PROD_LAPTOP", "PROD_MOUSE", "PROD_BAG"],
        bundle_discount_percentage=22.0,
        description="Laptop + Mouse + Bag combo — save 22%",
    ),
]

APPLIED_DISCOUNTS: dict = {}


# ── Tool definitions ───────────────────────────────────────────────────────────

@function_tool
def get_active_promotions(category: str, cart_total: float) -> str:
    """
    Fetch all active promotions applicable to the given category and cart total.

    Args:
        category: Product category (e.g. 'electronics', 'fashion', 'all')
        cart_total: Current cart total in PKR

    Returns:
        JSON list of applicable promotions with codes and discount details.
    """
    applicable = []
    for promo in MOCK_PROMOTIONS:
        category_match = (
            "all" in promo.applicable_categories
            or category.lower() in promo.applicable_categories
        )
        meets_minimum = cart_total >= promo.min_order_value
        if category_match and meets_minimum:
            applicable.append(promo.model_dump())

    if not applicable:
        return json.dumps({"promotions": [], "message": "No active promotions found for this cart."})

    return json.dumps({"promotions": applicable, "count": len(applicable)})


@function_tool
def get_loyalty_points(user_id: str) -> str:
    """
    Retrieve the user's loyalty points balance and tier information.

    Args:
        user_id: Unique user identifier

    Returns:
        JSON with points balance, monetary value, and tier details.
    """
    account = MOCK_LOYALTY.get(user_id)
    if not account:
        return json.dumps({
            "user_id": user_id,
            "points_balance": 0,
            "monetary_value": 0.0,
            "tier": "bronze",
            "message": "No loyalty account found. Starting with 0 points.",
        })

    monetary_value = account.points_balance * account.points_value_per_unit
    return json.dumps({
        "user_id": account.user_id,
        "points_balance": account.points_balance,
        "monetary_value_pkr": monetary_value,
        "tier": account.tier,
        "tier_multiplier": account.tier_multiplier,
        "message": f"You have {account.points_balance} points worth Rs. {monetary_value:.0f}",
    })


@function_tool
def get_bundle_offers(product_ids: list[str]) -> str:
    """
    Check if any products in the cart qualify for bundle deals.

    Args:
        product_ids: List of product IDs in the cart

    Returns:
        JSON with applicable bundle offers and savings.
    """
    matched_bundles = []
    product_set = set(product_ids)

    for bundle in MOCK_BUNDLES:
        required = set(bundle.required_product_ids)
        if required.issubset(product_set):
            matched_bundles.append(bundle.model_dump())

    if not matched_bundles:
        return json.dumps({"bundles": [], "message": "No bundle offers available for selected products."})

    return json.dumps({"bundles": matched_bundles, "count": len(matched_bundles)})


@function_tool
def apply_discount(
    cart_id: str,
    user_id: str,
    original_price: float,
    promo_codes: list[str],
    loyalty_points_to_use: int,
) -> str:
    """
    Apply selected promotions and loyalty points to the cart and calculate final price.

    Args:
        cart_id: Shopping cart identifier
        user_id: User identifier
        original_price: Cart total before discounts (PKR)
        promo_codes: List of promo codes to apply
        loyalty_points_to_use: Number of loyalty points to redeem

    Returns:
        JSON with itemized discount breakdown and final price.
    """
    price = original_price
    applied = []
    total_discount = 0.0

    # Apply promo codes
    for code in promo_codes:
        promo = next((p for p in MOCK_PROMOTIONS if p.code == code), None)
        if promo and price >= promo.min_order_value:
            if promo.discount_type == "percentage":
                discount_amt = price * (promo.discount_value / 100)
                price -= discount_amt
                total_discount += discount_amt
                applied.append(f"{code} (-{promo.discount_value}% = Rs. {discount_amt:.0f})")
            elif promo.discount_type == "fixed":
                price -= promo.discount_value
                total_discount += promo.discount_value
                applied.append(f"{code} (-Rs. {promo.discount_value:.0f})")
            elif promo.discount_type == "bundle":
                discount_amt = price * (promo.discount_value / 100)
                price -= discount_amt
                total_discount += discount_amt
                applied.append(f"{code} (bundle -{promo.discount_value}% = Rs. {discount_amt:.0f})")

    # Apply loyalty points
    loyalty_discount = 0.0
    if loyalty_points_to_use > 0:
        account = MOCK_LOYALTY.get(user_id)
        if account and account.points_balance >= loyalty_points_to_use:
            loyalty_discount = loyalty_points_to_use * account.points_value_per_unit
            price -= loyalty_discount
            total_discount += loyalty_discount
            applied.append(f"{loyalty_points_to_use} loyalty pts (-Rs. {loyalty_discount:.0f})")
            # Deduct points from mock store
            MOCK_LOYALTY[user_id] = LoyaltyAccount(
                user_id=user_id,
                points_balance=account.points_balance - loyalty_points_to_use,
                points_value_per_unit=account.points_value_per_unit,
                tier=account.tier,
                tier_multiplier=account.tier_multiplier,
            )

    price = max(price, 0.0)
    savings_pct = (total_discount / original_price) * 100 if original_price > 0 else 0

    result = DiscountResult(
        applied_promotions=applied,
        loyalty_points_used=loyalty_points_to_use,
        total_discount_amount=total_discount,
        final_price=round(price, 2),
        original_price=original_price,
        savings_percentage=round(savings_pct, 1),
        message=f"You saved Rs. {total_discount:.0f} ({savings_pct:.1f}%) on your order!",
    )

    # Store result
    APPLIED_DISCOUNTS[cart_id] = result.model_dump()

    return json.dumps(result.model_dump())
