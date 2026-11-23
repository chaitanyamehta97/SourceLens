# SourceLens

Headphone recommendations where every reason links to its source.
MSCS 2101 · Group 5.

## Run locally (Windows 11 or Ubuntu 22.04, Python 3.10+)

```bash
pip install -r requirements.txt
python scripts/build_catalog.py      # builds catalog.json from catalog/curation_*.json
streamlit run app.py                 # opens http://localhost:8501
```

## Tests

```bash
python -m pytest -q tests test_catalog_security.py
```

`recommender_test.py` is still marked NOT READY and is excluded for now.

## Editing the catalog

Edit a file in `catalog/`, rerun `python scripts/build_catalog.py`, and commit
both the curation file and `catalog.json`. Never edit `catalog.json` by hand.
Every catalog change needs a pull request with one reviewer who checks each new
evidence item against its source (NFR-10, Security Review SR-8).
