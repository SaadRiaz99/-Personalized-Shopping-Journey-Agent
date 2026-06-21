import sys, pathlib, json, random
sys.path.insert(0, str(pathlib.Path.cwd()))

FILE = "data/products.json"

# Sample first 20 items using ijson
import ijson

count = 0
samples = []
seen_categories = set()
seen_brands = set()
keys = set()
has_brand = False
min_price = float('inf')
max_price = float('-inf')
missing_price = 0
total = 0

with open(FILE, "rb") as f:
    parser = ijson.parse(f)
    for prefix, event, value in parser:
        if prefix == "item" and event == "start_map":
            item = {}
        elif prefix.startswith("item."):
            key = prefix.split(".", 1)[1]
            keys.add(key)
            if event == "number":
                item[key] = value
            elif event == "string":
                item[key] = value
            elif event == "boolean":
                item[key] = value
        elif prefix == "item" and event == "end_map":
            total += 1
            if count < 20:
                samples.append(dict(item))
                count += 1
            if "category" in item:
                seen_categories.add(item["category"])
            if "brand" in item and item.get("brand"):
                has_brand = True
                seen_brands.add(item["brand"])
            if "price" in item and isinstance(item["price"], (int, float)):
                p = item["price"]
                if p < min_price: min_price = p
                if p > max_price: max_price = p
            else:
                missing_price += 1
            if total >= 5000:
                break

print(f"Fields in data: {sorted(keys)}")
print(f"Total products scanned: {total}")
print(f"Has 'brand' field: {has_brand}")
print(f"Missing price: {missing_price}")
print(f"Price range: {min_price} - {max_price}")
print(f"Categories: {sorted(seen_categories)}")
print(f"Brand samples (first 20): {sorted(list(seen_brands))[:20]}")
print()
print("=== FIRST 20 PRODUCTS ===")
for s in samples:
    print(json.dumps(s, indent=2))
    print()
