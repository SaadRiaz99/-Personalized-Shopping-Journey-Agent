import csv
import json
import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

CSV_FILE = pathlib.Path(__file__).parent.parent / "amazon_products.csv"
OUT_FILE = pathlib.Path(__file__).parent.parent / "data" / "amazon_products.json"

MISSING = object()


def parse_float(val: str) -> float | None:
    v = val.strip()
    if not v:
        return None
    try:
        f = float(v)
        return f if f > 0 else None
    except ValueError:
        return None


def parse_int(val: str) -> int | None:
    v = val.strip()
    if not v:
        return None
    try:
        return int(float(v))
    except ValueError:
        return None


def parse_bool(val: str) -> bool:
    return val.strip().lower() == "true"


def transform(row: dict) -> dict:
    return {
        "id":               row.get("asin", "").strip(),
        "title":            row.get("title", "").strip(),
        "image_url":        row.get("imgUrl", "").strip(),
        "product_url":      row.get("productURL", "").strip(),
        "rating":           parse_float(row.get("stars", "")),
        "review_count":     parse_int(row.get("reviews", "")),
        "price":            parse_float(row.get("price", "")),
        "list_price":       parse_float(row.get("listPrice", "")),
        "category_id":      row.get("category_id", "").strip(),
        "is_best_seller":   parse_bool(row.get("isBestSeller", "false")),
        "bought_in_last_month": parse_int(row.get("boughtInLastMonth", "")),
        "in_stock":         True,
    }


def main():
    import os

    total = 0
    written = 0
    skipped = 0

    # Count lines first for progress
    print("Counting rows...")
    with open(CSV_FILE, "r", encoding="utf-8") as f:
        line_count = sum(1 for _ in f) - 1
    print(f"CSV has {line_count:,} data rows")
    print()

    sys.stdout.flush()

    # Drop fields we dont keep
    drop_fields = {"imgUrl", "productURL", "listPrice", "isBestSeller", "boughtInLastMonth", "asin", "stars", "reviews"}
    kept = {"id", "title", "rating", "review_count", "price", "list_price", "category_id",
            "is_best_seller", "bought_in_last_month", "in_stock", "image_url", "product_url"}

    # Write JSON array line by line
    out_parent = OUT_FILE.parent
    if not out_parent.exists():
        out_parent.mkdir(parents=True)

    with open(CSV_FILE, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        with open(OUT_FILE, "w", encoding="utf-8") as out:
            out.write("[")
            first = True

            for i, row in enumerate(reader):
                total += 1
                obj = transform(row)

                # Skip rows missing critical fields
                if not obj["id"] or not obj["title"]:
                    skipped += 1
                    continue

                if not first:
                    out.write(",\n")
                out.write(json.dumps(obj, ensure_ascii=False))
                written += 1
                first = False

                if total % 100000 == 0:
                    pct = total / line_count * 100
                    print(f"  Processed {total:,}/{line_count:,} ({pct:.1f}%) — wrote {written:,}, skipped {skipped:,}")
                    sys.stdout.flush()

            out.write("]")

    out_size = os.path.getsize(OUT_FILE)
    print()
    print(f"Done.")
    print(f"  Total CSV rows:  {total:,}")
    print(f"  Written to JSON: {written:,}")
    print(f"  Skipped:         {skipped:,}")
    print(f"  Output file:     {OUT_FILE}")
    print(f"  File size:       {out_size / 1024 / 1024:.1f} MB")


if __name__ == "__main__":
    main()
