from fastapi import APIRouter, HTTPException
from app.models import UserPreferences

router = APIRouter(prefix="/api/preferences", tags=["preferences"])

_user_prefs = UserPreferences()


@router.get("", response_model=UserPreferences)
async def get_preferences():
    return _user_prefs


@router.put("", response_model=UserPreferences)
async def update_preferences(body: UserPreferences):
    global _user_prefs
    _user_prefs = body
    return _user_prefs
