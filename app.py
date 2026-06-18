"""FastAPI backend for the Deal Agent web UI."""

import os
import re
import time
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse

from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from deal_agent import CATALOG, DealAgent, SAMPLE_SCENARIOS, NAME_TO_ITEM, LOYALTY_DB

app = FastAPI(title="Deal Agent")

templates = Jinja2Templates(directory=Path(__file__).parent / "templates")

BASE_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434/v1")
API_KEY = os.environ.get("API_KEY", "ollama")
MODEL = os.environ.get("MODEL", "minimax-m2.5:cloud")

agent = DealAgent(api_key=API_KEY, model=MODEL, base_url=BASE_URL)

CONFIRM_WORDS = {"yes", "yeah", "yep", "correct", "right", "confirm", "proceed", "ok", "sure", "looks good", "that is correct", "that is right", "that's correct", "that's right", "all good"}

conversations: dict[str, dict] = {}


class ChatRequest(BaseModel):
    message: str
    session_id: str | None = None


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    catalog_items = [{"id": k, "name": v["name"], "price": f"${v['price']:.2f}", "category": v["category"]} for k, v in CATALOG.items()]
    return templates.TemplateResponse(
        request, "index.html",
        {"scenarios": SAMPLE_SCENARIOS, "catalog": catalog_items, "model": MODEL},
    )


@app.post("/api/chat")
async def chat(req: ChatRequest, request: Request):
    start = time.time()
    session_key = req.session_id or (request.client.host if request.client else "unknown")
    if session_key not in conversations:
        conversations[session_key] = {"cart_item_ids": [], "messages": [], "last_user_id": None, "pending_confirm": False}
    state = conversations[session_key]

    try:
        msg_lower = req.message.lower()
        msg_has_items = any(name in msg_lower for name in NAME_TO_ITEM)

        # Check if this is a confirmation reply
        cart_confirm = False
        if state.get("pending_confirm") and any(w in msg_lower for w in CONFIRM_WORDS):
            cart_confirm = True
            state["pending_confirm"] = False
        elif msg_has_items:
            state["pending_confirm"] = True

        accumulated = None if msg_has_items else {"cart_item_ids": state["cart_item_ids"]}

        has_uid = bool(re.search(r'user_\w+|\buser \d+|\buser\d{3}\b', msg_lower))
        effective_msg = req.message
        if not has_uid and state.get("last_user_id"):
            effective_msg = f"{state['last_user_id']} {req.message}"

        result = agent.run(effective_msg, accumulated_cart=accumulated, history=state.get("messages", []), cart_confirm=cart_confirm)
        elapsed = time.time() - start

        new_cart = result.get("cart_state", {}).get("cart_item_ids", [])
        state["cart_item_ids"] = new_cart

        parsed_uid = re.search(r'user_\w+', effective_msg.lower())
        if parsed_uid:
            state["last_user_id"] = parsed_uid.group(0)

        state.setdefault("messages", []).append({"role": "user", "content": req.message})
        state["messages"].append({"role": "assistant", "content": result["response"]})
        if len(state["messages"]) > 20:
            state["messages"] = state["messages"][-20:]

        return JSONResponse({
            "response": result["response"],
            "data": result["data"],
            "elapsed": round(elapsed, 1),
            "suppress_cards": result.get("suppress_cards", False),
        })
    except RuntimeError as e:
        return JSONResponse({"error": str(e)}, status_code=500)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
