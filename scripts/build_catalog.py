"""Build catalog.json from the curation files in catalog/.

Run from the repo root after any curation change, then commit both:

    python scripts/build_catalog.py

catalog_loader.py reads only catalog.json (SEC-05), so the curation files are
the place to edit records and catalog.json is generated, never edited by hand.
The script does not validate records: catalog_loader.py does that at load time
(FR-13), and the NFR-10 gate (load validation, T04, link check) runs on the
result before merge.
"""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCES = sorted((ROOT / "catalog").glob("curation_*.json"))
OUTPUT = ROOT / "catalog.json"


def records_from(path: Path) -> list:
    data = json.loads(path.read_text(encoding="utf-8"))
    # Curation files exist in both shapes: a list, or {"products": [...]}
    return data["products"] if isinstance(data, dict) else data


def main() -> None:
    catalog = []
    for path in SOURCES:
        records = records_from(path)
        catalog.extend(records)
        print(f"{path.name}: {len(records)} records")
    OUTPUT.write_text(
        json.dumps(catalog, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(f"Wrote {len(catalog)} records to {OUTPUT.name}")


if __name__ == "__main__":
    main()
