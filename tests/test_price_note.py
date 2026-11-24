"""Unit tests for price_note.py (FR-18 and the list-price policy)."""

import pytest

from price_note import PRICE_NOTE, format_price, price_caption


def product(**overrides):
    base = {
        "price_usd": 449.0,
        "price_basis": "LAUNCH_MSRP",
        "updated_on": "2026-11-08",
        "price_source_url": "https://www.example.com/press/launch",
    }
    return base | overrides


def test_price_has_two_decimals_and_thousands_separator():
    assert format_price(product()) == "$449.00"
    assert format_price(product(price_usd=1999.5)) == "$1,999.50"


@pytest.mark.parametrize(
    ("basis", "label"),
    [
        ("LAUNCH_MSRP", "Launch price — may differ today"),
        ("MANUFACTURER_LIST", "Manufacturer list price"),
        (None, "Catalog price"),
    ],
)
def test_caption_names_the_price_basis(basis, label):
    assert price_caption(product(price_basis=basis)).startswith(label)


def test_caption_has_date_and_note():  # FR-18
    caption = price_caption(product())
    assert "as of Nov 8, 2026" in caption
    assert caption.endswith(PRICE_NOTE)


def test_bad_or_missing_date_reads_unavailable():
    assert "as of unavailable" in price_caption(product(updated_on="11/08/2026"))
    assert "as of unavailable" in price_caption(product(updated_on=None))


def test_price_source_url_is_never_shown():
    assert "example.com" not in price_caption(product())
