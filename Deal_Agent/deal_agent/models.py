from pydantic import BaseModel
from typing import Optional


class Promotion(BaseModel):
    promo_id: str
    code: str
    description: str
    discount_type: str        # "percentage" | "fixed" | "bundle"
    discount_value: float
    min_order_value: float
    applicable_categories: list[str]
    applicable_product_ids: list[str]
    expiry_date: str
    stackable: bool


class LoyaltyAccount(BaseModel):
    user_id: str
    points_balance: int
    points_value_per_unit: float  # e.g. 1 point = $0.01
    tier: str                     # "bronze" | "silver" | "gold" | "platinum"
    tier_multiplier: float        # bonus multiplier on earning


class BundleOffer(BaseModel):
    bundle_id: str
    name: str
    required_product_ids: list[str]
    bundle_discount_percentage: float
    description: str


class DiscountResult(BaseModel):
    applied_promotions: list[str]
    loyalty_points_used: int
    total_discount_amount: float
    final_price: float
    original_price: float
    savings_percentage: float
    message: str
