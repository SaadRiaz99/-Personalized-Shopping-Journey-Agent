from app.models import Discount, DiscountStatus
from typing import Optional
from datetime import datetime, timedelta
import random
import uuid

COMPETITOR_STORES = ["Amazon", "BestBuy", "Walmart", "Target", "eBay"]

COMPETITOR_PRICES: dict[str, dict[str, float]] = {
    "SKU-WH001": {"Amazon": 239.99, "BestBuy": 219.99, "Walmart": 229.99, "Target": 244.99, "eBay": 210.00},
    "SKU-RS001": {"Amazon": 119.99, "BestBuy": 124.99, "Walmart": 109.99, "Target": 129.99, "eBay": 115.00},
    "SKU-CM001": {"Amazon": 74.99, "BestBuy": 69.99, "Walmart": 64.99, "Target": 79.99, "eBay": 60.00},
    "SKU-SW001": {"Amazon": 189.99, "BestBuy": 179.99, "Walmart": 199.99, "Target": 194.99, "eBay": 175.00},
    "SKU-LJ001": {"Amazon": 329.99, "BestBuy": 349.99, "Walmart": 319.99, "Target": 339.99, "eBay": 300.00},
    "SKU-YM001": {"Amazon": 34.99, "BestBuy": 39.99, "Walmart": 29.99, "Target": 36.99, "eBay": 25.00},
    "SKU-BS001": {"Amazon": 54.99, "BestBuy": 49.99, "Walmart": 52.99, "Target": 57.99, "eBay": 45.00},
    "SKU-DL001": {"Amazon": 44.99, "BestBuy": 47.99, "Walmart": 39.99, "Target": 49.99, "eBay": 42.00},
}

PRICE_HISTORY: dict[str, list[dict]] = {}

def _build_history(sku: str, base: float):
    if sku in PRICE_HISTORY:
        return
    now = datetime.now()
    history = []
    for i in range(14, -1, -1):
        day = now - timedelta(days=i)
        variance = random.uniform(-0.08, 0.08)
        price = round(base * (1 + variance), 2)
        history.append({"date": day.strftime("%Y-%m-%d"), "price": price})
    PRICE_HISTORY[sku] = history

def get_price_history(sku: str) -> list[dict]:
    prices = COMPETITOR_PRICES.get(sku)
    if prices:
        avg = sum(prices.values()) / len(prices)
        _build_history(sku, avg)
    else:
        _build_history(sku, 100.0)
    return PRICE_HISTORY.get(sku, [])

def get_price_drop_alerts(sku: str, threshold_pct: float = 5.0) -> list[dict]:
    history = get_price_history(sku)
    if len(history) < 2:
        return []
    recent = history[-7:]
    alerts = []
    for i in range(1, len(recent)):
        prev_entry = recent[i - 1]
        curr_entry = recent[i]
        prev = prev_entry["price"]
        curr = curr_entry["price"]
        drop_pct = round((prev - curr) / prev * 100, 2)
        if drop_pct >= threshold_pct:
            alerts.append({
                "date": curr_entry["date"],
                "from": prev,
                "to": curr,
                "drop_pct": drop_pct,
            })
    return alerts

SIMULATED_LOWER_PRICE_SKUS = {"SKU-LJ001", "SKU-YM001"}


def fetch_competitor_price(sku: str, store: Optional[str] = None) -> dict:
    prices = COMPETITOR_PRICES.get(sku)
    if not prices:
        return {"sku": sku, "error": "SKU not found in competitor database"}

    if store:
        price = prices.get(store)
        if price is None:
            return {"sku": sku, "error": f"Store '{store}' not found for SKU"}
        return {"sku": sku, "store": store, "price": price}

    lowest_store = min(prices, key=prices.get)
    return {
        "sku": sku,
        "store": lowest_store,
        "price": prices[lowest_store],
        "all_prices": prices,
    }


def authorize_price_match(current_price: float, competitor_price: float) -> dict:
    price_diff = current_price - competitor_price

    if competitor_price <= 0:
        return {"status": "declined", "reason": "Invalid competitor price"}

    margin_ratio = price_diff / current_price

    if competitor_price < current_price and margin_ratio <= 0.25:
        discount = round(price_diff, 2)
        return {
            "status": "approved",
            "discount_amount": discount,
            "new_price": round(current_price - discount, 2),
            "reason": f"Competitor price ${competitor_price:.2f} is ${discount:.2f} lower",
        }
    elif competitor_price < current_price and margin_ratio > 0.25:
        max_discount = round(current_price * 0.25, 2)
        return {
            "status": "approved",
            "discount_amount": max_discount,
            "new_price": round(current_price - max_discount, 2),
            "reason": f"Competitor price ${competitor_price:.2f} is below 25% margin cap. Discount capped at ${max_discount:.2f}",
        }

    return {"status": "declined", "reason": "Current price is already the best available"}


class PriceMatchAgent:
    def __init__(self):
        self.discounts: dict[str, Discount] = {}

    def check_price(self, sku: str, current_price: float, product_id: str, agent_id: str) -> Discount:
        comp_result = fetch_competitor_price(sku)
        if "error" in comp_result:
            return Discount(
                id=str(uuid.uuid4())[:8],
                agent_id=agent_id,
                product_id=product_id,
                sku=sku,
                store_price=current_price,
                competitor_store="N/A",
                competitor_price=current_price,
                discount_amount=0.0,
                new_price=current_price,
                status=DiscountStatus.declined,
            )

        auth_result = authorize_price_match(current_price, comp_result["price"])

        status = DiscountStatus.approved if auth_result["status"] == "approved" else DiscountStatus.declined
        discount = Discount(
            id=str(uuid.uuid4())[:8],
            agent_id=agent_id,
            product_id=product_id,
            sku=sku,
            store_price=current_price,
            competitor_store=comp_result["store"],
            competitor_price=comp_result["price"],
            discount_amount=auth_result.get("discount_amount", 0.0),
            new_price=auth_result.get("new_price", current_price),
            status=status,
        )
        self.discounts[discount.id] = discount
        return discount

    def get_discount(self, discount_id: str) -> Optional[Discount]:
        return self.discounts.get(discount_id)

    def list_discounts(self) -> list[Discount]:
        return list(self.discounts.values())

    def apply_discount(self, discount_id: str) -> Optional[Discount]:
        discount = self.discounts.get(discount_id)
        if discount and discount.status == DiscountStatus.approved:
            discount.status = DiscountStatus.applied
            return discount
        return None


price_match_agent = PriceMatchAgent()
