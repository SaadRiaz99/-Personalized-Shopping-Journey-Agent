# Deal Agent — Testing Report 5: Loyalty Over-Redemption Bug + Overall Summary

**Module under test:** `Deal_Agent/deal_agent/tools.py` (`apply_discount`) + full Deal Agent suite
**Tester:** Hashir (Deal Agent Specialist)
**Test type:** Unit test (bug) + final regression summary

## Bug: Misleading `loyalty_points_used` field on over-redemption

**Test case:** Called `apply_discount` with `loyalty_points_to_use=999999` for a
user with an actual balance far below that (1000 pts after a prior redemption).

**Expected:** Since the function correctly checks
`account.points_balance >= loyalty_points_to_use` before applying the discount,
no points should be deducted and the response should reflect that 0 points
were actually used.

**Actual output:**
```json
{
  "applied_promotions": [],
  "loyalty_points_used": 999999,
  "total_discount_amount": 0.0,
  "final_price": 1500.0,
  ...
}
```

The discount math is correct (Rs. 0 deducted, balance untouched), but the
`loyalty_points_used` field still echoes back the *requested* amount
(999999) instead of the *actual* amount applied (0). Any caller — including
the orchestrator agent or a frontend — reading this field at face value would
incorrectly believe 999,999 points were redeemed.

**Root cause:** in `apply_discount` (`Deal_Agent/deal_agent/tools.py`), the
`DiscountResult` is built using the raw `loyalty_points_to_use` parameter
rather than a separate `actual_points_used` variable that defaults to 0 when
the balance check fails.

**Recommendation:** Track applied points in a dedicated variable (e.g.
`points_actually_used = 0`, set only inside the `if account and
account.points_balance >= loyalty_points_to_use:` branch) and use that in the
returned `DiscountResult` instead of the input parameter.

**Verdict: FAIL — minor but real data-integrity bug, low effort to fix.**

---

## Overall Summary (Reports 1-5)

| Report | Area | Verdict |
|--------|------|---------|
| 1 | Mock agent — happy path | PASS |
| 2 | Mock agent — edge cases | FUNCTIONAL but not hardened (3 minor bugs) |
| 3 | Mock agent — discount stacking math | **FAIL (critical)** — savings can exceed 100% |
| 4 | Real `agents`-SDK tools — core logic | PASS |
| 5 | Real `agents`-SDK tools — loyalty redemption reporting | FAIL (minor) |

**Total bugs found: 5** (1 critical, 4 minor/cosmetic). No crashes/exceptions
were triggered in any test across both implementations — error handling for
invalid users, bad promo codes, and missing data is solid throughout. The main
risk is in the math/reporting layer of `deal_agent_mock.py`'s unconditional
discount stacking, which should be fixed before this agent is demoed or wired
into the orchestrator end-to-end.

**Tested by:** Hashir (Deal Agent Specialist) | SMIT Batch
