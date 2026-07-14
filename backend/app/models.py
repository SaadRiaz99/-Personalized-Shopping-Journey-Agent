from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum


class PrivacyLevel(str, Enum):
    strict = "strict"
    balanced = "balanced"
    open = "open"


class PrivacyRegion(str, Enum):
    gdpr = "gdpr"
    ccpa = "ccpa"
    none = "none"


class PrivacyConsent(BaseModel):
    marketing: bool = False
    third_party_sharing: bool = False
    biometric_data: bool = False
    profiling: bool = False
    data_retention: bool = True


class UserPrivacyProfile(BaseModel):
    privacy_level: PrivacyLevel = PrivacyLevel.strict
    consents: PrivacyConsent = Field(default_factory=PrivacyConsent)
    region: PrivacyRegion = PrivacyRegion.none
    data_retention_days: int = 90
    opted_out_of_sale: bool = False


class GuardrailAction(str, Enum):
    allowed = "allowed"
    blocked = "blocked"
    sanitized = "sanitized"
    flagged = "flagged"


class GuardrailResult(BaseModel):
    action: GuardrailAction
    sanitized_text: Optional[str] = None
    redacted_fields: list[str] = []
    violations: list[str] = []
    explanation: str = ""


class AgentStatus(str, Enum):
    idle = "idle"
    running = "running"
    completed = "completed"
    error = "error"


class TaskStatus(str, Enum):
    pending = "pending"
    running = "running"
    completed = "completed"
    failed = "failed"


class Agent(BaseModel):
    id: str
    name: str
    status: AgentStatus = AgentStatus.idle
    task: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class Product(BaseModel):
    id: str
    name: str
    description: str
    price: float
    category: str
    image_url: Optional[str] = None
    rating: float = 0.0
    tags: list[str] = []
    sku: Optional[str] = None


class UserPreferences(BaseModel):
    categories: list[str] = []
    price_min: float = 0.0
    price_max: float = 10000.0
    brands: list[str] = []
    budget: float = 1000.0


class Task(BaseModel):
    id: str
    agent_id: str
    type: str
    status: TaskStatus = TaskStatus.pending
    result: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class QueryIntent(BaseModel):
    category: Optional[str] = None
    budget: Optional[float] = None
    budget_currency: Optional[str] = "USD"
    occasion: Optional[str] = None
    style_preferences: list[str] = []
    urgency: Optional[str] = None
    raw_query: str = ""


class DiscountStatus(str, Enum):
    pending = "pending"
    approved = "approved"
    applied = "applied"
    declined = "declined"


class Discount(BaseModel):
    id: str
    agent_id: str
    product_id: str
    sku: str
    store_price: float
    competitor_store: str
    competitor_price: float
    discount_amount: float
    new_price: float
    status: DiscountStatus = DiscountStatus.pending
    created_at: datetime = Field(default_factory=datetime.now)


class PriceMatchRequest(BaseModel):
    product_id: str
    sku: str
    current_price: float


class AgentCreate(BaseModel):
    name: str
    task: Optional[str] = None


class TaskCreate(BaseModel):
    agent_id: str
    type: str


class LoyaltyTier(str, Enum):
    bronze = "bronze"
    silver = "silver"
    gold = "gold"
    platinum = "platinum"


class CartItem(BaseModel):
    product_id: str
    sku: str
    name: str
    price: float
    quantity: int = 1
    category: str = ""


class CartSession(BaseModel):
    user_id: str
    items: list[CartItem] = []
    loyalty_tier: LoyaltyTier = LoyaltyTier.bronze
    budget: Optional[float] = None
    opted_out: bool = False

    @property
    def subtotal(self) -> float:
        return round(sum(i.price * i.quantity for i in self.items), 2)


class SafetyCheckResult(BaseModel):
    allowed: bool = True
    blocked_category: Optional[str] = None
    blocked_reason: str = ""
    suggested_safe_query: Optional[str] = None


class DiscountType(str, Enum):
    percentage = "percentage"
    fixed = "fixed"
    bogo = "bogo"
    category_markdown = "category_markdown"


class Promotion(BaseModel):
    id: str
    name: str
    description: str
    type: DiscountType
    value: float
    stackable: bool = False
    min_purchase: Optional[float] = None
    max_discount: Optional[float] = None
    applicable_categories: list[str] = []
    min_loyalty_tier: LoyaltyTier = LoyaltyTier.bronze
    requires_opt_in: bool = False
    active: bool = True

    def is_applicable(self, cart: CartSession) -> bool:
        if not self.active:
            return False
        if self.requires_opt_in and cart.opted_out:
            return False
        tier_order = [LoyaltyTier.bronze, LoyaltyTier.silver, LoyaltyTier.gold, LoyaltyTier.platinum]
        if tier_order.index(cart.loyalty_tier) < tier_order.index(self.min_loyalty_tier):
            return False
        if self.min_purchase and cart.subtotal < self.min_purchase:
            return False
        if self.applicable_categories:
            cart_cats = {i.category for i in cart.items}
            if not cart_cats.intersection(self.applicable_categories):
                return False
        return True

    def apply_to(self, cart: CartSession) -> dict:
        if self.type == DiscountType.fixed:
            discount = self.value
            if self.max_discount:
                discount = min(discount, self.max_discount)
            return {"discount": round(discount, 2), "new_total": round(max(cart.subtotal - discount, 0), 2)}

        if self.type == DiscountType.percentage:
            discount = round(cart.subtotal * self.value / 100, 2)
            if self.max_discount:
                discount = min(discount, self.max_discount)
            return {"discount": round(discount, 2), "new_total": round(max(cart.subtotal - discount, 0), 2)}

        if self.type == DiscountType.category_markdown:
            affected_total = sum(i.price * i.quantity for i in cart.items if i.category in self.applicable_categories)
            discount = round(affected_total * self.value / 100, 2)
            if self.max_discount:
                discount = min(discount, self.max_discount)
            return {"discount": round(discount, 2), "new_total": round(max(cart.subtotal - discount, 0), 2)}

        if self.type == DiscountType.bogo:
            sorted_items = sorted(cart.items, key=lambda i: i.price, reverse=True)
            if len(sorted_items) >= 2:
                discount = round(sorted_items[-1].price, 2)
                return {"discount": discount, "new_total": round(max(cart.subtotal - discount, 0), 2)}
            return {"discount": 0.0, "new_total": cart.subtotal}

        return {"discount": 0.0, "new_total": cart.subtotal}


class AppliedDiscount(BaseModel):
    promotion_id: str
    promotion_name: str
    discount_type: DiscountType
    discount_amount: float
    description: str


class DiscountStack(BaseModel):
    id: str
    user_id: str
    original_total: float
    final_total: float
    total_savings: float
    applied_discounts: list[AppliedDiscount] = []
    savings_breakdown: str = ""
    created_at: datetime = Field(default_factory=datetime.now)


class DealSessionRequest(BaseModel):
    user_id: str
    items: list[CartItem]
    loyalty_tier: LoyaltyTier = LoyaltyTier.bronze
    budget: Optional[float] = None
    opted_out: bool = False


# ── Gift Finder Models ──────────────────────────────────────

class GiftRecipient(BaseModel):
    occasion: str = ""
    relationship: str = ""
    age_group: str = ""
    interests: list[str] = []
    budget: Optional[float] = None
    gender_preference: Optional[str] = None


class GiftRecommendation(BaseModel):
    product: dict
    relevance_score: float
    match_reasons: list[str]


class GiftFinderResult(BaseModel):
    recipient: GiftRecipient
    recommendations: list[GiftRecommendation]
    total_found: int
    summary: str


# ── Cross-sell / Upsell Models ──────────────────────────────

class CrossSellItem(BaseModel):
    product: dict
    type: str  # "complementary" | "upsell" | "accessory"
    reason: str
    match_score: float


class CrossSellResult(BaseModel):
    source_product: dict
    recommendations: list[CrossSellItem]
    cart_context: list[dict] = []


class WishlistItem(BaseModel):
    id: str
    user_id: str
    product_id: int
    product_name: str
    product_price: float
    product_category: str
    product_image: Optional[str] = None
    note: Optional[str] = None
    price_alert_threshold: Optional[float] = None
    created_at: str = ""


class PriceAlertEvent(BaseModel):
    id: str
    wishlist_item_id: str
    product_id: int
    product_name: str
    current_price: float
    target_price: float
    triggered_at: str
    notified: bool = False


# ── Advanced Auth Models ─────────────────────────────────────

class UserRole(str, Enum):
    admin = "admin"
    premium = "premium"
    user = "user"


class AuthUser(BaseModel):
    id: str
    username: str
    email: str
    hashed_password: str
    role: UserRole = UserRole.user
    disabled: bool = False
    email_verified: bool = False
    twofa_enabled: bool = False
    twofa_secret: Optional[str] = None
    failed_login_attempts: int = 0
    locked_until: Optional[str] = None
    created_at: str = ""
    last_login: Optional[str] = None


class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=32)
    email: str = Field(..., min_length=5, max_length=128)
    password: str = Field(..., min_length=8, max_length=128)


class LoginRequest(BaseModel):
    username: str
    password: str
    twofa_code: Optional[str] = None
    device_info: Optional[str] = None


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: dict


class RefreshRequest(BaseModel):
    refresh_token: str


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str


class LoginHistoryEntry(BaseModel):
    id: str
    user_id: str
    ip_address: str
    device_info: str
    success: bool
    fail_reason: Optional[str] = None
    timestamp: str


class UserSession(BaseModel):
    id: str
    user_id: str
    refresh_token_hash: str
    device_info: str
    ip_address: str
    created_at: str
    last_activity: str
    is_active: bool = True


# ── Budget Tracker Models ─────────────────────────────────────

class BudgetPeriod(str, Enum):
    daily = "daily"
    weekly = "weekly"
    monthly = "monthly"


class BudgetEntry(BaseModel):
    id: str
    user_id: str
    product_id: str
    product_name: str
    category: str
    amount: float
    quantity: int = 1
    timestamp: str = ""
    note: Optional[str] = None


class BudgetLimit(BaseModel):
    id: str
    user_id: str
    period: BudgetPeriod
    limit_amount: float
    category: Optional[str] = None
    created_at: str = ""
    updated_at: str = ""


class BudgetCheckRequest(BaseModel):
    user_id: str
    product_id: str
    product_name: str
    category: str
    amount: float
    quantity: int = 1


class BudgetCheckResult(BaseModel):
    within_budget: bool
    current_spending: float
    limit: float
    remaining: float
    message: str
    alerts: list[str] = []


class SpendingSummary(BaseModel):
    user_id: str
    period: BudgetPeriod
    total_spent: float
    entry_count: int
    category_breakdown: dict[str, float] = {}
    daily_average: float = 0.0
    limits: list[BudgetLimit] = []
    alerts: list[str] = []


class BudgetAlternative(BaseModel):
    product: dict
    original_price: float
    alternative_price: float
    savings: float
    reason: str
