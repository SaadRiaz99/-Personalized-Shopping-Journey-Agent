import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from app.database import init_db
from app.auth import seed_users
from app.routes import agents, auth, catalog, deals, intent, preferences, price_match, privacy, products, recommendations, ws, gift_finder, cross_sell, wishlist, budget

load_dotenv(dotenv_path=Path(__file__).parents[2] / ".env")

app = FastAPI(title="Personalized Shopping Agent API", version="1.0.0")


@app.on_event("startup")
def on_startup():
    init_db()
    seed_users()

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.environ.get("CORS_ORIGINS", "http://localhost:5173").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(agents.router)
app.include_router(catalog.router)
app.include_router(deals.router)
app.include_router(intent.router)
app.include_router(price_match.router)
app.include_router(preferences.router)
app.include_router(privacy.router)
app.include_router(products.router)
app.include_router(recommendations.router)
app.include_router(ws.router)
app.include_router(gift_finder.router)
app.include_router(cross_sell.router)
app.include_router(wishlist.router)
app.include_router(budget.router)


@app.get("/api/health")
async def health():
    return {"status": "ok"}


@app.get("/api/auth/verify")
async def verify_token_endpoint(token: str):
    from app.auth import verify_token
    payload = verify_token(token, "access")
    if payload is None:
        return {"valid": False}
    return {"valid": True, "username": payload.get("username"), "user_id": payload.get("sub")}


DIST_DIR = Path(__file__).parent / "dist"


@app.get("/{full_path:path}", include_in_schema=False)
async def spa_fallback(full_path: str):
    if DIST_DIR.is_dir() and full_path.startswith(("api/", "ws/")):
        raise HTTPException(status_code=404, detail="Not found")
    if not DIST_DIR.is_dir():
        raise HTTPException(status_code=404, detail="Not found")
    candidate = (DIST_DIR / full_path).resolve()
    if full_path and candidate.is_file() and str(candidate).startswith(str(DIST_DIR.resolve())):
        return FileResponse(candidate)
    return FileResponse(DIST_DIR / "index.html")
