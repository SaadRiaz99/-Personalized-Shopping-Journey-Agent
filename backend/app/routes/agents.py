from fastapi import APIRouter, HTTPException
from app.models import Agent, AgentCreate
from app.services.agent_orchestrator import orchestrator

router = APIRouter(prefix="/api/agents", tags=["agents"])


@router.get("", response_model=list[Agent])
async def list_agents():
    return orchestrator.list_agents()


@router.post("", response_model=Agent, status_code=201)
async def create_agent(body: AgentCreate):
    return orchestrator.create_agent(body.name, body.task)


@router.get("/{agent_id}", response_model=Agent)
async def get_agent(agent_id: str):
    agent = orchestrator.get_agent(agent_id)
    if not agent:
        raise HTTPException(404, "Agent not found")
    return agent


@router.delete("/{agent_id}", status_code=204)
async def delete_agent(agent_id: str):
    if not orchestrator.delete_agent(agent_id):
        raise HTTPException(404, "Agent not found")


@router.post("/{agent_id}/run")
async def run_agent(agent_id: str):
    agent = orchestrator.get_agent(agent_id)
    if not agent:
        raise HTTPException(404, "Agent not found")
    result = await orchestrator.run_agent(agent_id)
    return {"status": "started", "agent_id": agent_id}


@router.post("/collaboration")
async def run_collaborative_agent(body: dict):
    query = body.get("query")
    if not query:
        raise HTTPException(400, "Query is required")
    result = await orchestrator.run_collaborative_task(query)
    return result
