from fastapi import APIRouter, HTTPException, Header, Query
from app.models import Agent, Discount, PriceMatchRequest
from app.services.agent_orchestrator import orchestrator
from app.services.price_match import price_match_agent, get_price_history, get_price_drop_alerts, fetch_competitor_price
from app.services.price_guardrail import price_guardrail
from shared.products import ALL_PRODUCTS as CATALOG_PRODUCTS

router = APIRouter(prefix="/api/price-match", tags=["price_match"])


@router.get("/products", response_model=list[dict])
async def list_price_match_products():
    products = []
    for p in CATALOG_PRODUCTS[:20]:
        sku = f"SKU-{p['id']:04d}"
        from app.services.price_match import fetch_competitor_price
        comp = fetch_competitor_price(sku)
        products.append({
            "id": str(p["id"]),
            "name": p["name"],
            "category": p["category"],
            "store_price": p["price"],
            "rating": p.get("rating", 0),
            "sku": sku,
            "tags": [p["category"].lower()],
            "description": p.get("description", ""),
            "competitor": comp if "error" not in comp else None,
            "history": get_price_history(sku),
            "alerts": get_price_drop_alerts(sku),
        })
    return products


@router.post("/check", response_model=dict)
async def check_price_match(body: PriceMatchRequest, x_user_id: str = Header("default")):
    input_check = price_guardrail.validate_input(body.sku, body.current_price)
    if not input_check.allowed:
        return {"error": True, "guardrail": input_check.__dict__, "discount": None}

    comp_result = fetch_competitor_price(body.sku)
    comp_price = comp_result.get("price", 0) if "error" not in comp_result else 0
    fraud_check = price_guardrail.detect_fraud(body.current_price, comp_price)
    if not fraud_check.allowed:
        return {"error": True, "guardrail": fraud_check.__dict__, "discount": None}

    rate_check = price_guardrail.check_rate_limit(x_user_id)
    if not rate_check.allowed:
        return {"error": True, "guardrail": rate_check.__dict__, "discount": None}

    product = next((p for p in CATALOG_PRODUCTS if str(p["id"]) == body.product_id), None)
    if not product:
        raise HTTPException(404, "Product not found")

    agent = orchestrator.create_agent(
        name="PriceMatchAgent",
        task=f"Check competitor prices for {product['name']} ({body.sku})",
    )

    discount = price_match_agent.check_price(body.sku, body.current_price, body.product_id, agent.id)

    abuse_check = price_guardrail.check_abuse(x_user_id, discount.discount_amount)
    if not abuse_check.allowed:
        return {"error": True, "guardrail": abuse_check.__dict__, "discount": None}

    price_guardrail.record_discount(x_user_id, discount.discount_amount)

    return {
        "agent": agent.model_dump(),
        "discount": discount.model_dump(),
        "guardrail": {"input": input_check.__dict__, "rate": rate_check.__dict__},
    }


@router.post("/agents/{agent_id}/check", response_model=dict)
async def run_price_match_agent(agent_id: str, body: PriceMatchRequest):
    agent = orchestrator.get_agent(agent_id)
    if not agent:
        raise HTTPException(404, "Agent not found")

    result = await orchestrator.run_price_match(agent_id, body.product_id, body.sku)
    if not result:
        raise HTTPException(404, "Failed to run price match")

    return result


@router.get("/discounts", response_model=list[Discount])
async def list_discounts():
    return price_match_agent.list_discounts()


@router.get("/discounts/{discount_id}", response_model=Discount)
async def get_discount(discount_id: str):
    discount = price_match_agent.get_discount(discount_id)
    if not discount:
        raise HTTPException(404, "Discount not found")
    return discount


@router.post("/discounts/{discount_id}/apply", response_model=Discount)
async def apply_discount(discount_id: str):
    discount = price_match_agent.apply_discount(discount_id)
    if not discount:
        raise HTTPException(404, "Discount not found or not in approvable state")
    return discount


@router.get("/competitor-prices/{sku}", response_model=dict)
async def get_competitor_prices(sku: str, store: str = None):
    from app.services.price_match import fetch_competitor_price

    result = fetch_competitor_price(sku, store)
    if "error" in result:
        raise HTTPException(404, result["error"])
    return result


@router.get("/history/{sku}", response_model=dict)
async def price_history(sku: str):
    return {"sku": sku, "history": get_price_history(sku), "alerts": get_price_drop_alerts(sku)}


@router.get("/alerts", response_model=list[dict])
async def price_alerts(threshold: float = Query(5.0, description="Minimum price drop % to alert")):
    alerts = []
    for p in CATALOG_PRODUCTS[:20]:
        sku = f"SKU-{p['id']:04d}"
        pa = get_price_drop_alerts(sku, threshold)
        if pa:
            alerts.append({"product_id": str(p["id"]), "product_name": p["name"], "sku": sku, "alerts": pa})
    return alerts
