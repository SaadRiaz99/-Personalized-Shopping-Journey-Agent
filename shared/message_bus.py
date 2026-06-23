from enum import Enum
from typing import Callable, TypedDict
from collections import defaultdict


class Topics(str, Enum):
    PRODUCT_QUERY = "product.query"
    PRODUCT_RESULT = "product.result"
    PRICE_CHECK = "price.check"
    DEAL_QUERY = "deal.query"
    DEAL_RESULT = "deal.result"
    POST_PURCHASE_EVENT = "post_purchase.event"


class AgentMessage(TypedDict):
    agent_name: str
    topic: str
    payload: dict


Callback = Callable[[AgentMessage], None]


class MessageBus:
    _instance: "MessageBus | None" = None

    def __new__(cls) -> "MessageBus":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._subscribers = defaultdict(list)
        return cls._instance

    def __init__(self) -> None:
        self._subscribers: dict[str, list[tuple[str, Callback]]] = defaultdict(list)

    def publish(self, agent_name: str, topic: str, payload: dict) -> None:
        message: AgentMessage = {
            "agent_name": agent_name,
            "topic": topic,
            "payload": payload,
        }
        callbacks = self._subscribers.get(topic, [])
        for subscriber_agent, callback in callbacks:
            callback(message)

    def subscribe(self, agent_name: str, topic: str, callback: Callback) -> None:
        self._subscribers[topic].append((agent_name, callback))

    def broadcast(self, topic: str, payload: dict) -> None:
        message: AgentMessage = {
            "agent_name": "system",
            "topic": topic,
            "payload": payload,
        }
        callbacks = self._subscribers.get(topic, [])
        for subscriber_agent, callback in callbacks:
            callback(message)
