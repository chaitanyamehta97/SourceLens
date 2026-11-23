"""UI tests for app.py with Streamlit's AppTest (no browser needed).

They run the real catalog_loader and recommender. Most use the generated
catalog.json; the FR-16 tests point the loader at a temporary file instead.

Run from the repo root:  python -m pytest -q tests test_catalog_security.py
"""

import json
from pathlib import Path

import pytest
import streamlit as st
from streamlit.testing.v1 import AppTest

import catalog_loader
from app import plain
from recommender import Recommender

APP = str(Path(__file__).parents[1] / "app.py")
NOTICE = "not from a generative AI model"


@pytest.fixture(autouse=True)
def fresh_cache():
    """Each test starts with no cached catalog."""
    st.cache_resource.clear()
    yield
    st.cache_resource.clear()


def run(**session):
    at = AppTest.from_file(APP, default_timeout=30)
    for key, value in session.items():
        at.session_state[key] = value
    return at.run()


ROOT = Path(__file__).parents[1]
CATALOG = ROOT / "catalog.json"
WEIGHTS = ROOT / "weights.json"
_real_load_catalog = catalog_loader.load_catalog


def use_catalog(monkeypatch, tmp_path, content: str):
    """Make the app load `content` instead of catalog.json (the app's path is fixed)."""
    path = tmp_path / "catalog.json"
    path.write_text(content, encoding="utf-8")
    monkeypatch.setattr(
        catalog_loader, "load_catalog", lambda _path: _real_load_catalog(path)
    )


def submit(at, budget, toggles=()):
    at.text_input[0].input(budget)
    for i in toggles:
        at.toggle[i].set_value(True)
    at.button[0].click().run()
    return at


def test_page_loads_real_catalog_with_notice():
    at = run()
    assert not at.exception
    assert any(NOTICE in i.value for i in at.info)  # FR-17
    count = len(catalog_loader.load_catalog(CATALOG))
    assert any(f"{count} products" in c.value for c in at.caption)
    assert not at.button[0].disabled


def test_every_control_has_a_visible_label():  # NFR-07
    at = run()
    labels = [
        at.text_input[0].label,
        *(s.label for s in at.selectbox),
        at.multiselect[0].label,
    ]
    assert labels == [
        "Maximum budget (USD)",
        "Headphone type",
        "Connection",
        "Features",
    ]


def test_must_have_toggle_appears_beside_each_selection():  # FR-02
    at = run(type="IN_EAR", features=["MICROPHONE", "WATER_RESISTANT"])
    assert [t.label for t in at.toggle] == [
        "Must-have: In-ear",
        "Must-have: Microphone",
        "Must-have: Water resistant",
    ]


def test_invalid_budget_shows_message_and_no_results():  # FR-03
    at = submit(run(), "nan")
    assert any("number" in e.value for e in at.error)
    assert not any(s.value == "Recommendations" for s in at.subheader)


def test_results_match_the_recommender():  # FR-06, end to end
    at = submit(
        run(connection="WIRELESS", features=["NOISE_CANCELLING", "MULTIPOINT"]),
        "300",
        [0],
    )
    assert not at.exception and not at.error
    request = at.session_state["request"]
    expected = Recommender(catalog_loader.load_catalog(CATALOG), WEIGHTS).recommend(
        request.to_recommender_prefs()
    )
    assert expected, "this request should return results on the real catalog"
    shown = [m.value for m in at.markdown if m.value.startswith("**#")]
    assert len(shown) == len(expected) <= 3
    for line, result in zip(shown, expected, strict=True):
        assert plain(result["product"]["name"]) in line


def test_no_match_lists_filters_without_relaxing():  # FR-10
    at = submit(run(features=["NOISE_CANCELLING"]), "1", [0])
    assert any("No matches found" in w.value for w in at.warning)
    filters = " ".join(m.value for m in at.markdown)
    assert (
        "budget up to $1" in filters and "must have Active noise cancelling" in filters
    )


def test_failed_catalog_blocks_requests_without_traceback(
    monkeypatch, tmp_path
):  # FR-16
    use_catalog(monkeypatch, tmp_path, "{not json")
    at = run()
    assert not at.exception
    assert at.button[0].disabled
    shown = " ".join(e.value for e in at.error)
    assert "couldn't be loaded" in shown and str(tmp_path) not in shown


def test_empty_catalog_counts_as_failure(monkeypatch, tmp_path):  # FR-16
    use_catalog(monkeypatch, tmp_path, "[]")
    assert run().button[0].disabled


def test_app_recovers_once_catalog_is_fixed(monkeypatch, tmp_path):
    """FR-16 blocks requests only "until a valid catalog is available"."""
    use_catalog(monkeypatch, tmp_path, "[]")
    at = run()
    assert at.button[0].disabled
    use_catalog(monkeypatch, tmp_path, CATALOG.read_text(encoding="utf-8"))
    at.run()
    assert not at.button[0].disabled


def test_catalog_text_is_escaped(monkeypatch, tmp_path):  # SEC-01
    records = json.loads(
        (Path(__file__).parents[1] / "catalog.json").read_text("utf-8")
    )
    hostile = dict(records[0], name="[click](javascript:alert(1)) **bold**")
    use_catalog(monkeypatch, tmp_path, json.dumps([hostile]))
    at = submit(run(), "2000")
    line = next(m.value for m in at.markdown if m.value.startswith("**#1"))
    assert "\\[click\\]" in line and "\\*\\*bold\\*\\*" in line


# ---------- W13: evidence panel (FR-07, FR-08, FR-15, SEC-01, SEC-02) ----------


def first_record_with(**changes):
    records = json.loads(CATALOG.read_text("utf-8"))
    return dict(records[0], **changes)


def test_every_result_has_a_sources_panel_for_its_reasons():  # FR-07, FR-08
    at = submit(run(connection="WIRELESS", features=["NOISE_CANCELLING"]), "500")
    request = at.session_state["request"]
    expected = Recommender(catalog_loader.load_catalog(CATALOG), WEIGHTS).recommend(
        request.to_recommender_prefs()
    )
    assert len(at.expander) == len(expected) > 0
    for panel, result in zip(at.expander, expected, strict=True):
        assert panel.label.startswith("Sources for these reasons")
        shown = " ".join(m.value for m in panel.markdown)
        for ev in result["product"]["evidence"]:
            if ev["supported_attribute"] in result["matched_attributes"]:
                assert plain(ev["factual_claim"]) in shown
        details = " ".join(c.value for c in panel.caption)
        assert "checked" in details and "](https://" in details


def test_source_link_shows_domain_and_real_url(monkeypatch, tmp_path):  # SEC-02
    record = first_record_with()
    record["evidence"] = [
        ev for ev in record["evidence"] if ev["supported_attribute"] == "TYPE"
    ]
    use_catalog(monkeypatch, tmp_path, json.dumps([record]))
    at = submit(run(type=record["type"]), "2000", [0])
    caption = at.expander[0].caption[0].value
    link_text, href = caption.split("[", 1)[1].split("](", 1)
    assert href.rstrip(")") == record["evidence"][0]["source_url"]
    domain = link_text.split(" :material", 1)[0].replace("\\", "")
    assert domain in href and not domain.startswith("www.")


@pytest.mark.parametrize(("days_ago", "labelled"), [(179, False), (181, True)])
def test_old_sources_are_labelled(monkeypatch, tmp_path, days_ago, labelled):  # FR-15
    from datetime import date, timedelta

    checked = (date.today() - timedelta(days=days_ago)).isoformat()
    record = first_record_with()
    record["evidence"] = [dict(ev, checked_on=checked) for ev in record["evidence"]]
    use_catalog(monkeypatch, tmp_path, json.dumps([record]))
    at = submit(run(type=record["type"]), "2000", [0])
    details = " ".join(c.value for c in at.expander[0].caption)
    assert ("source may be outdated" in details) is labelled


def test_evidence_text_is_escaped(monkeypatch, tmp_path):  # SEC-01
    record = first_record_with()
    record["evidence"] = [
        dict(ev, factual_claim="[win](javascript:alert(1)) **now**")
        if ev["supported_attribute"] == "TYPE"
        else ev
        for ev in record["evidence"]
    ]
    use_catalog(monkeypatch, tmp_path, json.dumps([record]))
    at = submit(run(type=record["type"]), "2000", [0])
    shown = " ".join(m.value for m in at.expander[0].markdown)
    assert "\\[win\\]" in shown and "\\*\\*now\\*\\*" in shown
