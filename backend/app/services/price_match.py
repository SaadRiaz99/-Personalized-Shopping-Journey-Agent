from app.database import (
    create_discount as db_create_discount,
    get_db,
    get_discount as db_get_discount,
    list_discounts as db_list_discounts,
    update_discount as db_update_discount,
)
from app.models import Discount, DiscountStatus
from typing import Optional
from datetime import datetime, timedelta
import random
import uuid

COMPETITOR_STORES = ["Amazon", "BestBuy", "Walmart", "Target", "eBay"]

from shared.products import ALL_PRODUCTS

_COMPETITOR_SKUS = [f"SKU-{p['id']:04d}" for p in ALL_PRODUCTS[:20]]

COMPETITOR_PRICES: dict[str, dict[str, float]] = {
    sku: {
        store: round(base * (1 + random.uniform(-0.15, 0.05)), 2)
        for store in ["Amazon", "BestBuy", "Walmart", "Target", "eBay"]
    }
    for sku, base in zip(_COMPETITOR_SKUS, [p["price"] for p in ALL_PRODUCTS[:20]])
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

SIMULATED_LOWER_PRICE_SKUS = set(_COMPETITOR_SKUS[:5])


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
        pass

    def check_price(self, sku: str, current_price: float, product_id: str, agent_id: str) -> Discount:
        comp_result = fetch_competitor_price(sku)
        if "error" in comp_result:
            discount = Discount(
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
            with get_db() as conn:
                db_create_discount(conn, discount)
            return discount

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
        with get_db() as conn:
            db_create_discount(conn, discount)
        return discount

    def get_discount(self, discount_id: str) -> Optional[Discount]:
        with get_db() as conn:
            return db_get_discount(conn, discount_id)

    def list_discounts(self) -> list[Discount]:
        with get_db() as conn:
            return db_list_discounts(conn)

    def apply_discount(self, discount_id: str) -> Optional[Discount]:
        with get_db() as conn:
            discount = db_get_discount(conn, discount_id)
            if discount and discount.status == DiscountStatus.approved:
                discount.status = DiscountStatus.applied
                db_update_discount(conn, discount)
                return discount
            return None


price_match_agent = PriceMatchAgent()
