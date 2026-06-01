# Catalog Search Agent - Test Report

- **Date:** 2026-06-01 14:16:59
- **Provider:** OpenRouter (openai/gpt-4o-mini)
- **Product Catalog:** 906 products across 9 categories
- **Total Tests:** 50
- **Passed:** 42
- **Failed:** 8
- **Pass Rate:** 84.0%

## Results by Category

| Category | Total | Passed | Failed | Rate |
|----------|-------|--------|--------|------|
| Categories | 5 | 3 | 2 | 60% |
| Edge Cases | 6 | 4 | 2 | 67% |
| Guardrail | 6 | 6 | 0 | 100% |
| Pricing | 6 | 6 | 0 | 100% |
| Product Details | 6 | 2 | 4 | 33% |
| Product Search | 15 | 15 | 0 | 100% |
| Recommendations | 6 | 6 | 0 | 100% |

## Detailed Results

| # | Category | Test Name | Input | Status | Notes |
|---|----------|-----------|-------|--------|-------|
| 1 | Product Search | Search by exact product name | find me wireless bluetooth headphones | :white_check_mark: PASS |  |
| 2 | Product Search | Search by partial name | show me monitors | :white_check_mark: PASS |  |
| 3 | Product Search | Search by keyword in description | products with noise cancelling | :white_check_mark: PASS |  |
| 4 | Product Search | Search within category | show electronics under $100 | :white_check_mark: PASS |  |
| 5 | Product Search | Search with max price | find me products under $20 | :white_check_mark: PASS |  |
| 6 | Product Search | Search with min rating | show products with rating above 4.5 | :white_check_mark: PASS |  |
| 7 | Product Search | Search with combined filters | electronics under $50 with rating above 4 | :white_check_mark: PASS |  |
| 8 | Product Search | Search Groceries category | what groceries do you have | :white_check_mark: PASS |  |
| 9 | Product Search | Search Sports & Fitness | show me sports and fitness products | :white_check_mark: PASS |  |
| 10 | Product Search | Search Furniture | list furniture items | :white_check_mark: PASS |  |
| 11 | Product Search | Search Clothing | show me clothing | :white_check_mark: PASS |  |
| 12 | Product Search | Search Books | what books are available | :white_check_mark: PASS |  |
| 13 | Product Search | Search with multiple keywords | find me cheap running shoes | :white_check_mark: PASS |  |
| 14 | Product Search | Search zero results | find me unicorn products | :white_check_mark: PASS |  |
| 15 | Product Search | Search by brand/model keyword | show me products with USB-C | :white_check_mark: PASS |  |
| 16 | Product Details | Get product details by ID - valid | tell me about product 1 | :white_check_mark: PASS |  |
| 17 | Product Details | Get product details by ID - another valid | show details for product 50 | :x: FAIL | Expected 'CPU Cooler' not found in output |
| 18 | Product Details | Get product details - invalid ID | tell me about product 99999 | :x: FAIL | Expected 'not found' not found in output |
| 19 | Product Details | Get product details by name | tell me about the yoga mat | :white_check_mark: PASS |  |
| 20 | Product Details | Get product details - out of stock item | tell me about running shoes product 11 | :x: FAIL | Expected 'out of stock' not found in output |
| 21 | Product Details | Get product details - expensive item | tell me about graphics card | :x: FAIL | Guardrail incorrectly triggered for catalog query |
| 22 | Categories | List all categories | what categories do you have | :white_check_mark: PASS |  |
| 23 | Categories | Ask about Electronics category | what's in electronics | :white_check_mark: PASS |  |
| 24 | Categories | Ask about Books category | tell me about the books category | :white_check_mark: PASS |  |
| 25 | Categories | Browse category counts | how many categories are there | :x: FAIL | Guardrail incorrectly triggered for catalog query |
| 26 | Categories | Ask about Home & Kitchen | show me home and kitchen items | :x: FAIL | Expected 'Home & Kitchen' not found in output |
| 27 | Recommendations | Recommend products under budget | recommend me something under $30 | :white_check_mark: PASS |  |
| 28 | Recommendations | Recommend top rated | what are the highest rated products | :white_check_mark: PASS |  |
| 29 | Recommendations | Compare products | compare headphones and earbuds | :white_check_mark: PASS |  |
| 30 | Recommendations | Best seller in Electronics | what's the best product in electronics | :white_check_mark: PASS |  |
| 31 | Recommendations | Suggest gift | suggest a gift under $50 | :white_check_mark: PASS |  |
| 32 | Recommendations | Stock availability check | which products are in stock | :white_check_mark: PASS |  |
| 33 | Edge Cases | Empty-like query - just category | electronics | :white_check_mark: PASS |  |
| 34 | Edge Cases | Single word query - cheap | cheap | :x: FAIL | Guardrail incorrectly triggered for catalog query |
| 35 | Edge Cases | Query with special characters | find me a 27" monitor | :white_check_mark: PASS |  |
| 36 | Edge Cases | Query with numbers | find products costing 49.99 | :white_check_mark: PASS |  |
| 37 | Edge Cases | Very broad query | show me everything | :x: FAIL | Guardrail incorrectly triggered for catalog query |
| 38 | Edge Cases | Multiple requests in one | show me electronics and also tell me about product 5 | :white_check_mark: PASS |  |
| 39 | Guardrail | Reject math question | what is 2+2 | :white_check_mark: PASS |  |
| 40 | Guardrail | Reject coding question | write a python function to sort a list | :white_check_mark: PASS |  |
| 41 | Guardrail | Reject general knowledge | who is the president of the united states | :white_check_mark: PASS |  |
| 42 | Guardrail | Reject unrelated chat | how's the weather today | :white_check_mark: PASS |  |
| 43 | Guardrail | Reject translation request | translate hello to spanish | :white_check_mark: PASS |  |
| 44 | Guardrail | Reject history question | what happened in world war 2 | :white_check_mark: PASS |  |
| 45 | Pricing | Check price of specific product | how much does the mechanical keyboard cost | :white_check_mark: PASS |  |
| 46 | Pricing | Find products within budget | show me products between $50 and $150 | :white_check_mark: PASS |  |
| 47 | Pricing | Find cheapest product | what's the cheapest product you have | :white_check_mark: PASS |  |
| 48 | Pricing | Find most expensive product | what's the most expensive product | :white_check_mark: PASS |  |
| 49 | Pricing | Check stock | is the running shoes in stock | :white_check_mark: PASS |  |
| 50 | Pricing | Filter by price and category | cheap electronics under $30 | :white_check_mark: PASS |  |

## Failed Tests Detail

### #17: Get product details by ID - another valid

- **Category:** Product Details
- **Input:** `show details for product 50`
- **Expected:** `CPU Cooler`
- **Error:** Expected 'CPU Cooler' not found in output
- **Actual Output:** Here are the details for the product:

- **Name:** Arduino Starter Kit
- **Category:** Electronics
- **Price:** $44.99
- **Rating:** 4.5
- **In Stock:** Yes
- **Description:** Includes Uno R3, 15 proj

### #18: Get product details - invalid ID

- **Category:** Product Details
- **Input:** `tell me about product 99999`
- **Expected:** `not found`
- **Error:** Expected 'not found' not found in output
- **Actual Output:** It seems that there is no product with the ID 99999. If you need help finding something specific, feel free to provide a name or category, and I'll assist you in your search!

### #20: Get product details - out of stock item

- **Category:** Product Details
- **Input:** `tell me about running shoes product 11`
- **Expected:** `out of stock`
- **Error:** Expected 'out of stock' not found in output
- **Actual Output:** It looks like product 11 is actually an External SSD, not running shoes. Here are the details:

- **Name:** External SSD 1TB
- **Category:** Electronics
- **Price:** $109.99
- **Rating:** 4.8
- **In S

### #21: Get product details - expensive item

- **Category:** Product Details
- **Input:** `tell me about graphics card`
- **Expected:** `Graphics Card`
- **Error:** Guardrail incorrectly triggered for catalog query
- **Actual Output:** [GUARDRAIL TRIGGERED]

### #25: Browse category counts

- **Category:** Categories
- **Input:** `how many categories are there`
- **Expected:** `9`
- **Error:** Guardrail incorrectly triggered for catalog query
- **Actual Output:** [GUARDRAIL TRIGGERED]

### #26: Ask about Home & Kitchen

- **Category:** Categories
- **Input:** `show me home and kitchen items`
- **Expected:** `Home & Kitchen`
- **Error:** Expected 'Home & Kitchen' not found in output
- **Actual Output:** It seems there are currently no specific home and kitchen items available in our catalog. Would you like to explore other categories or perhaps search for specific items?

### #34: Single word query - cheap

- **Category:** Edge Cases
- **Input:** `cheap`
- **Expected:** `$`
- **Error:** Guardrail incorrectly triggered for catalog query
- **Actual Output:** [GUARDRAIL TRIGGERED]

### #37: Very broad query

- **Category:** Edge Cases
- **Input:** `show me everything`
- **Expected:** `product`
- **Error:** Guardrail incorrectly triggered for catalog query
- **Actual Output:** [GUARDRAIL TRIGGERED]
