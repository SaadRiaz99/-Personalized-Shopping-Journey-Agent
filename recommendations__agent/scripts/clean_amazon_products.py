import json
import re
import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

IN_FILE  = pathlib.Path(__file__).parent.parent / "data" / "amazon_products.json"
OUT_FILE = pathlib.Path(__file__).parent.parent / "data" / "amazon_products_clean.json"

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

SUSPICIOUS_CHARS_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\uFFFD]")


def is_gibberish(title):
    words = title.split()
    if not words:
        return True
    first_word = words[0]
    remaining_lower = title.lower()
    has_buzzword = any(bw in remaining_lower for bw in BUZZWORD_PATTERNS)
    return first_word in CSS_COLORS and has_buzzword


def clean_title(title):
    title = SUSPICIOUS_CHARS_RE.sub("", title)
    if len(title) > 200:
        title = title[:200].rstrip() + "..."
    return title


def main():
    print(f"Loading {IN_FILE} ...")
    with open(IN_FILE, "r", encoding="utf-8") as f:
        products = json.load(f)

    before = len(products)
    print(f"Products before cleaning: {before:,}")
    print()

    removed = {
        "missing_or_null_rating": 0,
        "missing_or_null_price": 0,
        "price_zero_or_negative": 0,
        "title_too_short": 0,
        "title_auto_generated_gibberish": 0,
        "image_url_not_https": 0,
    }

    kept = []
    for p in products:
        title       = (p.get("title") or "").strip()
        price       = p.get("price")
        rating      = p.get("rating")
        image_url   = (p.get("image_url") or "").strip()
        list_price  = p.get("list_price")

        reasons = []

        if rating is None or (isinstance(rating, (int, float)) and rating == 0):
            reasons.append("missing_or_null_rating")
        if price is None:
            reasons.append("missing_or_null_price")
        elif not isinstance(price, (int, float)) or price <= 0:
            reasons.append("price_zero_or_negative")
        if len(title) < 5:
            reasons.append("title_too_short")
        if is_gibberish(title):
            reasons.append("title_auto_generated_gibberish")
        if not image_url.startswith("https://"):
            reasons.append("image_url_not_https")

        if reasons:
            for r in reasons:
                removed[r] += 1
            continue

        # Fix minor issues
        p["title"] = clean_title(title)

        if list_price is not None and isinstance(list_price, (int, float)) and list_price > 0:
            if isinstance(price, (int, float)) and list_price < price:
                p["list_price"] = price

        kept.append(p)

    after = len(kept)
    print(f"Products removed: {before - after:,}")
    print()
    print("Removal breakdown:")
    for reason, count in removed.items():
        if count > 0:
            print(f"  {reason}: {count:,}")
    print()
    print(f"Products after cleaning: {after:,}")
    print(f"Removal rate: {(before - after) / before * 100:.1f}%")
    print(f"Quality score: {after / before * 100:.1f}/100")
    print()

    # Count remaining issues after fixes
    long_titles_fixed = sum(1 for p in kept if len(p.get("title", "")) > 195)
    price_fixed = sum(
        1 for p in kept
        if p.get("list_price") is not None
        and isinstance(p.get("price"), (int, float))
        and isinstance(p.get("list_price"), (int, float))
        and p["list_price"] < p["price"]
    )
    print(f"Long titles truncated: ~{long_titles_fixed:,}")
    print(f"Inverted prices fixed: ~{price_fixed:,}")

    OUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    print(f"\nSaving {OUT_FILE} ...")
    with open(OUT_FILE, "w", encoding="utf-8") as f:
        f.write("[")
        for i, p in enumerate(kept):
            if i > 0:
                f.write(",\n")
            f.write(json.dumps(p, ensure_ascii=False))
        f.write("]")

    out_mb = OUT_FILE.stat().st_size / 1024 / 1024
    print(f"Saved {after:,} products ({out_mb:.1f} MB)")


if __name__ == "__main__":
    main()
