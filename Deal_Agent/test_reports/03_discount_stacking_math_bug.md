# Deal Agent — Testing Report 3: Discount-Stacking Math Bug (Critical)

**Module under test:** `Deal_Agent/deal_agent_mock.py` → `apply_best_discount()`
**Tester:** Hashir (Deal Agent Specialist)
**Test type:** Calculation correctness / regression

## Scope

`apply_best_discount` (1) picks the single best non-stackable promo, then
(2) applies **every** stackable promo on top, then (3) redeems **all** of the
user's loyalty points — with no cap. This report checks whether the reported
`saved` / `saved_pct` figures stay consistent with the actual final price.

## Test Cases & Results

| # | User | Category | Cart Total | Final Price | Reported Saved | Reported Saved % |
|---|------|----------|------------|--------------|-----------------|-------------------|
| 1 | U001 | electronics | Rs. 1500 | Rs. 560.46 | Rs. 939.54 | 62.6% |
| 2 | U002 | fashion | Rs. 2500 | **Rs. 0** | Rs. 6956.99 | **278.3%** |
| 3 | U010 | books | Rs. 300 | **Rs. 0** | Rs. 2117.74 | **705.9%** |
| 4 | U020 | home | Rs. 8000 | Rs. 2348.91 | Rs. 5651.09 | 70.6% |

## Bug

For test cases 2 and 3, the final price correctly clamps at Rs. 0 (price cannot
go negative), but `total_saved` keeps accumulating discount amounts computed
*before* clamping — and loyalty points get redeemed in full regardless of how
much of the cart they can actually offset. The result is a "Total Saved" figure
that is mathematically impossible (you cannot save 705.9% of a Rs. 300 cart).

Root cause: `apply_best_discount()` in `deal_agent_mock.py` (lines ~30-76) only
clamps the *final price* (`max(price, 0)`), not the *applied discount amounts*
that feed into `total_saved`. Each discount in the loop is computed against the
running `price` before checking whether `price` has already hit zero.

```python
price -= amt
total_saved += amt   # <-- keeps growing even after price would go negative
...
return {
    "final": round(max(price, 0), 2),   # price is clamped here...
    "saved": round(total_saved, 2),     # ...but saved is NOT clamped to original cart_total
}
```

## Impact

Any cart that is small relative to the user's loyalty balance, or that qualifies
for many stackable promos at once, will display an absurd "% off" figure
(seen up to 705.9% in testing). This is customer-facing copy
(`Total Saved : Rs. X (Y% off)`) and would look broken/untrustworthy in a demo
or production setting.

## Recommendation

Clamp `total_saved` to `min(total_saved, cart_total)` before computing
`saved_pct`, and stop applying further discounts/loyalty redemption once
`price` reaches 0 rather than continuing to subtract.

**Verdict: FAIL — critical calculation bug, recommend fix before demo/integration.**
