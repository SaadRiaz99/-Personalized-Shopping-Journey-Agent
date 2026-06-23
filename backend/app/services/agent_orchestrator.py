from app.database import (
    create_agent as db_create_agent,
    create_task as db_create_task,
    delete_agent as db_delete_agent,
    get_agent as db_get_agent,
    get_db,
    list_agents as db_list_agents,
    list_tasks as db_list_tasks,
    update_agent as db_update_agent,
)
from app.models import (
    Agent, AgentStatus, PrivacyRegion, QueryIntent, Task, TaskStatus,
    GiftRecipient, GiftFinderResult,
    CrossSellResult,
)
from app.services.intent_parser import parse_intent
from app.services.price_match import price_match_agent as pm_agent
from app.services.privacy_guardrail import privacy_guardrail
from app.services.recommendation import get_recommendations, search_products
from app.services.safety_guardrail import check_safety as check_safety_guardrail
from app.services.catalog_search import search_products as catalog_search_products, get_product as catalog_get_product, list_categories as catalog_list_categories
from app.services.gift_finder import find_gifts
from app.services.cross_sell import get_cross_sell
from datetime import datetime
from typing import Optional
import asyncio
import uuid


class AgentOrchestrator:
    def __init__(self):
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
        with get_db() as conn:
            db_create_agent(conn, agent)
        return agent

    def get_agent(self, agent_id: str) -> Optional[Agent]:
        with get_db() as conn:
            return db_get_agent(conn, agent_id)

    def list_agents(self) -> list[Agent]:
        with get_db() as conn:
            return db_list_agents(conn)

    def delete_agent(self, agent_id: str) -> bool:
        with get_db() as conn:
            return db_delete_agent(conn, agent_id)

    def create_task(self, agent_id: str, task_type: str) -> Optional[Task]:
        with get_db() as conn:
            agent = db_get_agent(conn, agent_id)
            if not agent:
                return None
            task = Task(
                id=str(uuid.uuid4())[:8],
                agent_id=agent_id,
                type=task_type,
            )
            db_create_task(conn, task)
            return task

    def list_tasks(self) -> list[Task]:
        with get_db() as conn:
            return db_list_tasks(conn)

    async def run_agent(self, agent_id: str, user_id: str = "default") -> Optional[dict]:
        with get_db() as conn:
            agent = db_get_agent(conn, agent_id)
            if not agent:
                return None
            agent.status = AgentStatus.running
            agent.updated_at = datetime.now()
            db_update_agent(conn, agent)
        await self._notify("agent_update", agent.model_dump())

        query = agent.task or ""

        guardrail_result = await privacy_guardrail.check_input(query, user_id)
        await self._notify("guardrail_input", guardrail_result.model_dump())
        safe_query = guardrail_result.sanitized_text or query

        profile = privacy_guardrail.get_or_create_profile(user_id)
        safety_check = await check_safety_guardrail(safe_query, profile.region)
        await self._notify("guardrail_safety", safety_check.model_dump())
        if not safety_check.allowed:
            result = {
                "agent_id": agent_id,
                "status": "blocked",
                "message": safety_check.blocked_reason,
                "intent": None,
                "products": [],
                "guardrail": {"safety": safety_check.model_dump()},
            }
            agent.status = AgentStatus.error
            agent.updated_at = datetime.now()
            with get_db() as conn:
                db_update_agent(conn, agent)
            await self._notify("agent_update", agent.model_dump())
            await self._notify("agent_result", result)
            return result

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
            with get_db() as conn:
                db_update_agent(conn, agent)
            await self._notify("agent_update", agent.model_dump())
            await self._notify("agent_result", result)
            return result

        intent = await parse_intent(safe_query) if safe_query else QueryIntent(raw_query="")
        await self._notify("intent_parsed", intent.model_dump())

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
        with get_db() as conn:
            db_update_agent(conn, agent)
        await self._notify("agent_update", agent.model_dump())
        await self._notify("agent_result", result)

        return result

    async def run_price_match(self, agent_id: str, product_id: str, sku: str) -> Optional[dict]:
        from shared.products import ALL_PRODUCTS as CATALOG

        with get_db() as conn:
            agent = db_get_agent(conn, agent_id)
            if not agent:
                return None

            agent.status = AgentStatus.running
            agent.updated_at = datetime.now()
            db_update_agent(conn, agent)
        await self._notify("agent_update", agent.model_dump())

        product = next((p for p in CATALOG if str(p["id"]) == product_id), None)
        if not product:
            result = {"agent_id": agent_id, "status": "error", "message": f"Product {product_id} not found"}
            agent.status = AgentStatus.error
            agent.updated_at = datetime.now()
            with get_db() as conn:
                db_update_agent(conn, agent)
            await self._notify("agent_update", agent.model_dump())
            await self._notify("agent_result", result)
            return result

        discount = pm_agent.check_price(sku, product["price"], product_id, agent_id)

        await self._notify("price_check", {
            "product_id": product_id,
            "sku": sku,
            "store_price": product["price"],
            "competitor_store": discount.competitor_store,
            "competitor_price": discount.competitor_price,
            "discount_amount": discount.discount_amount,
            "status": discount.status.value,
        })

        result = {
            "agent_id": agent_id,
            "status": "completed",
            "message": f"Price match check complete for {product['name']}",
            "product": product,
            "discount": discount.model_dump(),
        }

        agent.status = AgentStatus.completed
        agent.updated_at = datetime.now()
        with get_db() as conn:
            db_update_agent(conn, agent)
        await self._notify("agent_update", agent.model_dump())
        await self._notify("agent_result", result)

        return result

    async def run_gift_finder(self, agent_id: str, recipient: GiftRecipient) -> Optional[dict]:
        with get_db() as conn:
            agent = db_get_agent(conn, agent_id)
            if not agent:
                return None
            agent.status = AgentStatus.running
            agent.updated_at = datetime.now()
            db_update_agent(conn, agent)
        await self._notify("agent_update", agent.model_dump())

        result_data = find_gifts(recipient)

        result = {
            "agent_id": agent_id,
            "status": "completed",
            "message": f"Gift finder complete — found {result_data.total_found} ideas",
            "gift_result": result_data.model_dump(),
        }

        agent.status = AgentStatus.completed
        agent.updated_at = datetime.now()
        with get_db() as conn:
            db_update_agent(conn, agent)
        await self._notify("agent_update", agent.model_dump())
        await self._notify("agent_result", result)
        return result

    async def run_cross_sell_agent(self, agent_id: str, product_id: int) -> Optional[dict]:
        with get_db() as conn:
            agent = db_get_agent(conn, agent_id)
            if not agent:
                return None
            agent.status = AgentStatus.running
            agent.updated_at = datetime.now()
            db_update_agent(conn, agent)
        await self._notify("agent_update", agent.model_dump())

        result_data = get_cross_sell(product_id)

        result = {
            "agent_id": agent_id,
            "status": "completed",
            "message": f"Cross-sell analysis complete — found {len(result_data.recommendations)} recommendations",
            "cross_sell_result": result_data.model_dump(),
        }

        agent.status = AgentStatus.completed
        agent.updated_at = datetime.now()
        with get_db() as conn:
            db_update_agent(conn, agent)
        await self._notify("agent_update", agent.model_dump())
        await self._notify("agent_result", result)
        return result

    async def run_collaborative_task(self, query: str, user_id: str = "default") -> dict:
        collaboration_id = str(uuid.uuid4())[:8]
        await self._notify("collaboration_started", {"id": collaboration_id, "query": query})

        profile = privacy_guardrail.get_or_create_profile(user_id)
        safety_check = await check_safety_guardrail(query, profile.region)
        await self._notify("guardrail_safety", safety_check.model_dump())
        if not safety_check.allowed:
            return {
                "collaboration_id": collaboration_id,
                "status": "blocked",
                "query": query,
                "message": safety_check.blocked_reason,
                "intent": None,
                "products": [],
                "guardrail": {"safety": safety_check.model_dump()},
            }

        # 1. Researcher Agent: Parse Intent & Search Catalog
        researcher = self.create_agent(f"Researcher-{collaboration_id}", task=query)
        researcher.status = AgentStatus.running
        with get_db() as conn:
            db_update_agent(conn, researcher)
        await self._notify("agent_update", researcher.model_dump())
        
        intent = await parse_intent(query)
        # Extract key search terms from the query (remove filler words and price terms)
        filler = {"find", "me", "a", "an", "the", "for", "under", "good", "nice", "need", "i", "want", "some", "with", "and", "or", "budget", "around", "about", "get", "please", "can", "you", "help", "looking"}
        search_terms = " ".join(
            w for w in query.lower().split()
            if w not in filler
            and not w.startswith("$")
            and not w.replace(".","").replace(",","").isdigit()
        )
        cat_search = catalog_search_products(
            query=search_terms, 
            category=intent.category, 
            max_price=intent.budget,
            page_size=5
        )
        products = cat_search["products"]
        # Fallback: if text search yields nothing, search by category only
        if not products and intent.category:
            cat_search = catalog_search_products(
                query="",
                category=intent.category,
                max_price=intent.budget,
                sort_by="rating",
                page_size=5
            )
            products = cat_search["products"]
        researcher.status = AgentStatus.completed
        with get_db() as conn:
            db_update_agent(conn, researcher)
        await self._notify("agent_update", researcher.model_dump())
        await self._notify("collaboration_step", {"step": "research", "agent": researcher.name, "found": len(products)})

        # 2. Auditor Agent: Price Match Check
        auditor = self.create_agent(f"Auditor-{collaboration_id}", task="Price audit")
        auditor.status = AgentStatus.running
        with get_db() as conn:
            db_update_agent(conn, auditor)
        await self._notify("agent_update", auditor.model_dump())
        
        audited_products = []
        for p in products:
            sku = p.get("sku")
            if sku:
                discount = pm_agent.check_price(sku, p["price"], str(p["id"]), auditor.id)
                p_copy = p.copy()
                p_copy["audit"] = discount.model_dump()
                audited_products.append(p_copy)
            else:
                audited_products.append(p)
        
        auditor.status = AgentStatus.completed
        with get_db() as conn:
            db_update_agent(conn, auditor)
        await self._notify("agent_update", auditor.model_dump())
        await self._notify("collaboration_step", {"step": "audit", "agent": auditor.name, "processed": len(audited_products)})

        # 3. Stylist Agent: Finalize and Personalize (Simulation)
        stylist = self.create_agent(f"Stylist-{collaboration_id}", task="Personalization")
        stylist.status = AgentStatus.running
        with get_db() as conn:
            db_update_agent(conn, stylist)
        await self._notify("agent_update", stylist.model_dump())
        
        # Sort by combination of rating and price match availability
        final_products = sorted(
            audited_products, 
            key=lambda x: (x.get("rating", 0), x.get("audit", {}).get("discount_amount", 0)), 
            reverse=True
        )

        stylist.status = AgentStatus.completed
        with get_db() as conn:
            db_update_agent(conn, stylist)
        await self._notify("agent_update", stylist.model_dump())
        
        result = {
            "collaboration_id": collaboration_id,
            "status": "completed",
            "query": query,
            "intent": intent.model_dump(),
            "products": final_products,
            "summary": f"The Council has found {len(final_products)} options. Researcher identified {len(products)} matches, Auditor verified prices, and Stylist prioritized the best value."
        }
        
        await self._notify("collaboration_finished", result)
        return result

orchestrator = AgentOrchestrator()
