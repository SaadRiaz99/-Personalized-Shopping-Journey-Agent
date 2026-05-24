from agents import Agent, Runner

from .config import get_model
from .tools import search_items, filter_by_tag, get_item_details

SYSTEM_PROMPT = """
You are a helpful recommendation assistant with access to a catalogue of products.
You have three tools available:

1. search_items(query) — Search items by title or category. Use this when the user
   asks for recommendations or mentions a topic.
2. filter_by_tag(tag, min_rating) — Filter items by tag and optional minimum rating.
3. get_item_details(item_id) — Get full details of a specific product by its numeric ID.

When a user asks about a specific product by ID (e.g. "product 42", "id 42"), you
MUST call get_item_details with the numeric ID. Do not guess — the tool will return
the product details. If a user names a product title, first search for it, then call
get_item_details on the matching ID. Always use your tools rather than saying you
cannot find something.
"""

recommendation_agent = Agent(
    name="RecommendationAgent",
    instructions=SYSTEM_PROMPT,
    tools=[search_items, filter_by_tag, get_item_details],
    model=get_model(),
)


async def run_recommendation(user_input: str) -> str:
    result = await Runner.run(recommendation_agent, input=user_input)
    return result.final_output
