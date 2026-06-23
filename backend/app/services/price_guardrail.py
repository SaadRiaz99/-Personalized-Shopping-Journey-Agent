import re
import time
from dataclasses import dataclass, field
from typing import Optional

VALID_SKU_PATTERN = r'^SKU-\d{4}$'
MAX_PRICE = 100000.0
MIN_PRICE = 0.01
MAX_RATE_LIMIT_PER_HOUR = 50
MAX_PRICE_MATCHES_PER_SESSION = 10
MAX_DISCOUNT_PER_SESSION = 2000.0
SUSPICIOUS_PRICE_RATIO = 10.0
PRICE_GOUGE_RATIO = 2.0


@dataclass
class GuardrailVerdict:
    allowed: bool = True
    reason: str = ""
    category: Optional[str] = None


@dataclass
class RateLimitState:
    count: int = 0
    window_start: float = 0.0
    total_discount_claimed: float = 0.0


class PriceGuardrail:
    def __init__(self):
        self._sessions: dict[str, RateLimitState] = {}

    def validate_input(self, sku: str, price: float) -> GuardrailVerdict:
        if not re.match(VALID_SKU_PATTERN, sku):
            return GuardrailVerdict(allowed=False, category="invalid_sku", reason=f"SKU {sku} does not match format SKU-XX000")
        if price <= 0:
            return GuardrailVerdict(allowed=False, category="invalid_price", reason=f"Price ${price:.2f} must be positive")
        if price > MAX_PRICE:
            return GuardrailVerdict(allowed=False, category="price_cap", reason=f"Price ${price:.2f} exceeds ${MAX_PRICE:.2f}")
        if price < MIN_PRICE:
            return GuardrailVerdict(allowed=False, category="price_floor", reason=f"Price ${price:.2f} below minimum ${MIN_PRICE:.2f}")
        return GuardrailVerdict(allowed=True)

    def detect_fraud(self, store_price: float, competitor_price: float) -> GuardrailVerdict:
        if competitor_price <= 0:
            return GuardrailVerdict(allowed=False, category="bad_competitor", reason="Competitor price must be positive")
        ratio = store_price / competitor_price
        if ratio > SUSPICIOUS_PRICE_RATIO:
            return GuardrailVerdict(allowed=False, category="suspicious_data", reason=f"Competitor price ${competitor_price:.2f} is <10% of store price ${store_price:.2f}")
        if competitor_price > store_price * PRICE_GOUGE_RATIO:
            return GuardrailVerdict(allowed=False, category="gouging_risk", reason=f"Competitor ${competitor_price:.2f} is >200% of store ${store_price:.2f}")
        return GuardrailVerdict(allowed=True)

    def check_rate_limit(self, user_id: str) -> GuardrailVerdict:
        now = time.time()
        state = self._sessions.get(user_id)
        if state:
            if now - state.window_start < 3600:
                if state.count >= MAX_RATE_LIMIT_PER_HOUR:
                    return GuardrailVerdict(allowed=False, category="rate_limited", reason=f"Max {MAX_RATE_LIMIT_PER_HOUR} checks/hr exceeded")
                state.count += 1
            else:
                self._sessions[user_id] = RateLimitState(count=1, window_start=now)
        else:
            self._sessions[user_id] = RateLimitState(count=1, window_start=now)
        return GuardrailVerdict(allowed=True)

    def check_abuse(self, user_id: str, discount_amount: float) -> GuardrailVerdict:
        state = self._sessions.get(user_id)
        if not state:
            return GuardrailVerdict(allowed=True)
        if state.total_discount_claimed + discount_amount > MAX_DISCOUNT_PER_SESSION:
            return GuardrailVerdict(allowed=False, category="abuse", reason=f"Session discount cap ${MAX_DISCOUNT_PER_SESSION:.2f} exceeded")
        return GuardrailVerdict(allowed=True)

    def record_discount(self, user_id: str, amount: float):
        state = self._sessions.get(user_id)
        if state:
            state.total_discount_claimed += amount

    def reset(self, user_id: str):
        self._sessions.pop(user_id, None)


price_guardrail = PriceGuardrail()
