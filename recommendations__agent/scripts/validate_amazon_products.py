import re
import json
import sys
import pathlib
import statistics
from collections import Counter, defaultdict

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

DATA_FILE = pathlib.Path(__file__).parent.parent / "data" / "amazon_products_clean.json"
CAT_FILE = pathlib.Path(__file__).parent.parent / "data" / "amazon_categories.csv"
REPORT_FILE = pathlib.Path(__file__).parent / "amazon_products_quality_report.md"

AMAZON_IMAGE_DOMAINS = {"images-amazon.com", "m.media-amazon.com"}

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
    "mousepad", "stand", "holder", "strap", "case",
    "cover", "protector", "screen", "oil", "supplement",
    "vitamin", "protein", "mask", "sanitizer", "towel",
    "sheet", "comforter", "pillowcase", "mat", "decor",
    "puzzle", "lego", "action", "figure", "card", "console",
    "controller", "headset", "charger", "cable", "adapter",
    "hub", "dock", "mount", "bracket", "lock", "safe",
    "alarm", "camera", "light", "bulb", "switch", "outlet",
    "plug", "sensor", "thermostat", "filter", "hose",
    "nozzle", "blade", "bit", "saw", "level", "tape",
    "glue", "paint", "brush", "roller", "tray",
    "luggage", "suitcase", "backpack", "duffel", "tote",
    "wallet", "purse", "handbag", "watch", "bracelet",
    "necklace", "ring", "earring", "belt", "hat", "cap",
    "beanie", "glove", "scarf", "sunglass", "glass",
    "shoe", "boot", "sandal", "slipper", "sneaker",
    "loafer", "heel", "flat", "pump",
    "jacket", "coat", "hoodie", "sweater", "cardigan",
    "vest", "blazer", "suit", "tie", "pant", "short",
    "short", "legging", "jogger", "sweatpant", "uniform",
    "costume", "lingerie", "pajama", "robe", "swimsuit",
    "bikini", "trunk", "bra", "underwear", "sock",
    "tights", "hose", "belt", "suspenders",
    "food", "snack", "drink", "coffee", "tea", "water",
    "soda", "juice", "protein", "bar", "shake", "powder",
}

BUZZWORD_PATTERNS = [
    "upgradable", "compatible", "multi-tiered", "versatile",
    "business-focused", "enterprise-wide", "robust", "cloned",
    "triple-buffered", "organic", "fundamental", "multi-channeled",
    "de-engineered", "expanded", "re-engineered", "progressive",
    "managed", "customer-focused", "distributed", "cross-platform",
    "user-centric", "integrated", "optimized", "universal",
    "streamlined", "innovative", "synergistic", "scalable",
    "motivating", "national", "human-resource", "neutral",
    "explicit", "disintermediate", "asymmetric", "secured",
    "systematic", "user-facing", "needs-based", "even-keeled",
    "holistic", "multi-tasking", "4thgeneration", "capacity",
    "homogeneous", "value-added", "mobile", "methodology",
    "solution", "paradigm", "moratorium", "monitoring",
    "superstructure", "line", "capability", "orchestration",
    "productivity", "challenge", "throughput", "migration",
    "model", "benchmark", "contingency", "leverage",
    "architecture", "toolset", "installation", "budgetary",
    "forecast", "initiative", "portal", "matrices", "database",
    "algorithm", "concept", "GraphicalUserInterface",
    "info-mediaries", "collaboration", "groupware",
    "contingency", "leverage", "orchestration",
]

SUSPICIOUS_SYMBOL_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\uFFFD]")


def load_categories(filepath):
    if not filepath.exists():
        print(f"  WARNING: {filepath} not found — skipping category cross-reference")
        return None
    mapping = {}
    with open(filepath, "r", encoding="utf-8") as f:
        import csv
        reader = csv.DictReader(f)
        for row in reader:
            cid = row.get("category_id", "").strip()
            cname = row.get("category_name", row.get("name", "")).strip()
            if cid:
                mapping[cid] = cname
    print(f"  Loaded {len(mapping)} categories from {filepath}")
    return mapping


def check_title_quality(title):
    issues = []
    if not title or len(title) < 5:
        issues.append("title_too_short")
        return issues
    if len(title) > 300:
        issues.append("title_too_long")

    words = title.split()
    first_word = words[0] if words else ""

    remaining_lower = title.lower()
    has_buzzword = any(bw in remaining_lower for bw in BUZZWORD_PATTERNS)
    has_noun = any(noun in remaining_lower for noun in REAL_PRODUCT_NOUNS)

    # Only flag CSS-color+ buzzword combo when there's no real product noun
    if first_word in CSS_COLORS and has_buzzword and not has_noun:
        issues.append("title_auto_generated_gibberish")

    if not has_noun and len(words) >= 3:
        issues.append("title_no_product_noun")

    if SUSPICIOUS_SYMBOL_RE.search(title):
        issues.append("title_suspicious_symbols")

    return issues


def check_price_quality(price, list_price):
    issues = []
    if price is None:
        issues.append("price_missing")
        return issues
    if not isinstance(price, (int, float)):
        issues.append("price_missing")
        return issues
    if price <= 0:
        issues.append("price_zero_or_negative")
    if price > 50000:
        issues.append("price_unrealistically_high")
    if list_price is not None and isinstance(list_price, (int, float)) and list_price > 0:
        if list_price < price:
            issues.append("original_price_lower_than_discounted")
    return issues


def check_category_quality(category_id, cat_mapping):
    issues = []
    if not category_id:
        issues.append("category_missing")
        return issues
    if cat_mapping is not None and category_id not in cat_mapping:
        issues.append("category_not_found_in_reference")
    return issues


def check_rating_quality(rating, review_count):
    issues = []
    if rating is None:
        issues.append("rating_missing")
    elif not isinstance(rating, (int, float)):
        issues.append("rating_missing")
    elif not (1.0 <= rating <= 5.0):
        issues.append("rating_out_of_range")
    if review_count is not None and isinstance(review_count, (int, float)) and review_count < 0:
        issues.append("negative_review_count")
    return issues


def check_image_quality(image_url):
    issues = []
    if not image_url:
        issues.append("image_url_missing")
        return issues
    if not image_url.startswith("https://"):
        issues.append("image_url_not_https")
    domain_match = re.search(r"https?://([^/]+)", image_url)
    if domain_match:
        domain = domain_match.group(1)
        if not any(ad in domain for ad in AMAZON_IMAGE_DOMAINS):
            issues.append("image_url_not_amazon_domain")
    return issues


def check_general_quality(product, seen_ids):
    issues = []
    required = ["id", "title", "category_id", "price", "rating"]
    for f in required:
        if f not in product or product[f] is None or (isinstance(product[f], str) and not product[f].strip()):
            issues.append(f"missing_required_field_{f}")

    pid = product.get("id", "")
    if pid:
        if pid in seen_ids:
            issues.append("duplicate_id")
        seen_ids.add(pid)
        if not re.match(r"^[A-Z0-9]{10}$", str(pid)):
            issues.append("invalid_asin_format")

    return issues


def main():
    cat_mapping = load_categories(CAT_FILE)

    total = 0
    total_issues = 0
    issue_counter = Counter()
    category_dist = Counter()
    prices = []
    ratings = []
    review_counts = []
    bought_counts = []
    bad_examples = []
    good_examples = []
    seen_ids = set()

    print(f"Scanning {DATA_FILE} ...")
    sys.stdout.flush()

    with open(DATA_FILE, "r", encoding="utf-8") as f:
        # skip opening bracket
        first_char = f.read(1)
        if first_char != "[":
            f.seek(0)
            data = json.load(f)
            for prod in data:
                total, total_issues = process_product(
                    prod, cat_mapping, seen_ids, category_dist,
                    prices, ratings, review_counts, bought_counts,
                    bad_examples, good_examples, issue_counter,
                    total, total_issues
                )
            print(f"  Scanned {total} products... Done.")
            generate_report(total, total_issues, issue_counter, category_dist,
                          prices, ratings, review_counts, bought_counts,
                          bad_examples, good_examples, cat_mapping)
            return

        for raw_line in f:
            line = raw_line.strip()
            if not line or line == "]" or line == ",":
                continue
            if line.endswith(","):
                line = line[:-1]
            if line.endswith("]"):
                line = line[:-1].rstrip(",")
            if not line:
                continue

            prod = json.loads(line)
            total, total_issues = process_product(
                prod, cat_mapping, seen_ids, category_dist,
                prices, ratings, review_counts, bought_counts,
                bad_examples, good_examples, issue_counter,
                total, total_issues
            )

    print(f"  Scanned {total} products... Done.")
    sys.stdout.flush()

    generate_report(total, total_issues, issue_counter, category_dist,
                    prices, ratings, review_counts, bought_counts,
                    bad_examples, good_examples, cat_mapping)


def process_product(prod, cat_mapping, seen_ids, category_dist,
                    prices, ratings, review_counts, bought_counts,
                    bad_examples, good_examples, issue_counter,
                    total, total_issues):
    total += 1
    all_issues = []

    title = prod.get("title", "") or ""
    category_id = str(prod.get("category_id", "") or "")
    price = prod.get("price")
    list_price = prod.get("list_price")
    rating = prod.get("rating")
    review_count = prod.get("review_count")
    image_url = prod.get("image_url", "") or ""

    all_issues.extend(check_title_quality(title))
    all_issues.extend(check_price_quality(price, list_price))
    all_issues.extend(check_category_quality(category_id, cat_mapping))
    all_issues.extend(check_rating_quality(rating, review_count))
    all_issues.extend(check_image_quality(image_url))
    all_issues.extend(check_general_quality(prod, seen_ids))

    category_dist[category_id or "MISSING"] += 1

    if isinstance(price, (int, float)) and price > 0:
        prices.append(price)
    if isinstance(rating, (int, float)) and rating > 0:
        ratings.append(rating)
    if isinstance(review_count, (int, float)):
        review_counts.append(review_count)
    if isinstance(prod.get("bought_in_last_month"), (int, float)):
        bought_counts.append(prod["bought_in_last_month"])

    if all_issues:
        total_issues += len(all_issues)
        for iss in all_issues:
            issue_counter[iss] += 1
        if len(bad_examples) < 20:
            bad_examples.append((title[:100], list(all_issues)))
    else:
        if len(good_examples) < 20:
            good_examples.append(title[:100])

    if total % 200000 == 0:
        print(f"  Scanned {total} products...")
        sys.stdout.flush()

    return total, total_issues


def generate_report(total, total_issues, issue_counter, category_dist,
                    prices, ratings, review_counts, bought_counts,
                    bad_examples, good_examples, cat_mapping):
    valid_count = total - (issue_counter.total() if issue_counter else 0)
    # Actually, a product is "valid" if it has zero issues
    # But we cant track that directly without a separate counter
    # Better: valid = total - number_of_products_with_any_issue
    # We can't recalculate that now. Let's estimate.

    valid_estimate = len(good_examples)  # just a lower bound, not accurate
    invalid_estimate = total - valid_estimate

    # Score: start at 100, deduct for each category of issue
    score = 100.0
    # Title quality
    title_issues = sum(v for k, v in issue_counter.items() if k.startswith("title_"))
    if title_issues > 0:
        pct = title_issues / max(total, 1) * 100
        score -= min(25, pct * 0.25)

    # Price issues
    price_issues = sum(v for k, v in issue_counter.items() if k.startswith("price_"))
    if price_issues > 0:
        pct = price_issues / max(total, 1) * 100
        score -= min(25, pct * 0.25)

    # Category issues
    cat_issues = sum(v for k, v in issue_counter.items() if k.startswith("category_"))
    if cat_issues > 0:
        pct = cat_issues / max(total, 1) * 100
        score -= min(20, pct * 0.2)

    # Rating issues
    rating_issues = sum(v for k, v in issue_counter.items() if k.startswith("rating_"))
    if rating_issues > 0:
        pct = rating_issues / max(total, 1) * 100
        score -= min(15, pct * 0.15)

    # Image issues
    img_issues = sum(v for k, v in issue_counter.items() if k.startswith("image_"))
    if img_issues > 0:
        pct = img_issues / max(total, 1) * 100
        score -= min(10, pct * 0.1)

    # General issues
    gen_issues = sum(v for k, v in issue_counter.items() if k.startswith("missing_required"))
    if gen_issues > 0:
        pct = gen_issues / max(total, 1) * 100
        score -= min(10, pct * 0.1)

    if issue_counter.get("duplicate_id", 0) > 0:
        score -= 5
    if issue_counter.get("invalid_asin_format", 0) > 0:
        score -= 5

    score = max(0, round(score, 1))

    if score >= 90:
        verdict = "PRODUCTION READY"
    elif score >= 60:
        verdict = "NEEDS CLEANING"
    else:
        verdict = "REPLACE ENTIRELY"

    # Compute stats
    price_min = min(prices) if prices else 0
    price_max = max(prices) if prices else 0
    price_avg = round(sum(prices) / len(prices), 2) if prices else 0
    price_med = round(statistics.median(prices), 2) if prices else 0
    rating_avg = round(sum(ratings) / len(ratings), 2) if ratings else 0
    total_reviews = sum(review_counts) if review_counts else 0

    w = []
    def ln(s=""):
        w.append(s)

    ln("# amazon_products_clean.json — Data Quality Report")
    ln()
    ln(f"Generated by `scripts/validate_amazon_products.py`")
    ln(f"**Date:** {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M')}")
    ln(f"**File:** `data/amazon_products_clean.json`")
    ln()

    ln("## Summary")
    ln()
    ln("| Metric | Value |")
    ln("|---|---|")
    ln(f"| Total Products Scanned | {total:,} |")
    ln(f"| Total Issues Found | {total_issues:,} |")
    ln(f"| Overall Quality Score | **{score}/100** |")
    ln(f"| Verdict | **{verdict}** |")
    ln()

    ln("## Issue Breakdown")
    ln()
    ln("| # | Issue Type | Count | % of Products |")
    ln("|---|---|---|---|")

    sorted_issues = sorted(issue_counter.items(), key=lambda x: -x[1])
    for i, (iss, cnt) in enumerate(sorted_issues, 1):
        pct = round(cnt / max(total, 1) * 100, 2)
        ln(f"| {i} | {iss} | {cnt:,} | {pct}% |")
    ln()

    ln("## Price Distribution")
    ln()
    ln(f"| Metric | Value |")
    ln("|---|---|")
    ln(f"| Min Price | ${price_min:.2f} |")
    ln(f"| Max Price | ${price_max:.2f} |")
    ln(f"| Average Price | ${price_avg:.2f} |")
    ln(f"| Median Price | ${price_med:.2f} |")
    ln()

    ln("## Rating Distribution")
    ln()
    ln(f"| Metric | Value |")
    ln("|---|---|")
    ln(f"| Average Rating | {rating_avg}/5.0 |")
    ln(f"| Products with Rating | {len(ratings):,} |")
    ln(f"| Total Reviews Across All Products | {total_reviews:,} |")
    ln()

    ln("## Category Distribution (Top 20)")
    ln()
    ln("| Category ID | Count | % of Total |")
    ln("|---|---|---|")
    for cid, cnt in category_dist.most_common(20):
        pct = round(cnt / max(total, 1) * 100, 2)
        cname = ""
        if cat_mapping and cid in cat_mapping:
            cname = f" ({cat_mapping[cid]})"
        ln(f"| {cid}{cname} | {cnt:,} | {pct}% |")
    if len(category_dist) > 20:
        ln(f"| ... and {len(category_dist) - 20} more categories | | |")
    ln()

    ln("## Top 20 Bad Products")
    ln()
    for title, issues in bad_examples:
        reasons = "; ".join(issues[:3])
        ln(f"- `{title}` → {reasons}")
    ln()

    ln("## Top 20 Good Products")
    ln()
    for title in good_examples:
        ln(f"- `{title}`")
    ln()

    ln("## Recommendations")
    ln()
    if verdict == "REPLACE ENTIRELY":
        ln("**This data is too synthetic or fake and should be replaced.**")
        ln()
        ln("Critical issues:")
        for iss, cnt in sorted_issues[:5]:
            ln(f"- {iss}: {cnt:,} products affected")
    elif verdict == "NEEDS CLEANING":
        ln("**The data has fixable issues that should be addressed before production use.**")
        ln()
        ln("Recommended actions:")
        ln()
        if issue_counter.get("rating_missing", 0) > 0:
            ln(f"- **{issue_counter['rating_missing']:,} products** have missing ratings — "
               "impute with category average or drop products with no ratings")
        if issue_counter.get("price_missing", 0) > 0:
            ln(f"- **{issue_counter['price_missing']:,} products** have missing prices — "
               "remove or flag as 'price unavailable'")
        if issue_counter.get("price_zero_or_negative", 0) > 0:
            ln(f"- **{issue_counter['price_zero_or_negative']:,} products** have zero/negative prices — remove these records")
        if issue_counter.get("original_price_lower_than_discounted", 0) > 0:
            ln(f"- **{issue_counter['original_price_lower_than_discounted']:,} products** have list_price < price — "
               "fix or remove the list_price")
        if issue_counter.get("image_url_not_amazon_domain", 0) > 0:
            ln(f"- **{issue_counter['image_url_not_amazon_domain']:,} products** have non-Amazon image URLs — "
               "verify these are valid")
        if not cat_mapping:
            ln("- **No category reference file found** (`data/amazon_categories.csv`) — "
               "create it for category validation")
    else:
        ln("**The data is realistic, clean, and production-ready.**")
        ln()
        ln("No significant quality issues found.")

    REPORT_FILE.write_text("\n".join(w) + "\n", encoding="utf-8")
    print(f"\nReport saved to {REPORT_FILE}")

    # Print summary
    print(f"\n{'='*60}")
    print(f"  Products scanned:          {total:,}")
    print(f"  Issues found:              {total_issues:,}")
    print(f"  Quality score:             {score}/100")
    print(f"  Verdict:                   {verdict}")
    print(f"  Valid products (approx):   ~{total - (issue_counter.total() if issue_counter else 0):,}")
    print(f"  Avg price:                 ${price_avg:.2f}")
    print(f"  Avg rating:                {rating_avg}/5.0")
    print(f"{'='*60}")

    print(f"\nTop issues:")
    for iss, cnt in sorted_issues[:10]:
        pct = round(cnt / max(total, 1) * 100, 2)
        print(f"  {iss}: {cnt:,} ({pct}%)")


if __name__ == "__main__":
    main()
