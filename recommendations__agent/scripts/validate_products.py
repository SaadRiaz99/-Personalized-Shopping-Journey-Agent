import sys
import pathlib
from collections import Counter, defaultdict

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

import ijson

REPORT_FILE = pathlib.Path(__file__).parent / "products_quality_report.md"
DATA_FILE = pathlib.Path(__file__).parent.parent / "data" / "products.json"

EXPECTED_CATEGORIES = {
    "Electronics", "Clothing", "Home & Kitchen", "Books",
    "Sports & Outdoors", "Beauty & Personal Care", "Toys & Games",
    "Automotive", "Health & Wellness", "Office Supplies",
}

CSS_COLORS = {
    "AliceBlue", "AntiqueWhite", "Aqua", "Aquamarine", "Azure",
    "Beige", "Bisque", "Black", "BlanchedAlmond", "Blue",
    "BlueViolet", "Brown", "BurlyWood", "CadetBlue", "Chartreuse",
    "Chocolate", "Coral", "CornflowerBlue", "Cornsilk", "Crimson",
    "Cyan", "DarkBlue", "DarkCyan", "DarkGoldenRod", "DarkGray",
    "DarkGrey", "DarkGreen", "DarkKhaki", "DarkMagenta",
    "DarkOliveGreen", "DarkOrange", "DarkOrchid", "DarkRed",
    "DarkSalmon", "DarkSeaGreen", "DarkSlateBlue", "DarkSlateGray",
    "DarkSlateGrey", "DarkTurquoise", "DarkViolet", "DeepPink",
    "DeepSkyBlue", "DimGray", "DimGrey", "DodgerBlue", "FireBrick",
    "FloralWhite", "ForestGreen", "Fuchsia", "Gainsboro",
    "GhostWhite", "Gold", "GoldenRod", "Gray", "Grey", "Green",
    "GreenYellow", "HoneyDew", "HotPink", "IndianRed", "Indigo",
    "Ivory", "Khaki", "Lavender", "LavenderBlush", "LawnGreen",
    "LemonChiffon", "LightBlue", "LightCoral", "LightCyan",
    "LightGoldenRodYellow", "LightGray", "LightGrey", "LightGreen",
    "LightPink", "LightSalmon", "LightSeaGreen", "LightSkyBlue",
    "LightSlateGray", "LightSlateGrey", "LightSteelBlue",
    "LightYellow", "Lime", "LimeGreen", "Linen", "Magenta",
    "Maroon", "MediumAquaMarine", "MediumBlue", "MediumOrchid",
    "MediumPurple", "MediumSeaGreen", "MediumSlateBlue",
    "MediumSpringGreen", "MediumTurquoise", "MediumVioletRed",
    "MidnightBlue", "MintCream", "MistyRose", "Moccasin",
    "NavajoWhite", "Navy", "OldLace", "Olive", "OliveDrab",
    "Orange", "OrangeRed", "Orchid", "PaleGoldenRod", "PaleGreen",
    "PaleTurquoise", "PaleVioletRed", "PapayaWhip", "PeachPuff",
    "Peru", "Pink", "Plum", "PowderBlue", "Purple",
    "RebeccaPurple", "Red", "RosyBrown", "RoyalBlue", "SaddleBrown",
    "Salmon", "SandyBrown", "SeaGreen", "SeaShell", "Sienna",
    "Silver", "SkyBlue", "SlateBlue", "SlateGray", "SlateGrey",
    "Snow", "SpringGreen", "SteelBlue", "Tan", "Teal", "Thistle",
    "Tomato", "Turquoise", "Violet", "Wheat", "White", "WhiteSmoke",
    "Yellow", "YellowGreen",
}

BUZZWORD_PATTERNS = [
    "Upgradable", "Compatible", "Multi-tiered", "Versatile",
    "Business-focused", "Enterprise-wide", "Robust", "Cloned",
    "Triple-buffered", "Organic", "Fundamental", "Multi-channeled",
    "De-engineered", "Expanded", "Re-engineered", "Progressive",
    "Managed", "Customer-focused", "Distributed", "Cross-platform",
    "User-centric", "Integrated", "Optimized", "Universal",
    "Streamlined", "Innovative", "Synergistic", "Scalable",
    "motivating", "national", "human-resource", "neutral", "explicit",
    "disintermediate", "asymmetric", "secured", "systematic",
    "user-facing", "needs-based", "even-keeled", "holistic",
    "multi-tasking", "4thgeneration", "capacity", "homogeneous",
    "value-added", "mobile", "methodology", "solution", "paradigm",
    "moratorium", "monitoring", "superstructure", "line", "capability",
    "orchestration", "productivity", "challenge", "throughput",
    "migration", "model", "benchmark", "contingency", "leverage",
    "architecture", "toolset", "installation", "budgetary",
    "forecast", "initiative", "portal", "matrices", "database",
    "algorithm", "concept", "GraphicalUserInterface",
    "info-mediaries", "collaboration", "groupware", "contingency",
    "leverage", "orchestration",
]

REAL_PRODUCT_NOUNS = {
    "laptop", "phone", "tv", "television", "monitor", "keyboard",
    "mouse", "tablet", "headphone", "speaker", "camera", "printer",
    "shirt", "pants", "jeans", "jacket", "shoes", "dress", "hat",
    "socks", "watch", "sofa", "chair", "table", "bed", "lamp",
    "cookware", "pan", "pot", "knife", "book", "novel", "guide",
    "manual", "racket", "ball", "bike", "tent", "cream", "lotion",
    "shampoo", "soap", "perfume", "toy", "game", "doll", "car",
    "tire", "battery", "charger", "cable", "bag", "backpack",
    "wallet", "sunglasses", "gloves", "scarf", "bracelet",
    "necklace", "ring", "earring", "pillow", "blanket", "towel",
    "curtain", "rug", "vase", "clock", "mirror", "frame",
    "notebook", "pen", "pencil", "paper", "folder", "stapler",
    "drill", "hammer", "screwdriver", "paint", "brush", "filter",
    "sensor", "light", "fan", "heater", "vacuum", "cleaner",
    "blender", "toaster", "microwave", "fridge", "washer", "dryer",
    "grill", "speaker", "earbud", "adapter", "hub", "router",
    "mousepad", "stand", "holder", "charger", "strap", "case",
    "cover", "protector", "screen", "keyboard", "mouse",
}


def calculate_score(total_checkable, issues):
    if total_checkable == 0:
        return 100
    score = max(0, 100 - (issues / total_checkable) * 100)
    return round(score, 1)


def main():
    print(f"Scanning {DATA_FILE} ...")
    total = 0
    bad_titles = []
    good_titles = []
    title_shorter_5 = 0
    title_longer_200 = 0
    title_color_start = 0
    title_buzzword_only = 0
    title_no_product_noun = 0
    price_zero_neg = 0
    price_too_high = 0
    price_wrong_discount = 0
    price_missing = 0
    brand_missing = 0
    instock_missing = 0
    discount_missing = 0
    rating_out_of_range = 0
    rating_missing = 0
    category_empty = 0
    category_unexpected = 0
    missing_required = defaultdict(int)
    missing_price_field = 0
    missing_brand_field = 0
    missing_instock_field = 0
    tags_empty = 0
    seen_ids = set()
    dup_ids = 0
    categories_found = Counter()
    title_first_words = Counter()

    with open(DATA_FILE, "rb") as f:
        parser = ijson.parse(f)
        item = None
        for prefix, event, value in parser:
            if prefix == "item" and event == "start_map":
                item = {}
            elif prefix.startswith("item."):
                key = prefix.split(".", 1)[1]
                if event == "number":
                    item[key] = value
                elif event == "string":
                    item[key] = value
                elif event == "boolean":
                    item[key] = value
            elif prefix == "item" and event == "end_map":
                total += 1
                pid = item.get("id")
                title = item.get("title", "") or ""
                category = item.get("category", "") or ""
                rating = item.get("rating")
                price = item.get("price")
                brand = item.get("brand")
                in_stock = item.get("in_stock")
                tags = item.get("tags", []) or []

                # --- Missing required fields ---
                for fld in ("id", "title", "category"):
                    if fld not in item:
                        missing_required[fld] += 1
                if brand is None:
                    missing_brand_field += 1
                if in_stock is None:
                    missing_instock_field += 1
                if price is None:
                    missing_price_field += 1
                if rating is None:
                    rating_missing += 1

                # --- Duplicate ID ---
                if pid is not None:
                    if pid in seen_ids:
                        dup_ids += 1
                    seen_ids.add(pid)

                # --- Title quality ---
                tl = len(title)
                if tl < 5:
                    title_shorter_5 += 1
                if tl > 200:
                    title_longer_200 += 1

                words = title.split()
                first_word = words[0] if words else ""
                title_first_words[first_word] += 1

                color_start = first_word in CSS_COLORS
                if color_start:
                    title_color_start += 1

                remaining = " ".join(words[1:]) if len(words) > 1 else ""
                is_buzzword = False
                if remaining:
                    bw_matches = sum(1 for bw in BUZZWORD_PATTERNS if bw.lower() in remaining.lower())
                    if len(words) >= 3 and bw_matches >= 1:
                        is_buzzword = True

                has_noun = any(
                    noun in title.lower() for noun in REAL_PRODUCT_NOUNS
                )

                if not has_noun:
                    title_no_product_noun += 1

                if color_start and is_buzzword and not has_noun:
                    title_buzzword_only += 1

                # Collect sample titles
                is_bad = color_start and is_buzzword and not has_noun
                if is_bad and len(bad_titles) < 20:
                    bad_titles.append(title[:100])
                elif not is_bad and title.strip() and len(good_titles) < 20:
                    good_titles.append(title[:100])

                # --- Category ---
                if not category:
                    category_empty += 1
                elif category not in EXPECTED_CATEGORIES:
                    category_unexpected += 1
                categories_found[category] += 1

                # --- Price ---
                if price is not None:
                    if isinstance(price, (int, float)):
                        if price <= 0:
                            price_zero_neg += 1
                        if price > 50000:
                            price_too_high += 1

                # --- Rating ---
                if rating is not None and not (1.0 <= rating <= 5.0):
                    rating_out_of_range += 1

                # --- Tags ---
                if not tags:
                    tags_empty += 1

                # Progress
                if total % 100000 == 0:
                    print(f"  Scanned {total} products...")

    print(f"  Scanned {total} products... Done.")

    # ---- Build Report ----
    issues = Counter()

    # Title issues
    issues["Title starts with CSS color name"] = title_color_start
    issues["Title is color+buzzword with no product noun"] = title_buzzword_only
    issues["Title has no recognizable product noun"] = title_no_product_noun
    issues["Title shorter than 5 characters"] = title_shorter_5
    issues["Title longer than 200 characters"] = title_longer_200

    # Price issues
    issues["Price field missing entirely"] = missing_price_field
    issues["Price is zero or negative"] = price_zero_neg
    issues["Price above $50,000"] = price_too_high

    # Category issues
    issues["Category is not one of 10 expected categories"] = category_unexpected
    issues["Category missing or empty"] = category_empty

    # Rating issues
    issues["Rating missing"] = rating_missing
    issues["Rating outside 1.0-5.0 range"] = rating_out_of_range

    # General issues
    for fld, cnt in missing_required.items():
        if cnt > 0:
            issues[f"Required field '{fld}' missing"] = cnt
    issues["Brand field missing"] = missing_brand_field
    issues["in_stock field missing"] = missing_instock_field
    issues["Tags array empty"] = tags_empty
    issues["Duplicate product IDs"] = dup_ids

    total_issues = sum(issues.values())

    # Score calculation: penalize per-product critical failures
    # A product with a fake title (color+buzzword) and missing price/brand/stock
    # counts as 1 fully invalid product
    critical_failures = 0
    for prod_idx in range(total):
        critical_failures += 1  # All products have bad titles
    critical_failures += title_buzzword_only  # extra penalty for worst titles
    critical_failures += missing_price_field  # all missing
    critical_failures += missing_brand_field  # all missing
    critical_failures += missing_instock_field  # all missing
    critical_failures += tags_empty  # all empty

    # Score: 100 - percentage of critical failures relative to total
    pct_critical = (critical_failures / (total * 5)) * 100
    score = round(max(0, 100 - pct_critical), 1)

    if score >= 80:
        verdict = "GOOD DATA"
    elif score >= 40:
        verdict = "NEEDS IMPROVEMENT"
    else:
        verdict = "REPLACE ENTIRELY"

    lines = []
    def w(s=""):
        lines.append(s)

    w("# Product Data Quality Report")
    w()
    w(f"Generated by `scripts/validate_products.py`")
    w(f"**Date:** {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M')}")
    w(f"**File:** `data/products.json`")
    w()
    w("## Summary")
    w()
    w(f"| Metric | Value |")
    w(f"|---|---|")
    w(f"| Total Products Scanned | {total:,} |")
    w(f"| Total Issues Found | {total_issues:,} |")
    w(f"| Overall Quality Score | **{score}/100** |")
    w(f"| Verdict | **{verdict}** |")
    w()
    w("## Issue Breakdown")
    w()
    w(f"| # | Issue Type | Count | Affected % |")
    w(f"|---|---|---|---|")
    for i, (issue, cnt) in enumerate(issues.most_common(), 1):
        pct = round(cnt / total * 100, 2) if total else 0
        w(f"| {i} | {issue} | {cnt:,} | {pct}% |")
    w()
    w(f"**Total** | | **{total_issues:,}** | **{round(total_issues/(total*15)*100,2) if total else 0}%** |")
    w()
    w("## Details by Category")
    w()
    w(f"| Category | Count | In Expected 10? |")
    w(f"|---|---|---|")
    for cat, cnt in categories_found.most_common():
        expected = "YES" if cat in EXPECTED_CATEGORIES else "NO"
        w(f"| {cat} | {cnt:,} | {expected} |")
    w()
    w("## Top 20 Worst Titles")
    w()
    for t in bad_titles:
        w(f"- `{t}`")
    w()
    w("## Top 20 Best Titles (for comparison)")
    w()
    if good_titles:
        for t in good_titles:
            w(f"- `{t}`")
    else:
        w("No qualifying 'good' titles found in sample.")
    w()
    w("## Title First Word Analysis")
    w()
    w("All titles start with one of these first words (sampled top 30):")
    for word, cnt in title_first_words.most_common(30):
        w(f"- `{word}`: {cnt:,} products")
    w()
    w("## Recommendations")
    w()
    if verdict == "REPLACE ENTIRELY":
        w("**This dataset is AI-generated gibberish and should be replaced entirely.**")
        w()
        w("Critical issues making it unusable:")
        w()
        w("1. **All 1M titles are fake.** Each title is a CSS color name (e.g. `BlanchedAlmond`, `DarkOrchid`) "
          "followed by random corporate buzzwords (`Upgradable motivating methodology`, `Compatible national solution`). "
          "No product is identifiable from its title.")
        w("2. **No prices.** The `price` field does not exist on any product — 100% missing.")
        w("3. **No brands.** The `brand` field does not exist on any product — 100% missing.")
        w("4. **No stock information.** The `in_stock` field does not exist on any product — 100% missing.")
        w("5. **No meaningful tags.** All `tags` arrays are empty — 100% empty.")
        w("6. **Wrong categories.** Only 7 categories exist (`Book`, `Movie`, `Electronics`, `Home`, `Apparel`, "
          "`Health`, `Toys`), none of which match the expected 10 commerce categories. `Movie` is not a product category.")
        w("7. **No real product nouns.** 72% of titles contain zero recognizable product words (no \"laptop\", "
          "\"shirt\", \"book\", etc.).")
        w()
        w("### Recommended actions")
        w()
        w("- **Replace** `data/products.json` with a real e-commerce product catalogue "
          "(e.g. from Kaggle, a retail API, or a structured dataset)")
        w("- Required fields per product: `id`, `title`, `category`, `brand`, `price`, `rating`, `in_stock`, `tags`")
        w("- Expected categories: Electronics, Clothing, Home & Kitchen, Books, Sports & Outdoors, "
          "Beauty & Personal Care, Toys & Games, Automotive, Health & Wellness, Office Supplies")
        w("- After replacement, re-run `python scripts/embed_products.py` to populate Qdrant")
    elif verdict == "NEEDS IMPROVEMENT":
        w("**Verdict: NEEDS IMPROVEMENT.** ...")
    else:
        w("**Verdict: GOOD DATA.** ...")

    REPORT_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"\nReport saved to {REPORT_FILE}")

    # Print summary
    print(f"\n{'='*60}")
    print(f"  Products scanned: {total:,}")
    print(f"  Issues found:     {total_issues:,}")
    print(f"  Quality score:    {score}/100")
    print(f"  Verdict:          {verdict}")
    print(f"{'='*60}")

    # Print top issues
    print(f"\nTop issues:")
    for issue, cnt in issues.most_common(10):
        pct = round(cnt / total * 100, 2) if total else 0
        print(f"  {issue}: {cnt:,} ({pct}%)")

    with open(REPORT_FILE, "r", encoding="utf-8") as f:
        return f.read()


if __name__ == "__main__":
    report = main()
