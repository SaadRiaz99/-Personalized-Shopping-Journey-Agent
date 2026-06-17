from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import init_db
from app.auth import seed_users
from app.routes import auth, documents, chat, conversations, admin

load_dotenv(dotenv_path=Path(__file__).parents[2] / ".env")

app = FastAPI(
    title="RAG Document Q&A API",
    version="2.0.0",
    description="Retrieval-Augmented Generation API for document Q&A",
)


@app.on_event("startup")
def on_startup():
    init_db()
    seed_users()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(documents.router)
app.include_router(chat.router)
app.include_router(conversations.router)
app.include_router(admin.router)


@app.get("/api/health")
async def health():
    from app.services.vector_store import vector_store
    vs_health = vector_store.health_check()
    return {
        "status": "ok",
        "version": "2.0.0",
        "vector_store": vs_health,
    }


@app.get("/api/auth/verify")
async def verify_token_endpoint(token: str):
    from app.auth import verify_token
    payload = verify_token(token, "access")
    if payload is None:
        return {"valid": False}
    return {"valid": True, "username": payload.get("username"), "user_id": payload.get("sub")}
