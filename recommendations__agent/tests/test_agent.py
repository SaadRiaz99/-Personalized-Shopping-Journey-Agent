import pytest
from agent.agent import run_recommendation


@pytest.mark.asyncio
async def test_sci_fi_recommendation():
    response = await run_recommendation("I want a sci-fi book")
    assert any(word in response.lower() for word in ["dune", "martian", "sci-fi"])


@pytest.mark.asyncio
async def test_high_rated_self_help():
    response = await run_recommendation("Recommend a self-help book rated above 4.6")
    assert any(w in response.lower() for w in ["atomic habits", "deep work"])


@pytest.mark.asyncio
async def test_unknown_category_graceful():
    response = await run_recommendation("Recommend something about cooking")
    assert isinstance(response, str)
    assert len(response) > 0


@pytest.mark.asyncio
async def test_electronics_recommendation():
    response = await run_recommendation("What headphones do you recommend?")
    assert any(word in response.lower() for word in ["wh-1000xm5", "sony", "headphones"])


@pytest.mark.asyncio
async def test_empty_prompt():
    response = await run_recommendation("")
    assert isinstance(response, str)
    assert len(response) > 0


@pytest.mark.asyncio
async def test_product_by_id():
    response = await run_recommendation("tell me about the product with id 13")
    assert isinstance(response, str) and len(response) > 0
    assert any(w in response.lower() for w in ["id", "rating", "category", "title"])
