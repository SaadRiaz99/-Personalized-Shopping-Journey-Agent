"""30 strict tests for the Deal Agent."""
import json, urllib.request

API = "http://localhost:8003/api/chat"

seq = 0
def test(msg, checks, sid=None):
    global seq; seq += 1
    s = sid or "s%d" % seq
    p = json.dumps({"message": msg, "session_id": s}).encode()
    req = urllib.request.Request(API, data=p, headers={"Content-Type":"application/json"}, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            resp = json.loads(r.read())
    except Exception as e:
        return False, str(e)
    text = resp.get("response", "")
    for check in checks:
        if check.lower() not in text.lower():
            return False, 'Missing "%s" in: %.200s' % (check, text)
    return True, text[:200]

tests = [
    # 1-3: Guest best deals
    ("I have Running Shoes and Yoga Mat", ["Runner's Pack", "17.25"]),
    ("I have Yoga Mat Water Bottle Resistance Bands", ["Recovery Kit", "7.20"]),
    ("I have Resistance Bands Foam Roller Water Bottle", ["Recovery Kit", "7.80"]),
    # 4-6: User IDs + name greeting
    ("user_001 Running Shoes Protein Powder Wireless Earbuds", ["Alice", "PLAT50"]),
    ("user_050 Yoga Mat Water Bottle Resistance Bands", ["Zara", "Recovery Kit"]),
    ("user_450 Running Shoes", ["Zion", "Runner's Pack"]),
    # 7-9: Name-only requires user ID
    ("my name is Alice what tier", ["provide your user ID"]),
    ("my name is Zara am I platinum", ["provide your user ID"]),
    ("my name is Zion what is my tier", ["provide your user ID"]),
    # 10-12: Valid user ID loyalty queries
    ("user_002 what tier", ["Bob", "Platinum"]),
    ("user_003 check my points", ["Charlie"]),
    ("user_004 what is my loyalty", ["Diana"]),
    # 13-14: Off-topic refusal
    ("write me a poem", ["deal agent"]),
    ("what is the weather today", ["deal agent"]),
    # 15-16: Empty cart
    ("user_005 any deals for me", ["cart is empty"]),
    ("any deals for me", ["cart is empty"]),
    # 17-18: Image handling
    ("image.png", ["only process text"]),
    ("my photo.jpg", ["only process text"]),
    # 19-20: Invalid user ID
    ("user_999 Running Shoes", ["valid"]),
    ("user_000 Yoga Mat", ["valid"]),
    # 21-23: Follow-up memory (same session)
    ("user_001 what deals for Running Shoes", ["Alice"], "follow1"),
    ("what about with a discount", ["Alice", "LOYAL20"], "follow1"),
    ("what was in my cart", ["Running Shoes"], "follow1"),
    # 24-25: Deal listing
    ("what deals are available", ["Summer Sale", "WELCOME10"]),
    ("show me promotions", ["Summer Sale", "BOGO"]),
    # 26: Guest single item
    ("I have Running Shoes and Yoga Mat get deals", ["Runner's Pack"]),
    # 27: User asking about cart items (was false-positive off-topic)
    ("user_003 what are my cart items", ["cart is empty"]),
    # 28-31: Edge cases
    ("how old are you", ["deal agent"]),
    ("help me", ["help"]),
    ("what can you do for me", ["help you save money"]),
    ("user_001 what are my loyalty benefits", ["Alice", "Platinum"]),
]

passed = failed = 0
for i, (msg, checks, *sid) in enumerate(tests, 1):
    ok, detail = test(msg, checks, sid[0] if sid else None)
    if ok:
        passed += 1
        status = "PASS"
    else:
        failed += 1
        status = "FAIL"
    print("  %s #%2d: %-55s | %.120s" % (status, i, msg[:55], detail))

total = passed + failed
print("\n%s" % ("="*60))
print("RESULTS: %d/%d passed, %d failed" % (passed, total, failed))
print("Accuracy: %d%%" % (passed*100//total))
