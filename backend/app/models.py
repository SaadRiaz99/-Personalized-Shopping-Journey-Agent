from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum


class AgentStatus(str, Enum):
    idle = "idle"
    running = "running"
    completed = "completed"
    error = "error"


class TaskStatus(str, Enum):
    pending = "pending"
    running = "running"
    completed = "completed"
    failed = "failed"


class Agent(BaseModel):
    id: str
    name: str
    status: AgentStatus = AgentStatus.idle
    task: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class Product(BaseModel):
    id: str
    name: str
    description: str
    price: float
    category: str
    image_url: Optional[str] = None
    rating: float = 0.0
    tags: list[str] = []


class UserPreferences(BaseModel):
    categories: list[str] = []
    price_min: float = 0.0
    price_max: float = 10000.0
    brands: list[str] = []
    budget: float = 1000.0


class Task(BaseModel):
    id: str
    agent_id: str
    type: str
    status: TaskStatus = TaskStatus.pending
    result: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class QueryIntent(BaseModel):
    category: Optional[str] = None
    budget: Optional[float] = None
    budget_currency: Optional[str] = "USD"
    occasion: Optional[str] = None
    style_preferences: list[str] = []
    urgency: Optional[str] = None
    raw_query: str = ""


class AgentCreate(BaseModel):
    name: str
    task: Optional[str] = None


class TaskCreate(BaseModel):
    agent_id: str
    type: str
