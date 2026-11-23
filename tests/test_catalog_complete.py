"""Every record in the shipped catalog.json must load.

The loader drops an invalid record and keeps the rest (FR-13), so a bad record
would only show up as a log line and every other test would still pass. This
test makes a dropped record fail the build instead.
"""

import json
from pathlib import Path

from catalog_loader import load_catalog

ROOT = Path(__file__).parents[1]
CATALOG = ROOT / "catalog.json"


def test_every_catalog_record_loads():
    raw = json.loads(CATALOG.read_text(encoding="utf-8"))
    expected = [r["product_id"] for r in raw]
    loaded = [r["product_id"] for r in load_catalog(CATALOG)]
    assert loaded == expected, f"dropped at load: {sorted(set(expected) - set(loaded))}"


def test_catalog_json_matches_curation_files():
    """catalog.json must be rebuilt after any curation change (build_catalog.py)."""
    built = []
    for path in sorted((ROOT / "catalog").glob("curation_*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        built.extend(data["products"] if isinstance(data, dict) else data)
    shipped = json.loads(CATALOG.read_text(encoding="utf-8"))
    assert shipped == built, "catalog.json is stale: run python scripts/build_catalog.py"
