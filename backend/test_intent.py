import sys
import asyncio
sys.path.insert(0, "backend")
from app.services.intent_parser import parse_intent

async def main():
    queries = [
        "I need something nice for my wife's birthday, not too expensive",
        "Need a formal outfit for a wedding ASAP, budget around $200",
        "Looking for a new laptop, preferably under $1000",
        "Just browsing for some casual shoes",
    ]
    for q in queries:
        result = await parse_intent(q)
        print(f"Query: {q}")
        print(f"  {result.model_dump()}\n")

asyncio.run(main())
