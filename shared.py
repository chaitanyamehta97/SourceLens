"""Plain-dict helpers shared across backend modules. Products are raw dicts from catalog.json."""
from decimal import Decimal, InvalidOperation

from constants import Connection, EvidenceKind, FeatureTag, ProductType, SupportedAttribute

MET, NOT_MET, NOT_VERIFIED = "met", "not met", "not met (not verified)"  # FR-19
MIN_BUDGET, MAX_BUDGET = Decimal("1.00"), Decimal("2000.00")              # FR-03

# C17: product connection -> requested connections it satisfies
CONNECTION_SATISFIES = {
    Connection.WIRED: {Connection.WIRED},
    Connection.WIRELESS: {Connection.WIRELESS},
    Connection.BOTH: {Connection.WIRED, Connection.WIRELESS, Connection.BOTH},
}


def validate_budget(raw) -> float:
    """FR-03: 1.00-2,000.00 with at most 2 decimals. None/blank/text raise ValueError."""
    try:
        dec = Decimal(str(raw).strip())
    except InvalidOperation:
        raise ValueError(f"Invalid budget: {raw!r}") from None
    if not dec.is_finite() or dec.as_tuple().exponent < -2 or not MIN_BUDGET <= dec <= MAX_BUDGET:
        raise ValueError("Budget must be 1.00-2,000.00 with at most 2 decimal places.")
    return float(dec)


def validate_product(product: dict) -> None:
    """FR-13: raise ValueError if any categorical value is outside constants.py."""
    ProductType(product["type"])
    Connection(product["connection"])
    for tag in product.get("feature_tags", []):
        FeatureTag(tag)
    for ev in product.get("evidence", []):
        EvidenceKind(ev["evidence_kind"])
        SupportedAttribute(ev["supported_attribute"])


def product_has(product: dict, attribute: str, target: str) -> bool:
    """Does the product claim the requested value? (C17 applies to connection.)"""
    if attribute == SupportedAttribute.TYPE:
        return product["type"] == target
    if attribute == SupportedAttribute.CONNECTION:
        return target in CONNECTION_SATISFIES[product["connection"]]
    return target in product.get("feature_tags", [])


def evidenced_attributes(product: dict) -> set[str]:
    """Attributes backed by at least one evidence item on this same product (C15)."""
    return {ev["supported_attribute"] for ev in product.get("evidence", [])}



