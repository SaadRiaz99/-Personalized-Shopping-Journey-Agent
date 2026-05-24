import uuid
from datetime import datetime
from typing import Optional

from app.models import (
    AppliedDiscount,
    CartSession,
    DealSessionRequest,
    DiscountStack,
    DiscountType,
    LoyaltyTier,
    Promotion,
)


def _seed_promotions() -> list[Promotion]:
    return [
        Promotion(
            id="promo_bronze_5",
            name="Bronze Welcome",
            description="5% off your entire order",
            type=DiscountType.percentage,
            value=5.0,
            stackable=True,
            min_loyalty_tier=LoyaltyTier.bronze,
        ),
        Promotion(
            id="promo_silver_10",
            name="Silver Saver",
            description="10% off your entire order",
            type=DiscountType.percentage,
            value=10.0,
            stackable=True,
            min_loyalty_tier=LoyaltyTier.silver,
        ),
        Promotion(
            id="promo_gold_15",
            name="Gold Member Discount",
            description="15% off your entire order",
            type=DiscountType.percentage,
            value=15.0,
            stackable=True,
            min_loyalty_tier=LoyaltyTier.gold,
        ),
        Promotion(
            id="promo_platinum_20",
            name="Platinum Elite",
            description="20% off your entire order",
            type=DiscountType.percentage,
            value=20.0,
            stackable=True,
            min_loyalty_tier=LoyaltyTier.platinum,
        ),
        Promotion(
            id="promo_new_user",
            name="New User Special",
            description="$10 off your first purchase",
            type=DiscountType.fixed,
            value=10.0,
            stackable=True,
            min_purchase=50.0,
        ),
        Promotion(
            id="promo_flash_friday",
            name="Flash Friday",
            description="15% off storewide this weekend only",
            type=DiscountType.percentage,
            value=15.0,
            stackable=True,
            min_purchase=75.0,
            max_discount=50.0,
        ),
        Promotion(
            id="promo_electronics_10",
            name="Tech Markdown",
            description="10% off all Electronics",
            type=DiscountType.category_markdown,
            value=10.0,
            stackable=True,
            applicable_categories=["Electronics"],
            max_discount=30.0,
        ),
        Promotion(
            id="promo_fashion_15",
            name="Fashion Flash Sale",
            description="15% off Fashion items",
            type=DiscountType.category_markdown,
            value=15.0,
            stackable=True,
            applicable_categories=["Fashion"],
            max_discount=40.0,
        ),
        Promotion(
            id="promo_sports_12",
            name="Fitness Frenzy",
            description="12% off Sports & Fitness gear",
            type=DiscountType.category_markdown,
            value=12.0,
            stackable=True,
            applicable_categories=["Sports"],
            max_discount=25.0,
        ),
        Promotion(
            id="promo_home_8",
            name="Home Comforts",
            description="8% off Home items",
            type=DiscountType.category_markdown,
            value=8.0,
            stackable=True,
            applicable_categories=["Home"],
            max_discount=20.0,
        ),
        Promotion(
            id="promo_bogo_welcome",
            name="Buy One Get One Free",
            description="Cheapest item free when you buy 2+ items",
            type=DiscountType.bogo,
            value=100.0,
            stackable=False,
            min_purchase=25.0,
        ),
        Promotion(
            id="promo_big_spender",
            name="Big Spender Bonus",
            description="$25 off orders over $200",
            type=DiscountType.fixed,
            value=25.0,
            stackable=True,
            min_purchase=200.0,
        ),
        Promotion(
            id="promo_freedom",
            name="Privacy-Friendly Discount",
            description="5% off for everyone — no personalization needed",
            type=DiscountType.percentage,
            value=5.0,
            stackable=True,
            requires_opt_in=False,
        ),
    ]


class DealAgent:
    def __init__(self):
        self.promotions: list[Promotion] = _seed_promotions()
        self.applied_stacks: dict[str, DiscountStack] = {}

    def get_active_promotions(self) -> list[Promotion]:
        return [p for p in self.promotions if p.active]

    def add_promotion(self, promo: Promotion) -> Promotion:
        self.promotions.append(promo)
        return promo

    def deactivate_promotion(self, promo_id: str) -> bool:
        for p in self.promotions:
            if p.id == promo_id and p.active:
                p.active = False
                return True
        return False

    def optimize_stack(self, cart: CartSession) -> Optional[DiscountStack]:
        applicable = [p for p in self.promotions if p.is_applicable(cart)]

        loyalty_promo = None
        for p in applicable:
            if p.type == DiscountType.percentage and not p.applicable_categories:
                if cart.loyalty_tier.value in p.name.lower() or p.id.startswith("promo_"):
                    if not loyalty_promo or p.value > loyalty_promo.value:
                        loyalty_promo = p

        stackable_percentage = [p for p in applicable if p.stackable and p.type == DiscountType.percentage]
        stackable_fixed = [p for p in applicable if p.stackable and p.type == DiscountType.fixed]
        stackable_category = [p for p in applicable if p.stackable and p.type == DiscountType.category_markdown]
        non_stackable = [p for p in applicable if not p.stackable]

        bogo = None
        for p in non_stackable:
            if p.type == DiscountType.bogo:
                bogo = p
                break

        applied: list[AppliedDiscount] = []
        running_total = cart.subtotal

        if bogo and bogo.is_applicable(cart):
            bogo_result = bogo.apply_to(cart)
            if bogo_result["discount"] > 0:
                running_total = bogo_result["new_total"]
                applied.append(AppliedDiscount(
                    promotion_id=bogo.id,
                    promotion_name=bogo.name,
                    discount_type=bogo.type,
                    discount_amount=bogo_result["discount"],
                    description=bogo.description,
                ))

        best_percentage = None
        for p in stackable_percentage:
            result = p.apply_to(cart)
            if not best_percentage or result["discount"] > best_percentage["discount"]:
                best_percentage = {"promo": p, **result}

        if best_percentage:
            running_total = round(running_total - best_percentage["discount"], 2)
            applied.append(AppliedDiscount(
                promotion_id=best_percentage["promo"].id,
                promotion_name=best_percentage["promo"].name,
                discount_type=best_percentage["promo"].type,
                discount_amount=best_percentage["discount"],
                description=best_percentage["promo"].description,
            ))

        for p in stackable_category:
            result = p.apply_to(cart)
            if result["discount"] > 0:
                running_total = round(running_total - result["discount"], 2)
                applied.append(AppliedDiscount(
                    promotion_id=p.id,
                    promotion_name=p.name,
                    discount_type=p.type,
                    discount_amount=result["discount"],
                    description=p.description,
                ))

        for p in stackable_fixed:
            result = p.apply_to(cart)
            if result["discount"] > 0:
                running_total = round(running_total - result["discount"], 2)
                applied.append(AppliedDiscount(
                    promotion_id=p.id,
                    promotion_name=p.name,
                    discount_type=p.type,
                    discount_amount=result["discount"],
                    description=p.description,
                ))

        running_total = round(max(running_total, 0), 2)

        if cart.budget and running_total > cart.budget * 1.2:
            running_total = cart.subtotal
            applied = []

        total_savings = round(cart.subtotal - running_total, 2)

        break_lines = [f">> Cart Subtotal: ${cart.subtotal:.2f}"]
        for d in applied:
            sign = "+" if d.discount_amount > 0 else ""
            break_lines.append(f"  - {d.promotion_name}: -${d.discount_amount:.2f}")
        break_lines.append(f"  {'=' * 20}")
        break_lines.append(f"  Final Total: ${running_total:.2f}")
        break_lines.append(f"  You Save: ${total_savings:.2f}")
        savings_breakdown = "\n".join(break_lines)

        stack = DiscountStack(
            id=str(uuid.uuid4())[:8],
            user_id=cart.user_id,
            original_total=cart.subtotal,
            final_total=running_total,
            total_savings=total_savings,
            applied_discounts=applied,
            savings_breakdown=savings_breakdown,
        )

        self.applied_stacks[stack.id] = stack
        return stack

    def apply_stack(self, stack_id: str) -> Optional[DiscountStack]:
        stack = self.applied_stacks.get(stack_id)
        if stack:
            return stack
        return None

    def get_stack(self, stack_id: str) -> Optional[DiscountStack]:
        return self.applied_stacks.get(stack_id)

    def list_stacks(self) -> list[DiscountStack]:
        return list(self.applied_stacks.values())

    def process_cart(self, request: DealSessionRequest) -> dict:
        cart = CartSession(
            user_id=request.user_id,
            items=request.items,
            loyalty_tier=request.loyalty_tier,
            budget=request.budget,
            opted_out=request.opted_out,
        )

        stack = self.optimize_stack(cart)
        if not stack:
            return {
                "user_id": cart.user_id,
                "message": "No applicable promotions found for your cart.",
                "subtotal": cart.subtotal,
                "final_total": cart.subtotal,
                "total_savings": 0.0,
                "applied_discounts": [],
                "savings_breakdown": f"No discounts available. Subtotal: ${cart.subtotal:.2f}",
            }

        return {
            "user_id": cart.user_id,
            "message": f"I've analyzed your cart and found the best deals!",
            "subtotal": cart.subtotal,
            "final_total": stack.final_total,
            "total_savings": stack.total_savings,
            "applied_discounts": [d.model_dump() for d in stack.applied_discounts],
            "savings_breakdown": stack.savings_breakdown,
        }


deal_agent = DealAgent()
