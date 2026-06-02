import json, yaml

with open("cassettes/test_agent/agent_catalog_pass.yaml") as f:
    data = yaml.safe_load(f)

total = len(data["interactions"])
print(f"Total interactions: {total}")

# Check request bodies to determine guardrail vs main agent
for i in range(min(total, 6)):
    req = data["interactions"][i]["request"]
    body_str = req["body"]
    obj = json.loads(body_str)
    msgs = obj.get("messages", [])
    roles = [m.get("role", "") for m in msgs]
    content0 = ""
    for m in msgs:
        if m.get("role") == "user":
            content0 = m.get("content", "")[:60]
            break
    model = obj.get("model", "")
    print(f"Int {i}: model={model} roles={roles} user={content0!r}")
