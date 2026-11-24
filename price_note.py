"""Price display for the UI (W13, FR-18): pure functions, no Streamlit.

FR-18: every displayed price carries the record's updated_on date and a note
that catalog prices are informational and may differ from retailers.

Price policy (curation rule): the catalog stores the official list price,
never a sale price. A launch price is labelled as such because it may have
changed since launch. price_source_url is for curators only and is never shown.
Price is information, not evidence, so it never appears as a "reason".
"""

from evidence_panel import format_date, parse_checked_on

PRICE_NOTE = "Catalog prices are informational and may differ from retailers."
BASIS_LABELS = {
    "MANUFACTURER_LIST": "Manufacturer list price",
    "LAUNCH_MSRP": "Launch price — may differ today",
}
DEFAULT_BASIS_LABEL = "Catalog price"  # price_basis is optional in the loader


def format_price(product: dict) -> str:
    return f"${product['price_usd']:,.2f}"


def price_caption(product: dict) -> str:
    """e.g. "Launch price — may differ today · as of Nov 8, 2026 · Catalog prices…"."""
    basis = BASIS_LABELS.get(product.get("price_basis"), DEFAULT_BASIS_LABEL)
    as_of = format_date(parse_checked_on(product.get("updated_on")))
    return f"{basis} · as of {as_of} · {PRICE_NOTE}"
