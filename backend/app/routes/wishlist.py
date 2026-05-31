from fastapi import APIRouter, HTTPException, Header
from datetime import datetime
from typing import Optional
import uuid

from app.database import (
    get_db,
    create_wishlist_item as db_create_wishlist,
    get_wishlist as db_get_wishlist,
    delete_wishlist_item as db_delete_wishlist,
    update_wishlist_item as db_update_wishlist,
    get_wishlist_item as db_get_wishlist_item,
    create_price_alert as db_create_alert,
    list_price_alerts as db_list_alerts,
)
from app.models import WishlistItem, PriceAlertEvent

router = APIRouter(prefix="/api/wishlist", tags=["wishlist"])


def _user_id(x_user_id: Optional[str] = Header(None)) -> str:
    return x_user_id or "default"


@router.get("")
async def get_wishlist(user_id: str = Header("default")):
    with get_db() as conn:
        items = db_get_wishlist(conn, user_id)
    return {"items": [i.model_dump() for i in items], "total": len(items)}


@router.post("", status_code=201)
async def add_to_wishlist(body: dict, user_id: str = Header("default")):
    required = ["product_id", "product_name", "product_price", "product_category"]
    for r in required:
        if r not in body:
            raise HTTPException(400, f"{r} is required")
    item = WishlistItem(
        id=str(uuid.uuid4())[:8],
        user_id=user_id,
        product_id=body["product_id"],
        product_name=body["product_name"],
        product_price=body["product_price"],
        product_category=body["product_category"],
        product_image=body.get("product_image"),
        note=body.get("note"),
        price_alert_threshold=body.get("price_alert_threshold"),
        created_at=datetime.now().isoformat(),
    )
    with get_db() as conn:
        db_create_wishlist(conn, item)
    return item.model_dump()


@router.delete("/{item_id}")
async def remove_from_wishlist(item_id: str):
    with get_db() as conn:
        if not db_delete_wishlist(conn, item_id):
            raise HTTPException(404, "Wishlist item not found")
    return {"status": "deleted"}


@router.patch("/{item_id}")
async def update_wishlist_item(item_id: str, body: dict):
    with get_db() as conn:
        existing = db_get_wishlist_item(conn, item_id)
        if not existing:
            raise HTTPException(404, "Wishlist item not found")
        if "note" in body:
            existing.note = body["note"]
        if "price_alert_threshold" in body:
            existing.price_alert_threshold = body["price_alert_threshold"]
        db_update_wishlist(conn, existing)
    return existing.model_dump()


@router.post("/alerts/check")
async def check_price_alerts(user_id: str = Header("default")):
    from shared.products import ALL_PRODUCTS
    triggered = []
    with get_db() as conn:
        items = db_get_wishlist(conn, user_id)
        for item in items:
            if item.price_alert_threshold is None:
                continue
            product = next((p for p in ALL_PRODUCTS if p["id"] == item.product_id), None)
            if product and product["price"] <= item.price_alert_threshold:
                alert = PriceAlertEvent(
                    id=str(uuid.uuid4())[:8],
                    wishlist_item_id=item.id,
                    product_id=item.product_id,
                    product_name=item.product_name,
                    current_price=product["price"],
                    target_price=item.price_alert_threshold,
                    triggered_at=datetime.now().isoformat(),
                )
                db_create_alert(conn, alert)
                triggered.append(alert.model_dump())
    return {"alerts_triggered": triggered, "count": len(triggered)}


@router.get("/alerts")
async def get_price_alerts(user_id: str = Header("default")):
    with get_db() as conn:
        alerts = db_list_alerts(conn, user_id)
    return {"alerts": [a.model_dump() for a in alerts], "total": len(alerts)}
