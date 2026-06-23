import time
from typing import Any, TypedDict


class AgentRequest(TypedDict):
    agent_id: str
    source: str
    target: str
    action: str
    payload: dict[str, Any]
    timestamp: float


class AgentResponse(TypedDict):
    agent_id: str
    source: str
    target: str
    status: str
    payload: dict[str, Any]
    error: str | None
    timestamp: float


ROUTING_TABLE: dict[str, str] = {
    "search_products": "catalog_search_agent",
    "get_product_details": "catalog_search_agent",
    "list_categories": "catalog_search_agent",
    "check_deals": "deal_agent",
    "apply_discount": "deal_agent",
    "track_order": "post_purchase_agent",
    "get_customer_profile": "post_purchase_agent",
    "analyze_sentiment": "post_purchase_agent",
    "generate_retention": "post_purchase_agent",
    "record_feedback": "post_purchase_agent",
    "discover_products": "discovery_agent",
}


class AgentRouter:
    def __init__(self, routing_table: dict[str, str] | None = None) -> None:
        self._routing_table = routing_table or dict(ROUTING_TABLE)

    def route(self, request: AgentRequest) -> str | None:
        return self._routing_table.get(request["action"])

    def build_request(
        self,
        source: str,
        target: str,
        action: str,
        payload: dict[str, Any],
    ) -> AgentRequest:
        return AgentRequest(
            agent_id=f"{source}->{target}",
            source=source,
            target=target,
            action=action,
            payload=payload,
            timestamp=time.time(),
        )

    def build_response(
        self,
        request: AgentRequest,
        status: str,
        payload: dict[str, Any],
        error: str | None = None,
    ) -> AgentResponse:
        return AgentResponse(
            agent_id=f"{request['target']}->{request['source']}",
            source=request["target"],
            target=request["source"],
            status=status,
            payload=payload,
            error=error,
            timestamp=time.time(),
        )

    def register_action(self, action: str, target_agent: str) -> None:
        self._routing_table[action] = target_agent
