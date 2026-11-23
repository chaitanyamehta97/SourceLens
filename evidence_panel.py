"""Evidence panel data for the UI (W13): pure functions, no Streamlit.

    FR-07  a reason is shown with the same-product evidence that supports it
    FR-08  each item gives claim, source name, source reference, evidence kind
           and verification date; missing or broken parts read "unavailable"
    FR-09  an attribute with no evidence item gets no claim here
    FR-15  evidence checked more than 180 days ago is labelled
           "source may be outdated"
    SEC-02 only http/https links with a host are shown, with their domain

Kept separate from app.py so these rules can be unit-tested without a browser.
"""

from datetime import date, datetime
from urllib.parse import quote, urlparse

OUTDATED_AFTER_DAYS = 180  # FR-15: day 180 is still current, day 181 is outdated
OUTDATED_LABEL = "source may be outdated"
UNAVAILABLE = "unavailable"
SAFE_SCHEMES = {"http", "https"}
KIND_LABELS = {"SPEC": "Manufacturer spec", "REVIEW_EXCERPT": "Review excerpt"}
# Characters left as-is in a link target. Parentheses, spaces and angle brackets
# are percent-encoded so a URL can never break out of a Markdown link.
_URL_SAFE = ":/?#@!$&'*+,;=%~-._"


def safe_link(url) -> tuple[str, str] | None:
    """Return (domain, href) for an http/https URL with a host, else None (SEC-02)."""
    if not isinstance(url, str):
        return None
    try:
        parsed = urlparse(url.strip())
    except ValueError:
        return None
    if parsed.scheme.lower() not in SAFE_SCHEMES or not parsed.hostname:
        return None
    domain = parsed.hostname.removeprefix("www.")
    return domain, quote(url.strip(), safe=_URL_SAFE)


def parse_checked_on(value) -> date | None:
    """ISO date (YYYY-MM-DD) or None if missing or malformed."""
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except (TypeError, ValueError):
        return None


def is_outdated(checked: date | None, today: date) -> bool:
    """FR-15. An unknown date is not called outdated; it already reads "unavailable"."""
    return checked is not None and (today - checked).days > OUTDATED_AFTER_DAYS


def format_date(value: date | None) -> str:
    return f"{value:%b} {value.day}, {value.year}" if value else UNAVAILABLE


def _text(item: dict, field: str) -> str:
    value = item.get(field)
    return value.strip() if isinstance(value, str) and value.strip() else UNAVAILABLE


def evidence_rows(product: dict, attributes: list[str], today: date) -> list[dict]:
    """One row per evidence item behind each reason, in the order the reasons are shown.

    Each row: attribute, claim, source_name, link ((domain, href) or None),
    kind, checked (display text) and outdated (bool).
    """
    rows = []
    for attribute in attributes:
        for item in product.get("evidence", []):
            if item.get("supported_attribute") != attribute:
                continue
            checked = parse_checked_on(item.get("checked_on"))
            rows.append(
                {
                    "attribute": attribute,
                    "claim": _text(item, "factual_claim"),
                    "source_name": _text(item, "source_name"),
                    "link": safe_link(item.get("source_url")),
                    "kind": KIND_LABELS.get(item.get("evidence_kind"), UNAVAILABLE),
                    "checked": format_date(checked),
                    "outdated": is_outdated(checked, today),
                }
            )
    return rows
