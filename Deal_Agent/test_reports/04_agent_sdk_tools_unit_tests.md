# Deal Agent — Testing Report 4: Agents-SDK Tool Functions (Unit Tests)

**Module under test:** `Deal_Agent/deal_agent/tools.py`
**Tester:** Hashir (Deal Agent Specialist)
**Test type:** Unit testing (tool-level, bypassing the LLM)

## Scope

The production agent (`Deal_Agent/deal_agent/agent.py`) wraps four
`@function_tool`-decorated functions from `tools.py`:
`get_active_promotions`, `get_loyalty_points`, `get_bundle_offers`, `apply_discount`.
Since these require an OpenAI-compatible API key to run through the full agent,
each tool was invoked directly via `on_invoke_tool()` with a constructed
`ToolContext`, bypassing the LLM layer to test tool logic in isolation.

## Test Cases & Results

| # | Tool | Input | Result | Verdict |
|---|------|-------|--------|---------|
| 1 | `get_active_promotions` | electronics, Rs. 1500 | 3 matching promos (SAVE10, FLAT200, BUNDLE15) returned correctly | PASS |
| 2 | `get_loyalty_points` | user_id=U001 (valid) | 1500 pts, silver tier, Rs. 750 value — correct | PASS |
| 3 | `get_loyalty_points` | user_id=U999 (invalid) | Gracefully returns 0 pts / bronze default, no exception | PASS |
| 4 | `get_bundle_offers` | [PROD_PHONE, PROD_EARBUDS] | Correctly matches "Phone + Earbuds Bundle" (18% off) | PASS |
| 5 | `get_bundle_offers` | [PROD_RANDOM] | Correctly returns empty bundle list | PASS |
| 6 | `apply_discount` | Rs. 1500, codes=[SAVE10, FLAT200], 500 pts | Rs. 600 total discount, final Rs. 900, 40% off — math checks out | PASS |
| 7 | `apply_discount` | promo_codes=["NONEXISTENT"] | Unknown code silently ignored, no crash, no discount applied | PASS (defensive) |
| 8 | `apply_discount` | original_price=-200, code=SAVE10 | Negative price rejected by `min_order_value` check, final clamped to 0, no crash | PASS (defensive) |

## Manual Verification of Test 6 Math

```
Original: Rs. 1500
SAVE10 (10%):      -Rs. 150.00  -> Rs. 1350.00
FLAT200 (fixed):   -Rs. 200.00  -> Rs. 1150.00
500 loyalty pts @ Rs.0.5/pt: -Rs. 250.00 -> Rs. 900.00
Total discount: Rs. 600.00 (40.0%) -- matches reported output exactly.
```

## Conclusion

Unlike the mock conversational agent (see Report 3), `tools.py`'s
`apply_discount` only stacks the *specific* promo codes passed in by the
caller rather than blindly stacking every stackable promo — so it does not
exhibit the >100%-savings bug. Bad promo codes and negative prices are handled
defensively without exceptions.

One related issue (loyalty point over-redemption reporting) was found and is
detailed separately in Report 5.

**Verdict: PASS — core tool logic is sound and correctly bounded.**
