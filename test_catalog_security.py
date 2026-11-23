"""Regression tests for the Security Review findings (SR-1..SR-4)."""
import json
import math
import pytest
import catalog_loader as cl
from catalog_loader import CatalogLoadError, parse_catalog

with open("catalog/curation_chaitanya.json", encoding="utf-8") as f:
    GOOD = json.load(f)["products"][0]

def record(**changes):
    r = json.loads(json.dumps(GOOD))
    r.update(changes)
    return r

@pytest.mark.parametrize("price", [math.nan, math.inf, -math.inf])
def test_non_finite_price_is_rejected_not_crash(price):  # SR-2
    with pytest.raises(CatalogLoadError):
        parse_catalog([record(price_usd=price)])

@pytest.mark.parametrize("bad_id", [["x"], {"a": 1}, 42])
def test_non_string_id_is_rejected_not_crash(bad_id):  # SR-2
    assert parse_catalog([record(product_id=bad_id), record(product_id="ok-1")])[0]["product_id"] == "ok-1"

def test_non_dict_evidence_is_rejected():  # SR-2
    with pytest.raises(CatalogLoadError):
        parse_catalog([record(evidence=["not-a-dict"])])

@pytest.mark.parametrize("shape", [[GOOD], {"products": [GOOD]}])
def test_both_catalog_shapes_load(tmp_path, monkeypatch, shape):  # SR-1
    path = tmp_path / "test_catalog.json"
    path.write_text(json.dumps(shape), encoding="utf-8")
    #monkeypatch.setattr(cl, "CATALOG_PATH", path)
    assert len(cl.load_catalog(path)) == 1

@pytest.mark.parametrize("shape", ['{"items": []}', '"text"', '42'])
def test_wrong_catalog_shape_fails_closed(tmp_path, monkeypatch, shape):  # SR-1
    path = tmp_path / "test_catalog.json"
    path.write_text(shape, encoding="utf-8")
    #monkeypatch.setattr(cl, "CATALOG_PATH", path)
    with pytest.raises(CatalogLoadError):
        cl.load_catalog(path)

def test_curated_catalogs_now_load():  # SR-3
    with open("catalog/curation_chaitanya.json", encoding="utf-8") as f:
        assert len(parse_catalog(json.load(f)["products"])) == 4
    with open("catalog/curation_quanjun.json", encoding="utf-8") as f:
        assert len(parse_catalog(json.load(f))) == 4

def test_javascript_url_evidence_is_dropped():  # SEC-02 regression
    r = record()
    r["evidence"][0]["source_url"] = "javascript:alert(1)"
    kept = parse_catalog([r])[0]["evidence"]
    assert all(e["source_url"].startswith(("http://", "https://")) for e in kept)
    assert len(kept) == len(GOOD["evidence"]) - 1
