import json
from pathlib import Path

_DATA_DIR = Path(__file__).resolve().parent.parent / "data"
_PRODUCTS_FILE = _DATA_DIR / "products.json"

_synthetic_catalogue: list[dict] | None = None


def load_products() -> list[dict]:
    global _synthetic_catalogue
    if _synthetic_catalogue is None:
        with open(_PRODUCTS_FILE, "r", encoding="utf-8") as f:
            _synthetic_catalogue = json.load(f)
    return _synthetic_catalogue
