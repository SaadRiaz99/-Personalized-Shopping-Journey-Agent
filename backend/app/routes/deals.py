from fastapi import APIRouter, HTTPException
from app.models import DealSessionRequest, Promotion
from app.services.deal_agent import deal_agent

router = APIRouter(prefix="/api/deals", tags=["deals"])


@router.get("/promotions")
async def list_promotions():
    return [p.model_dump() for p in deal_agent.get_active_promotions()]


@router.get("/promotions/{promo_id}")
async def get_promotion(promo_id: str):
    for p in deal_agent.get_active_promotions():
        if p.id == promo_id:
            return p.model_dump()
    raise HTTPException(404, "Promotion not found")


@router.post("/optimize")
async def optimize_cart(body: DealSessionRequest):
    result = deal_agent.process_cart(body)
    return result


@router.post("/apply/{stack_id}")
async def apply_stack(stack_id: str):
    stack = deal_agent.apply_stack(stack_id)
    if not stack:
        raise HTTPException(404, "Discount stack not found or already expired")
    return {
        "message": "Discounts have been auto-applied to your checkout session!",
        "stack": stack.model_dump(),
    }


@router.get("/stacks")
async def list_stacks():
    return [s.model_dump() for s in deal_agent.list_stacks()]


@router.get("/stacks/{stack_id}")
async def get_stack(stack_id: str):
    stack = deal_agent.get_stack(stack_id)
    if not stack:
        raise HTTPException(404, "Stack not found")
    return stack.model_dump()
