from fastapi import APIRouter, HTTPException
from app.models import GiftRecipient, GiftFinderResult
from app.services.gift_finder import find_gifts

router = APIRouter(prefix="/api/gift-finder", tags=["gift-finder"])


@router.post("/find", response_model=GiftFinderResult)
async def find_gifts_endpoint(recipient: GiftRecipient):
    return find_gifts(recipient)
