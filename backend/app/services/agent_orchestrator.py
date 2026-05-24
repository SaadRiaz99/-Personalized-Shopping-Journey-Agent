from app.models import Agent, AgentStatus, QueryIntent, Task, TaskStatus
from app.services.intent_parser import parse_intent
from app.services.price_match import price_match_agent as pm_agent
from app.services.privacy_guardrail import privacy_guardrail
from app.services.recommendation import get_recommendations, search_products, SAMPLE_PRODUCTS
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

    async def run_agent(self, agent_id: str, user_id: str = "default") -> Optional[dict]:
        agent = self.agents.get(agent_id)
        if not agent:
            return None
        agent.status = AgentStatus.running
        agent.updated_at = datetime.now()
        await self._notify("agent_update", agent.model_dump())

        query = agent.task or ""

        guardrail_result = await privacy_guardrail.check_input(query, user_id)
        await self._notify("guardrail_input", guardrail_result.model_dump())
        safe_query = guardrail_result.sanitized_text or query

        agent_access = await privacy_guardrail.check_agent_access(
            agent.name,
            ["query", "preferences", "browsing_history"],
            user_id,
        )
        await self._notify("guardrail_access", agent_access.model_dump())
        if agent_access.action.value == "blocked":
            result = {
                "agent_id": agent_id,
                "status": "blocked",
                "message": f"Agent {agent.name} access blocked by privacy guardrail",
                "intent": None,
                "products": [],
                "guardrail": agent_access.model_dump(),
            }
            agent.status = AgentStatus.error
            agent.updated_at = datetime.now()
            await self._notify("agent_update", agent.model_dump())
            await self._notify("agent_result", result)
            return result

        intent = await parse_intent(safe_query) if safe_query else QueryIntent(raw_query="")
        await self._notify("intent_parsed", intent.model_dump())

        await asyncio.sleep(2)

        products = search_products(safe_query) if safe_query else []
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

        product_dicts = [p.model_dump() for p in products]
        output_check = await privacy_guardrail.check_output(product_dicts, user_id)
        await self._notify("guardrail_output", output_check.model_dump())

        result = {
            "agent_id": agent_id,
            "status": "completed",
            "message": f"Shopping analysis complete for {agent.name}",
            "intent": intent.model_dump(),
            "products": product_dicts,
            "guardrail": {
                "input": guardrail_result.model_dump(),
                "access": agent_access.model_dump(),
                "output": output_check.model_dump(),
            },
        }

        agent.status = AgentStatus.completed
        agent.updated_at = datetime.now()
        await self._notify("agent_update", agent.model_dump())
        await self._notify("agent_result", result)

        return result

    async def run_price_match(self, agent_id: str, product_id: str, sku: str) -> Optional[dict]:
        agent = self.agents.get(agent_id)
        if not agent:
            return None

        agent.status = AgentStatus.running
        agent.updated_at = datetime.now()
        await self._notify("agent_update", agent.model_dump())

        product = next((p for p in SAMPLE_PRODUCTS if p.id == product_id), None)
        if not product:
            result = {"agent_id": agent_id, "status": "error", "message": f"Product {product_id} not found"}
            agent.status = AgentStatus.error
            agent.updated_at = datetime.now()
            await self._notify("agent_update", agent.model_dump())
            await self._notify("agent_result", result)
            return result

        await asyncio.sleep(1)

        discount = pm_agent.check_price(sku, product.price, product_id, agent_id)

        await self._notify("price_check", {
            "product_id": product_id,
            "sku": sku,
            "store_price": product.price,
            "competitor_store": discount.competitor_store,
            "competitor_price": discount.competitor_price,
            "discount_amount": discount.discount_amount,
            "status": discount.status.value,
        })

        result = {
            "agent_id": agent_id,
            "status": "completed",
            "message": f"Price match check complete for {product.name}",
            "product": product.model_dump(),
            "discount": discount.model_dump(),
        }

        agent.status = AgentStatus.completed
        agent.updated_at = datetime.now()
        await self._notify("agent_update", agent.model_dump())
        await self._notify("agent_result", result)

        return result


orchestrator = AgentOrchestrator()
