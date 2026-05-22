from app.models import Agent, AgentStatus, QueryIntent, Task, TaskStatus
from app.services.intent_parser import parse_intent
from app.services.recommendation import get_recommendations, search_products
from datetime import datetime
from typing import Optional
import asyncio
import uuid


class AgentOrchestrator:
    def __init__(self):
        self.agents: dict[str, Agent] = {}
        self.tasks: dict[str, Task] = {}
        self._callbacks: list = []

    def on_event(self, callback):
        self._callbacks.append(callback)

    async def _notify(self, event: str, data: dict):
        for cb in self._callbacks:
            await cb(event, data)

    def create_agent(self, name: str, task: Optional[str] = None) -> Agent:
        agent = Agent(
            id=str(uuid.uuid4())[:8],
            name=name,
            task=task,
        )
        self.agents[agent.id] = agent
        return agent

    def get_agent(self, agent_id: str) -> Optional[Agent]:
        return self.agents.get(agent_id)

    def list_agents(self) -> list[Agent]:
        return list(self.agents.values())

    def delete_agent(self, agent_id: str) -> bool:
        if agent_id in self.agents:
            del self.agents[agent_id]
            return True
        return False

    def create_task(self, agent_id: str, task_type: str) -> Optional[Task]:
        agent = self.agents.get(agent_id)
        if not agent:
            return None
        task = Task(
            id=str(uuid.uuid4())[:8],
            agent_id=agent_id,
            type=task_type,
        )
        self.tasks[task.id] = task
        return task

    def list_tasks(self) -> list[Task]:
        return list(self.tasks.values())

    async def run_agent(self, agent_id: str) -> Optional[dict]:
        agent = self.agents.get(agent_id)
        if not agent:
            return None
        agent.status = AgentStatus.running
        agent.updated_at = datetime.now()
        await self._notify("agent_update", agent.model_dump())

        query = agent.task or ""
        intent = await parse_intent(query) if query else QueryIntent(raw_query="")

        await self._notify("intent_parsed", intent.model_dump())

        await asyncio.sleep(2)

        products = search_products(query) if query else []
        if not products and intent.category:
            from app.models import UserPreferences
            category_map = {
                "electronics": "Electronics",
                "clothing": "Fashion",
                "footwear": "Fashion",
                "accessories": "Fashion",
                "home": "Home",
                "beauty": "Fashion",
                "sports": "Sports",
                "books": "Home",
                "toys": "Home",
                "food": "Home",
                "gifts": "Fashion",
            }
            mapped = category_map.get(intent.category.lower()) if intent.category else None
            if mapped:
                prefs = UserPreferences(categories=[mapped])
                if intent.budget:
                    prefs.price_max = intent.budget * 1.2
                    prefs.price_min = intent.budget * 0.3
                products = get_recommendations(prefs)

        result = {
            "agent_id": agent_id,
            "status": "completed",
            "message": f"Shopping analysis complete for {agent.name}",
            "intent": intent.model_dump(),
            "products": [p.model_dump() for p in products],
        }

        agent.status = AgentStatus.completed
        agent.updated_at = datetime.now()
        await self._notify("agent_update", agent.model_dump())
        await self._notify("agent_result", result)

        return result


orchestrator = AgentOrchestrator()
