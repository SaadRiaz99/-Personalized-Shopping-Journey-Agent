from fastapi import APIRouter, HTTPException
from app.models import Agent, Discount, PriceMatchRequest
from app.services.agent_orchestrator import orchestrator
from app.services.price_match import price_match_agent
from app.services.recommendation import SAMPLE_PRODUCTS

router = APIRouter(prefix="/api/price-match", tags=["price_match"])


@router.post("/check", response_model=dict)
async def check_price_match(body: PriceMatchRequest):
    product = next((p for p in SAMPLE_PRODUCTS if p.id == body.product_id), None)
    if not product:
        raise HTTPException(404, "Product not found")

    agent = orchestrator.create_agent(
        name="PriceMatchAgent",
        task=f"Check competitor prices for {product.name} ({body.sku})",
    )

    discount = price_match_agent.check_price(body.sku, body.current_price, body.product_id, agent.id)

    return {
        "agent": agent.model_dump(),
        "discount": discount.model_dump(),
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
