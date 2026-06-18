"""Practical test: does the agent pick the correct best deal?"""
import json, re, time, random, urllib.request
from decimal import Decimal, ROUND_HALF_UP
from deal_agent import LOYALTY_DB

API = "http://localhost:8003/api/chat"
random.seed(42)

PRICES = {"Running Shoes":89.99,"Yoga Mat":24.99,"Water Bottle":14.99,"Gym Bag":39.99,"Protein Powder":44.99,"Resistance Bands":19.99,"Foam Roller":29.99,"Wireless Earbuds":59.99}
ITEMS = list(PRICES.keys())
TR = {"bronze":0,"silver":1,"gold":2,"platinum":3}
CD = [
    {"code":"WELCOME10","type":"percent_off","value":10,"min_spend":20,"min_tier":"bronze"},
    {"code":"LOYAL20","type":"percent_off","value":20,"min_spend":50,"min_tier":"gold"},
    {"code":"SAVE5","type":"flat_off","value":5,"min_spend":30,"min_tier":"bronze"},
    {"code":"PLAT50","type":"percent_off","value":25,"min_spend":100,"min_tier":"platinum"},
]
BD = [
    {"name":"Starter Fitness","items":["Yoga Mat","Water Bottle","Resistance Bands"],"discount":10},
    {"name":"Runner's Pack","items":["Running Shoes","Protein Powder","Wireless Earbuds"],"discount":15},
    {"name":"Recovery Kit","items":["Resistance Bands","Foam Roller","Water Bottle"],"discount":12},
]
UT = {uid: info["tier"] for uid, info in LOYALTY_DB.items()}
UIDS = list(UT.keys())

def rd(v):
    return float(Decimal(str(v)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))

def expected_best(subtotal, tier, items):
    """Return (expected_best_label, expected_best_savings)"""
    best_label, best_sav = None, -1
    for c in CD:
        if TR.get(tier,0) < TR.get(c.get("min_tier","bronze"),0): continue
        if subtotal < c["min_spend"]: continue
        sav = rd(subtotal * c["value"] / 100) if c["type"]=="percent_off" else rd(min(c["value"], subtotal))
        if sav > best_sav:
            best_sav = sav
            best_label = c["code"]
    cs = set(items)
    for b in BD:
        if cs & set(b["items"]):
            sav = rd(subtotal * b["discount"] / 100)
            if sav > best_sav:
                best_sav = sav
                best_label = b["name"]
    return best_label, best_sav

_DEAL_NAMES = ["Runner's Pack", "Starter Fitness", "Recovery Kit", "PLAT50", "LOYAL20", "WELCOME10", "SAVE5"]
def extract_best_deal(text):
    """Find the best deal name from model output. Best deal is always mentioned first."""
    t = text.lower()
    # Strategy 1: return the FIRST deal name appearing in the response
    first_name, first_pos = None, 9999
    for name in _DEAL_NAMES:
        nl = name.lower()
        pos = t.find(nl)
        if pos != -1 and pos < first_pos:
            first_pos = pos
            first_name = name
    return first_name

seq = 0
def run_test(msg, expected_label):
    global seq; seq += 1
    p = json.dumps({"message": msg, "session_id": "s%d" % seq}).encode()
    req = urllib.request.Request(API, data=p, headers={"Content-Type":"application/json"}, method="POST")
    with urllib.request.urlopen(req, timeout=120) as r:
        resp = json.loads(r.read())
    text = resp.get("response", "")
    chosen = extract_best_deal(text)
    ok = chosen and expected_label and chosen.lower() == expected_label.lower()
    return ok, chosen, text

# Manual diverse tests first
manual = []
for msg, items, uid in [
    ("I have Running Shoes in my cart. Find me the best deals.", ["Running Shoes"], None),
    ("I have Yoga Mat and Water Bottle in my cart. Find me the best deals.", ["Yoga Mat", "Water Bottle"], None),
    ("user_001, I have Running Shoes and Yoga Mat in my cart. Find me the best deals.", ["Running Shoes", "Yoga Mat"], "user_001"),
    ("user_002, I have Protein Powder and Wireless Earbuds in my cart. Find me the best deals.", ["Protein Powder", "Wireless Earbuds"], "user_002"),
    ("user_003, I have Gym Bag and Foam Roller in my cart. Find me the best deals.", ["Gym Bag", "Foam Roller"], "user_003"),
    ("user_004, I have Water Bottle and Resistance Bands in my cart. Find me the best deals.", ["Water Bottle", "Resistance Bands"], "user_004"),
    ("user_001, I have Water Bottle in my cart. Find me the best deals.", ["Water Bottle"], "user_001"),
    ("I have Resistance Bands, Foam Roller, and Water Bottle in my cart. Find me the best deals.", ["Resistance Bands", "Foam Roller", "Water Bottle"], None),
    ("user_050, I have Yoga Mat, Water Bottle, and Resistance Bands in my cart. Find me the best deals.", ["Yoga Mat", "Water Bottle", "Resistance Bands"], "user_050"),
    ("user_450, I have Running Shoes, Protein Powder, and Wireless Earbuds in my cart. Find me the best deals.", ["Running Shoes", "Protein Powder", "Wireless Earbuds"], "user_450"),
]:
    st = rd(sum(PRICES[it] for it in items))
    tier = UT.get(uid, "bronze") if uid else "bronze"
    exp, _ = expected_best(st, tier, items)
    manual.append((msg, exp))

print("=== MANUAL TESTS ===")
mp = mf = 0
for msg, exp in manual:
    ok, chosen, resp_text = run_test(msg, exp)
    if ok: mp += 1
    else: mf += 1
    status = "PASS" if ok else "FAIL"
    if ok:
        print("  %s: expected=%s chosen=%s | msg=%.50s" % (status, exp, chosen, msg))
    else:
        print("  %s: expected=%s chosen=%s | msg=%.50s" % (status, exp, chosen, msg))
        print("    RESP: %.200s" % resp_text)

print("\n=== RANDOM SCENARIOS ===")
print("Generating 15 random tests...")
scenarios = []
for i in range(15):
    nitems = random.randint(1, 5)
    items = random.sample(ITEMS, min(nitems, len(ITEMS)))
    st = rd(sum(PRICES[it] for it in items))
    use_user = random.random() < 0.6
    if use_user:
        uid = random.choice(UIDS)
        tier = UT[uid]
        msg = "%s, I have %s in my cart. Find me the best deals." % (uid, ", ".join(items))
    else:
        uid, tier = None, "bronze"
        msg = "I have %s in my cart. Find me the best deals." % ", ".join(items)
    exp_label, _ = expected_best(st, tier, items)
    if exp_label:
        scenarios.append((msg, exp_label))

print("Running %d tests..." % len(scenarios))
passed = failed = 0
start = time.time()
for idx, (msg, exp) in enumerate(scenarios):
    ok, chosen, resp_text = run_test(msg, exp)
    if ok: passed += 1
    else:
        failed += 1
        print("  FAIL #%d: exp=%s chosen=%s | msg=%.50s" % (idx+1, exp, chosen, msg))
        print("    RESP: %.200s" % resp_text)
    if (idx+1) % 20 == 0:
        el = time.time() - start
        print("  [%d/%d] pass=%d fail=%d rate=%.1f/s" % (idx+1, len(scenarios), passed, failed, (idx+1)/el))

elapsed = time.time() - start
total = mp + passed
tfail = mf + failed
print()
print("="*60)
print("FINAL RESULTS")
print("Total: %d" % (total + tfail))
print("Pass: %d" % total)
print("Fail: %d" % tfail)
print("Accuracy: %.1f%%" % (total * 100.0 / max(total + tfail, 1)))
print("Time: %.1f min" % (elapsed/60))
print("="*60)

with open("test_results.json", "w") as f:
    json.dump({"passed": total, "failed": tfail, "total": total+tfail, "accuracy_pct": round(total*100.0/max(total+tfail,1),1)}, f)
print("Saved to test_results.json")
