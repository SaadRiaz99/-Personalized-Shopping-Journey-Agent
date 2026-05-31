from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import init_db
from app.routes import agents, auth, catalog, deals, intent, preferences, price_match, privacy, products, ws

load_dotenv(dotenv_path=Path(__file__).parents[2] / ".env")

app = FastAPI(title="Personalized Shopping Agent API", version="1.0.0")


@app.on_event("startup")
def on_startup():
    init_db()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
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
app.include_router(ws.router)


@app.get("/api/health")
async def health():
    return {"status": "ok"}


@app.get("/api/auth/verify")
async def verify_token_endpoint(token: str):
    from app.auth import verify_token
    payload = verify_token(token)
    if payload is None:
        return {"valid": False}
    return {"valid": True, "username": payload.get("sub")}
