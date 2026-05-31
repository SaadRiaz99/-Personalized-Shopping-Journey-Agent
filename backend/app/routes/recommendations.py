from fastapi import APIRouter
from app.models import Product
from app.services.recommendation import get_recommendations
from app.routes.preferences import _user_prefs

router = APIRouter(prefix="/api/recommendations", tags=["recommendations"])


@router.get("", response_model=list[Product])
async def list_recommendations():
    return get_recommendations(_user_prefs)
