from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from app.models import BudgetCheckRequest, BudgetPeriod
from app.services.budget_tracker import budget_tracker

router = APIRouter(prefix="/api/budget", tags=["budget"])


class SetLimitRequest(BaseModel):
    user_id: str
    period: BudgetPeriod
    limit_amount: float
    category: Optional[str] = None


class TrackEntryRequest(BaseModel):
    user_id: str
    product_id: str
    product_name: str
    category: str
    amount: float
    quantity: int = 1
    note: Optional[str] = None


@router.post("/track")
async def track_entry(body: TrackEntryRequest):
    if body.amount <= 0:
        raise HTTPException(400, "Amount must be positive")
    if body.quantity < 1:
        raise HTTPException(400, "Quantity must be at least 1")
    entry = budget_tracker.track_entry(
        user_id=body.user_id,
        product_id=body.product_id,
        product_name=body.product_name,
        category=body.category,
        amount=body.amount,
        quantity=body.quantity,
        note=body.note,
    )
    return entry.model_dump()


@router.get("/summary/{user_id}")
async def get_summary(user_id: str, period: str = "monthly"):
    try:
        p = BudgetPeriod(period)
    except ValueError:
        raise HTTPException(400, f"Invalid period: {period}. Must be daily, weekly, or monthly.")
    return budget_tracker.get_summary(user_id, p).model_dump()


@router.post("/check")
async def check_budget(body: BudgetCheckRequest):
    return budget_tracker.check_budget(body).model_dump()


@router.post("/set-limit")
async def set_limit(body: SetLimitRequest):
    if body.limit_amount <= 0:
        raise HTTPException(400, "Limit amount must be positive")
    limit = budget_tracker.set_limit(
        user_id=body.user_id,
        period=body.period,
        limit_amount=body.limit_amount,
        category=body.category,
    )
    return limit.model_dump()


@router.get("/limits/{user_id}")
async def get_limits(user_id: str):
    limits = budget_tracker.get_limits(user_id)
    return [l.model_dump() for l in limits]


@router.get("/entries/{user_id}")
async def get_entries(user_id: str, period: Optional[str] = None):
    p = BudgetPeriod(period) if period else None
    entries = budget_tracker.get_entries(user_id, period=p)
    return [e.model_dump() for e in entries]


@router.delete("/entries/{entry_id}")
async def delete_entry(entry_id: str):
    if not budget_tracker.delete_entry(entry_id):
        raise HTTPException(404, "Entry not found")
    return {"message": "Entry deleted"}


@router.delete("/limits/{limit_id}")
async def delete_limit(limit_id: str):
    if not budget_tracker.delete_limit(limit_id):
        raise HTTPException(404, "Limit not found")
    return {"message": "Limit deleted"}
