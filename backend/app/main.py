from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import agents, intent, preferences, privacy, products, ws

load_dotenv(dotenv_path=Path(__file__).parents[2] / ".env")

app = FastAPI(title="Personalized Shopping Agent API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(agents.router)
app.include_router(intent.router)
app.include_router(preferences.router)
app.include_router(privacy.router)
app.include_router(products.router)
app.include_router(ws.router)


@app.get("/api/health")
async def health():
    return {"status": "ok"}
