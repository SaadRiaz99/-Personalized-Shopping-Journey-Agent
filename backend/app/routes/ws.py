from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.services.agent_orchestrator import orchestrator
import json

router = APIRouter()

active_connections: dict[str, list[WebSocket]] = {}


@router.websocket("/ws/agents/{agent_id}")
async def agent_websocket(websocket: WebSocket, agent_id: str):
    await websocket.accept()
    if agent_id not in active_connections:
        active_connections[agent_id] = []
    active_connections[agent_id].append(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        active_connections[agent_id].remove(websocket)


async def broadcast_event(event: str, data: dict):
    agent_id = data.get("id") or data.get("agent_id")
    if agent_id and agent_id in active_connections:
        msg = json.dumps({"event": event, "data": data})
        for ws in active_connections[agent_id]:
            try:
                await ws.send_text(msg)
            except Exception:
                pass


orchestrator.on_event(broadcast_event)
