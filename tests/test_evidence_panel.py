"""Unit tests for evidence_panel.py (FR-07, FR-08, FR-09, FR-15, SEC-02)."""

from datetime import date, timedelta

import pytest

from evidence_panel import (
    UNAVAILABLE,
    evidence_rows,
    format_date,
    is_outdated,
    parse_checked_on,
    safe_link,
)

TODAY = date(2026, 11, 22)


def item(attribute="TYPE", **overrides):
    base = {
        "evidence_id": f"p-{attribute}",
        "supported_attribute": attribute,
        "factual_claim": f"Claim about {attribute}.",
        "evidence_kind": "SPEC",
        "source_name": "Maker product page",
        "checked_on": "2026-11-08",
        "source_url": "https://www.example.com/p/1",
    }
    return base | overrides


# ---------- SEC-02 ----------


@pytest.mark.parametrize(
    ("url", "expected_domain"),
    [
        ("https://www.bose.com/p/qc", "bose.com"),
        ("http://sony.com/x", "sony.com"),
        ("HTTPS://Shop.Example.com/a", "shop.example.com"),
    ],
)
def test_safe_link_accepts_http_and_https(url, expected_domain):
    domain, href = safe_link(url)
    assert domain == expected_domain
    assert href.lower().startswith("http")


@pytest.mark.parametrize(
    "url",
    [
        "javascript:alert(1)",
        "file:///etc/passwd",
        "data:text/html,<b>x</b>",
        "https://",
        "//example.com/no-scheme",
        "",
        None,
        42,
    ],
)
def test_safe_link_rejects_everything_else(url):
    assert safe_link(url) is None


def test_link_target_cannot_break_out_of_markdown():
    _, href = safe_link("https://example.com/a (b)[c]<d>")
    for ch in " ()[]<>":
        assert ch not in href


# ---------- FR-15 ----------


@pytest.mark.parametrize(
    ("days_ago", "outdated"), [(179, False), (180, False), (181, True)]
)
def test_outdated_after_180_days(days_ago, outdated):
    assert is_outdated(TODAY - timedelta(days=days_ago), TODAY) is outdated


def test_unknown_date_is_not_called_outdated():
    assert is_outdated(None, TODAY) is False


@pytest.mark.parametrize("value", [None, "", "2026-13-01", "11/08/2026", 20261108])
def test_bad_dates_parse_to_none(value):
    assert parse_checked_on(value) is None
    assert format_date(parse_checked_on(value)) == UNAVAILABLE


def test_date_is_shown_in_plain_english():
    assert format_date(date(2026, 11, 8)) == "Nov 8, 2026"


# ---------- FR-07, FR-08, FR-09 ----------


def test_rows_follow_reason_order_and_skip_other_evidence():
    product = {"evidence": [item("MICROPHONE"), item("TYPE"), item("FOLDABLE")]}
    rows = evidence_rows(product, ["TYPE", "MICROPHONE"], TODAY)
    assert [r["attribute"] for r in rows] == ["TYPE", "MICROPHONE"]


def test_row_has_every_fr08_field():
    row = evidence_rows({"evidence": [item()]}, ["TYPE"], TODAY)[0]
    assert row == {
        "attribute": "TYPE",
        "claim": "Claim about TYPE.",
        "source_name": "Maker product page",
        "link": ("example.com", "https://www.example.com/p/1"),
        "kind": "Manufacturer spec",
        "checked": "Nov 8, 2026",
        "outdated": False,
    }


def test_every_item_for_a_reason_is_listed():
    product = {"evidence": [item("TYPE"), item("TYPE", evidence_id="p-TYPE-2")]}
    assert len(evidence_rows(product, ["TYPE"], TODAY)) == 2


def test_reason_without_evidence_gets_no_claim():  # FR-09
    assert evidence_rows({"evidence": [item("TYPE")]}, ["MICROPHONE"], TODAY) == []


def test_broken_parts_read_unavailable():  # FR-08
    broken = item(
        factual_claim="  ",
        source_name=None,
        source_url="javascript:alert(1)",
        evidence_kind="RUMOR",
        checked_on="not a date",
    )
    row = evidence_rows({"evidence": [broken]}, ["TYPE"], TODAY)[0]
    assert row["claim"] == row["source_name"] == row["kind"] == UNAVAILABLE
    assert row["checked"] == UNAVAILABLE
    assert row["link"] is None
    assert row["outdated"] is False


def test_old_item_is_flagged():  # FR-15
    old = item(checked_on=(TODAY - timedelta(days=181)).isoformat())
    assert evidence_rows({"evidence": [old]}, ["TYPE"], TODAY)[0]["outdated"]
