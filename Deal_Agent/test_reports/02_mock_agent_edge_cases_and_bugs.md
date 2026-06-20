# Deal Agent — Testing Report 2: Mock Conversational Agent (Edge Cases & Bugs Found)

**Module under test:** `Deal_Agent/deal_agent_mock.py`
**Tester:** Hashir (Deal Agent Specialist)
**Test type:** Edge case / negative testing

## Scope

Fed invalid/unusual inputs (unknown user, zero/negative cart totals, unknown
category, free-text input including Roman-Urdu phrases) to `handle_input` to check
for crashes and logical correctness.

## Test Cases & Results

| # | Input | Category | Cart Total | User | Outcome |
|---|-------|----------|------------|------|---------|
| 1 | `apply best deal` | electronics | 1200 | U999 (invalid) | No crash, gracefully skips loyalty section. PASS |
| 2 | `apply best deal` | toys (unmapped) | 0 | U001 | No crash, but discounts of "Rs. 0" listed as "applied" — noisy output. **Minor bug** |
| 3 | `apply best deal` | electronics | -500 (negative) | U001 | No crash, but negative cart total is accepted silently and still "saves" Rs. 6 via loyalty. **Bug** |
| 4 | `kitna bachega` (Urdu) | unknown_category | 1500 | U001 | Falls back to "all"-category promos only, no warning shown to user. **Minor bug** |
| 5 | `random gibberish xyz` | electronics | 1500 | U001 | Correctly falls through to help-menu response. PASS |
| 6 | `` (empty string) | electronics | 1500 | U001 | Correctly falls through to help-menu response. PASS |

## Bugs Found

1. **No input validation on `cart_total`.** Negative and zero values are accepted
   without rejection or warning, producing nonsensical output such as
   `Original Price : Rs. -500` followed by a "savings" line.
2. **Unknown/unmapped category fails silently.** Typing a category that doesn't
   exist in `promotions.json` (e.g. `toys`, `unknown_category`) returns only
   the generic "all" promos with no message telling the user their category
   wasn't recognized — looks like a smaller result set rather than an error.
3. **Zero-value discount lines clutter output.** When `cart_total` is 0, the
   agent still lists promos as "applied" with `-Rs. 0`, which is misleading
   noise rather than a clean "no applicable discounts" message.

## Recommendation

Add a guard at the top of `handle_input`/`apply_best_discount` to reject
`cart_total <= 0` with a clear message, and validate `category` against the
known set in `promotions.json` before searching.

**Verdict: FUNCTIONAL but NOT HARDENED — fails gracefully (no crashes) but lacks input validation.**
