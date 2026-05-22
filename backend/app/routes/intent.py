from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional

from app.models import QueryIntent
from app.services.intent_parser import parse_intent

router = APIRouter(prefix="/api/intent", tags=["intent"])


class IntentRequest(BaseModel):
    query: str


class IntentResponse(BaseModel):
    intent: QueryIntent


@router.post("", response_model=IntentResponse)
async def decode_intent(body: IntentRequest):
    intent = await parse_intent(body.query)
    return IntentResponse(intent=intent)
