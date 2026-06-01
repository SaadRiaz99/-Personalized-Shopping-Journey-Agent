import asyncio
import json
import os
import sys
import time
from dataclasses import dataclass
from typing import Optional

from openai import AsyncOpenAI
from pydantic import BaseModel, Field

from agents import (
    Agent,
    GuardrailFunctionOutput,
    InputGuardrailTripwireTriggered,
    RunContextWrapper,
    Runner,
    TResponseInputItem,
    function_tool,
    input_guardrail,
    set_tracing_disabled,
)
from agents.models.openai_chatcompletions import OpenAIChatCompletionsModel

set_tracing_disabled(disabled=True)

PRODUCTS: list[dict] = json.load(open("products.json"))

@dataclass
class UserContext:
    user_id: str
    name: str
    preferred_categories: Optional[list[str]] = None
    max_budget: Optional[float] = None

class ProductResult(BaseModel):
    id: int = Field(description="Product ID")
    name: str = Field(description="Product name")
    category: str = Field(description="Product category")
    price: float = Field(description="Current price in USD")
    rating: float = Field(description="Average customer rating (1-5)")
    in_stock: bool = Field(description="Whether the product is currently in stock")
    description: str = Field(description="Short product description")

class SearchResults(BaseModel):
    query: str = Field(description="The original search query")
    total_found: int = Field(description="Number of matching products")
    products: list[ProductResult] = Field(description="List of matching products")
    note: Optional[str] = Field(default=None, description="Any helpful note for the user")

class CategoriesResult(BaseModel):
    categories: list[str] = Field(description="Available product categories")
    total: int = Field(description="Number of categories")

class CatalogQueryCheck(BaseModel):
    is_catalog_query: bool = Field(description="Whether the user's query is about the product catalog")
    reasoning: str = Field(description="Reasoning for the classification")

@function_tool
def search_products(
    ctx: RunContextWrapper[UserContext],
    query: str,
    category: Optional[str] = None,
    max_price: Optional[float] = None,
    min_rating: Optional[float] = None,
) -> SearchResults:
    results = list(PRODUCTS)
    q = query.lower()
    results = [p for p in results if q in p["name"].lower() or q in p["description"].lower()]
    if category:
        results = [p for p in results if p["category"].lower() == category.lower()]
    if max_price is not None:
        results = [p for p in results if p["price"] <= max_price]
    if min_rating is not None:
        results = [p for p in results if p["rating"] >= min_rating]
    products = [ProductResult(id=p["id"], name=p["name"], category=p["category"], price=p["price"], rating=p["rating"], in_stock=p["stock"] > 0, description=p["description"]) for p in results]
    return SearchResults(query=query, total_found=len(products), products=products)

@function_tool
def get_product_details(product_id: int) -> ProductResult:
    p = next((p for p in PRODUCTS if p["id"] == product_id), None)
    if not p:
        return ProductResult(id=product_id, name="Not found", category="", price=0, rating=0, in_stock=False, description=f"No product found with ID {product_id}.")
    return ProductResult(id=p["id"], name=p["name"], category=p["category"], price=p["price"], rating=p["rating"], in_stock=p["stock"] > 0, description=p["description"])

@function_tool
def list_categories(dummy: Optional[str] = None) -> str:
    cats = sorted(set(p["category"] for p in PRODUCTS))
    return f"Available categories ({len(cats)}): " + ", ".join(cats)

def dynamic_instructions(ctx: RunContextWrapper[UserContext], agent: Agent[UserContext]) -> str:
    base = (
        "You are a friendly catalog search assistant. "
        "Help users find products by searching, browsing categories, and getting details.\n\n"
        "Guidelines:\n"
        "- Use search_products when filtering by name, category, price, or rating\n"
        "- Use get_product_details for more info on a specific product\n"
        "- Use list_categories to show available categories\n"
        "- If a product is out of stock, mention it and suggest alternatives\n"
        "- Be concise but helpful"
    )
    user = ctx.context
    prefs = []
    if user.preferred_categories:
        prefs.append(f"Preferred categories: {', '.join(user.preferred_categories)}")
    if user.max_budget is not None:
        prefs.append(f"Max budget: ${user.max_budget:.2f}")
    if prefs:
        base += "\n\nUser preferences:\n" + "\n".join(prefs)
    return base


# ---------------------------------------------------------------------------
# Test cases
# ---------------------------------------------------------------------------

TestResult = dict  # {"test_id": int, "name": str, "input": str, "expected": str, "passed": bool, "output": str, "error": str}

def make_test(name: str, input_text: str, expected: str, category: str) -> dict:
    return {
        "name": name,
        "input": input_text,
        "expected": expected,
        "category": category,
        "passed": False,
        "output": "",
        "error": "",
    }

def build_tests() -> list[dict]:
    tests = []

    # --- Product Search (15 tests) ---
    tests.append(make_test(
        "Search by exact product name", "find me wireless bluetooth headphones",
        "Wireless Bluetooth Headphones", "Product Search"))
    tests.append(make_test(
        "Search by partial name", "show me monitors",
        "Monitor", "Product Search"))
    tests.append(make_test(
        "Search by keyword in description", "products with noise cancelling",
        "noise", "Product Search"))
    tests.append(make_test(
        "Search within category", "show electronics under $100",
        "Electronics", "Product Search"))
    tests.append(make_test(
        "Search with max price", "find me products under $20",
        "$", "Product Search"))
    tests.append(make_test(
        "Search with min rating", "show products with rating above 4.5",
        "4.", "Product Search"))
    tests.append(make_test(
        "Search with combined filters", "electronics under $50 with rating above 4",
        "Electronics", "Product Search"))
    tests.append(make_test(
        "Search Groceries category", "what groceries do you have",
        "Groceries", "Product Search"))
    tests.append(make_test(
        "Search Sports & Fitness", "show me sports and fitness products",
        "Sports", "Product Search"))
    tests.append(make_test(
        "Search Furniture", "list furniture items",
        "Furniture", "Product Search"))
    tests.append(make_test(
        "Search Clothing", "show me clothing",
        "Clothing", "Product Search"))
    tests.append(make_test(
        "Search Books", "what books are available",
        "Books", "Product Search"))
    tests.append(make_test(
        "Search with multiple keywords", "find me cheap running shoes",
        "Running", "Product Search"))
    tests.append(make_test(
        "Search zero results", "find me unicorn products",
        "no", "Product Search"))
    tests.append(make_test(
        "Search by brand/model keyword", "show me products with USB-C",
        "USB-C", "Product Search"))

    # --- Product Details (6 tests) ---
    tests.append(make_test(
        "Get product details by ID - valid", "tell me about product 1",
        "Wireless Bluetooth Headphones", "Product Details"))
    tests.append(make_test(
        "Get product details by ID - another valid", "show details for product 50",
        "CPU Cooler", "Product Details"))
    tests.append(make_test(
        "Get product details - invalid ID", "tell me about product 99999",
        "not found", "Product Details"))
    tests.append(make_test(
        "Get product details by name", "tell me about the yoga mat",
        "Yoga Mat", "Product Details"))
    tests.append(make_test(
        "Get product details - out of stock item", "tell me about running shoes product 11",
        "out of stock", "Product Details"))
    tests.append(make_test(
        "Get product details - expensive item", "tell me about graphics card",
        "Graphics Card", "Product Details"))

    # --- Categories (5 tests) ---
    tests.append(make_test(
        "List all categories", "what categories do you have",
        "9", "Categories"))
    tests.append(make_test(
        "Ask about Electronics category", "what's in electronics",
        "Electronics", "Categories"))
    tests.append(make_test(
        "Ask about Books category", "tell me about the books category",
        "Books", "Categories"))
    tests.append(make_test(
        "Browse category counts", "how many categories are there",
        "9", "Categories"))
    tests.append(make_test(
        "Ask about Home & Kitchen", "show me home and kitchen items",
        "Home & Kitchen", "Categories"))

    # --- Recommendations & Comparisons (6 tests) ---
    tests.append(make_test(
        "Recommend products under budget", "recommend me something under $30",
        "$", "Recommendations"))
    tests.append(make_test(
        "Recommend top rated", "what are the highest rated products",
        "rating", "Recommendations"))
    tests.append(make_test(
        "Compare products", "compare headphones and earbuds",
        "headphone", "Recommendations"))
    tests.append(make_test(
        "Best seller in Electronics", "what's the best product in electronics",
        "Electronics", "Recommendations"))
    tests.append(make_test(
        "Suggest gift", "suggest a gift under $50",
        "$", "Recommendations"))
    tests.append(make_test(
        "Stock availability check", "which products are in stock",
        "stock", "Recommendations"))

    # --- Edge Cases (6 tests) ---
    tests.append(make_test(
        "Empty-like query - just category", "electronics",
        "Electronics", "Edge Cases"))
    tests.append(make_test(
        "Single word query - cheap", "cheap",
        "$", "Edge Cases"))
    tests.append(make_test(
        "Query with special characters", "find me a 27\" monitor",
        "Monitor", "Edge Cases"))
    tests.append(make_test(
        "Query with numbers", "find products costing 49.99",
        "49.99", "Edge Cases"))
    tests.append(make_test(
        "Very broad query", "show me everything",
        "product", "Edge Cases"))
    tests.append(make_test(
        "Multiple requests in one", "show me electronics and also tell me about product 5",
        "Electronics", "Edge Cases"))

    # --- Guardrail Rejection (6 tests) ---
    tests.append(make_test(
        "Reject math question", "what is 2+2",
        "only answer", "Guardrail"))
    tests.append(make_test(
        "Reject coding question", "write a python function to sort a list",
        "only answer", "Guardrail"))
    tests.append(make_test(
        "Reject general knowledge", "who is the president of the united states",
        "only answer", "Guardrail"))
    tests.append(make_test(
        "Reject unrelated chat", "how's the weather today",
        "only answer", "Guardrail"))
    tests.append(make_test(
        "Reject translation request", "translate hello to spanish",
        "only answer", "Guardrail"))
    tests.append(make_test(
        "Reject history question", "what happened in world war 2",
        "only answer", "Guardrail"))

    # --- Pricing & Availability (6 tests) ---
    tests.append(make_test(
        "Check price of specific product", "how much does the mechanical keyboard cost",
        "$", "Pricing"))
    tests.append(make_test(
        "Find products within budget", "show me products between $50 and $150",
        "$", "Pricing"))
    tests.append(make_test(
        "Find cheapest product", "what's the cheapest product you have",
        "$", "Pricing"))
    tests.append(make_test(
        "Find most expensive product", "what's the most expensive product",
        "$", "Pricing"))
    tests.append(make_test(
        "Check stock", "is the running shoes in stock",
        "stock", "Pricing"))
    tests.append(make_test(
        "Filter by price and category", "cheap electronics under $30",
        "Electronics", "Pricing"))

    for i, t in enumerate(tests, 1):
        t["test_id"] = i
    return tests


# ---------------------------------------------------------------------------
# Run tests
# ---------------------------------------------------------------------------

def check_guardrail_triggered(output: str) -> bool:
    keywords = ["only answer", "only help", "only assist", "product catalog", "cannot", "can't", "not able"]
    return any(k in output.lower() for k in keywords)

async def main():
    key = os.environ.get("OPENROUTER_API_KEY", "")
    if not key:
        print("ERROR: Set $env:OPENROUTER_API_KEY first")
        sys.exit(1)

    model = OpenAIChatCompletionsModel(
        model=os.environ.get("LLM_MODEL", "openai/gpt-4o-mini"),
        openai_client=AsyncOpenAI(api_key=key, base_url="https://openrouter.ai/api/v1"),
    )

    user_ctx = UserContext(user_id="test_user", name="Tester")

    guardrail_agent = Agent[UserContext](
        name="CatalogGuardrail",
        instructions=(
            "Determine if the user's query is about searching, browsing, or asking about "
            "products in a product catalog. Topics include: finding products, checking prices, "
            "filtering by category, product details, stock/availability, ratings, recommendations, "
            "and comparing products. Reject math, coding, general knowledge, or unrelated chat."
        ),
        output_type=CatalogQueryCheck,
        model=model,
    )

    @input_guardrail
    async def catalog_relevance_guardrail(
        ctx: RunContextWrapper[UserContext], agent: Agent[UserContext], input: str | list[TResponseInputItem]
    ) -> GuardrailFunctionOutput:
        result = await Runner.run(guardrail_agent, input, context=ctx.context)
        return GuardrailFunctionOutput(
            output_info=result.final_output,
            tripwire_triggered=not result.final_output.is_catalog_query,
        )

    agent = Agent[UserContext](
        name="CatalogSearchAgent",
        instructions=dynamic_instructions,
        model=model,
        tools=[search_products, get_product_details, list_categories],
        input_guardrails=[catalog_relevance_guardrail],
    )

    tests = build_tests()
    total = len(tests)
    passed_count = 0

    print("=" * 70)
    print(f"  Running {total} Test Cases on Catalog Search Agent")
    print(f"  Provider: OpenRouter ({os.environ.get('LLM_MODEL', 'openai/gpt-4o-mini')})")
    print("=" * 70)

    for t in tests:
        t_id = t["test_id"]
        name = t["name"]
        cat = t["category"]
        inp = t["input"]
        expected = t["expected"]

        # Truncate long input for display
        disp_input = inp[:60] + "..." if len(inp) > 60 else inp
        sys.stdout.write(f"\n[{t_id:02d}/{total}] [{cat}] {name}\n    Input: {disp_input}\n    ")

        try:
            result = await Runner.run(agent, inp, context=user_ctx)
            output = str(result.final_output)
            t["output"] = output

            if cat == "Guardrail":
                # Guardrail tests: expected NOT to pass; we check guardrail was NOT triggered
                # Actually for guardrail tests we WANT the guardrail to trigger (reject)
                # But we hit InputGuardrailTripwireTriggered exception
                # So if we get here without exception, guardrail didn't trigger -> fail
                t["passed"] = False
                t["error"] = "Guardrail did NOT trigger for non-catalog query"
                sys.stdout.write("FAIL - Guardrail did not trigger\n")
            else:
                if expected.lower() in output.lower():
                    t["passed"] = True
                    passed_count += 1
                    sys.stdout.write("PASS\n")
                else:
                    t["passed"] = False
                    t["error"] = f"Expected '{expected}' not found in output"
                    sys.stdout.write(f"FAIL - Expected '{expected}' not found\n")

        except InputGuardrailTripwireTriggered:
            t["output"] = "[GUARDRAIL TRIGGERED]"
            if cat == "Guardrail":
                t["passed"] = True
                passed_count += 1
                sys.stdout.write("PASS (guardrail correctly rejected)\n")
            else:
                t["passed"] = False
                t["error"] = "Guardrail incorrectly triggered for catalog query"
                sys.stdout.write(f"FAIL - Guardrail incorrectly triggered\n")

        except Exception as e:
            t["passed"] = False
            t["error"] = str(e)
            t["output"] = ""
            sys.stdout.write(f"ERROR - {str(e)[:80]}\n")

        # Brief delay to avoid rate limiting
        await asyncio.sleep(0.5)

    # Summary
    print("\n" + "=" * 70)
    print(f"  RESULTS: {passed_count}/{total} passed")
    print("=" * 70)

    for t in tests:
        status = "PASS" if t["passed"] else "FAIL"
        print(f"  [{status}] #{t['test_id']:02d} {t['name']}")
        if not t["passed"] and t.get("error"):
            print(f"         Error: {t['error']}")

    # Generate report.md
    generate_report(tests, total, passed_count)
    print(f"\nReport written to report.md")


def generate_report(tests: list[dict], total: int, passed: int):
    lines = []
    lines.append("# Catalog Search Agent - Test Report")
    lines.append("")
    lines.append(f"- **Date:** {time.strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append("- **Provider:** OpenRouter (openai/gpt-4o-mini)")
    lines.append(f"- **Product Catalog:** {len(PRODUCTS)} products across {len(set(p['category'] for p in PRODUCTS))} categories")
    lines.append(f"- **Total Tests:** {total}")
    lines.append(f"- **Passed:** {passed}")
    lines.append(f"- **Failed:** {total - passed}")
    lines.append(f"- **Pass Rate:** {passed/total*100:.1f}%")
    lines.append("")

    # By category
    lines.append("## Results by Category")
    lines.append("")
    lines.append("| Category | Total | Passed | Failed | Rate |")
    lines.append("|----------|-------|--------|--------|------|")
    cats = sorted(set(t["category"] for t in tests))
    for c in cats:
        ct = [t for t in tests if t["category"] == c]
        cp = sum(1 for t in ct if t["passed"])
        lines.append(f"| {c} | {len(ct)} | {cp} | {len(ct)-cp} | {cp/len(ct)*100:.0f}% |")
    lines.append("")
    lines.append("## Detailed Results")
    lines.append("")
    lines.append("| # | Category | Test Name | Input | Status | Notes |")
    lines.append("|---|----------|-----------|-------|--------|-------|")

    for t in tests:
        status = ":white_check_mark: PASS" if t["passed"] else ":x: FAIL"
        note = t.get("error", "") if not t["passed"] else ""
        inp_escaped = t["input"].replace("|", "\\|")
        note_escaped = note.replace("|", "\\|")
        lines.append(f"| {t['test_id']} | {t['category']} | {t['name']} | {inp_escaped} | {status} | {note_escaped} |")

    lines.append("")
    lines.append("## Failed Tests Detail")
    lines.append("")

    failed = [t for t in tests if not t["passed"]]
    if failed:
        for t in failed:
            lines.append(f"### #{t['test_id']}: {t['name']}")
            lines.append("")
            lines.append(f"- **Category:** {t['category']}")
            lines.append(f"- **Input:** `{t['input']}`")
            lines.append(f"- **Expected:** `{t['expected']}`")
            lines.append(f"- **Error:** {t.get('error', 'N/A')}")
            if t.get("output"):
                lines.append(f"- **Actual Output:** {t['output'][:200]}")
            lines.append("")
    else:
        lines.append("All tests passed! :tada:")
        lines.append("")

    with open("report.md", "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


if __name__ == "__main__":
    asyncio.run(main())
