# Deal Agent — Testing Report 1: Mock Conversational Agent (Functional)

**Module under test:** `Deal_Agent/deal_agent_mock.py`
**Tester:** Hashir (Deal Agent Specialist)
**Test type:** Functional / happy-path

## Scope

Exercised the no-API-key conversational agent (`search_promotions`, `get_loyalty`,
`apply_best_discount`) directly against `promotions.json` (20 promotions, 20 users)
to confirm normal cart/discount flows behave correctly.

## Test Cases & Results

| # | User | Category | Cart Total (Rs.) | Promos Matched | Loyalty Found | Result |
|---|------|------------|------------------|-----------------|---------------|--------|
| 1 | U001 | electronics | 1500 | 10 | Yes (25 pts, bronze) | PASS — discounts applied, final price returned |
| 2 | U002 | fashion | 2500 | 12 | Yes (7006 pts, gold) | PASS — discounts applied, final price returned |
| 3 | U010 | books | 300 | 5 | Yes (3932 pts) | PASS — category-specific promo (BOOK15) correctly matched |
| 4 | U020 | home | 8000 | 14 | Yes (367 pts) | PASS — high-value cart unlocks tiered promos (SAVE30, FLAT500) |

## Sample Output (Test 1 — U001, electronics, Rs. 1500)

```
Original Price : Rs. 1500
(-) SAVE20: 20% off on orders above Rs. 1500 = -Rs. 300
(-) SAVE5: 5% off on all orders = -Rs. 60
(-) SAVE10: 10% off on orders above Rs. 500 = -Rs. 114
(-) FLAT100: Rs. 100 off on orders above Rs. 500 = -Rs. 100
(-) BUNDLE10/15/20 stacked = -Rs. 360 combined
(-) Loyalty (25 pts) = -Rs. 6
Final Price    : Rs. 560.46
Total Saved    : Rs. 939.54 (62.6% off)
```

## Conclusion

Core happy-path flow works as designed: category matching, minimum-order gating,
and loyalty lookup all function correctly for valid users and positive cart totals.
Deeper stacking/math concerns are covered separately in Report 2 (edge cases).

**Verdict: PASS for standard usage.**
