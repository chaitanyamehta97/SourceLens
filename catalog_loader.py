"""Data layer: load catalog.json once at startup and keep only valid records.

FR-13  reject invalid records, log a non-sensitive diagnostic, continue with the rest
FR-16  raise CatalogLoadError so app.py can block requests when nothing usable loads
NFR-09 unique IDs, USD prices with two decimals, source references checked at load
SEC-04 logs carry only the record position and a reason code, never raw values or IDs
SEC-05 reads one fixed path; no function here takes a path from the user
"""
import json
import logging
import math
from collections import Counter
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from urllib.parse import urlparse

from constants import DATE_FORMAT, PriceBasis
from shared import validate_product

logger = logging.getLogger(__name__)

CATALOG_PATH = Path(__file__).parent / "catalog.json"  # SEC-05: fixed, read-only

IDENTITY_FIELDS = ("product_id", "name", "brand", "model")
EVIDENCE_FIELDS = (
    "evidence_id", "supported_attribute", "factual_claim", "evidence_kind",
    "source_name", "source_url", "checked_on",
)
SAFE_URL_SCHEMES = {"http", "https"}  # SEC-02: javascript:, file: etc. are rejected


class CatalogLoadError(Exception):
    """FR-16: no usable catalog. app.py shows a non-technical error and blocks requests."""


def is_iso_date(value) -> bool:
    try:
        datetime.strptime(value, DATE_FORMAT)
        return True
    except (TypeError, ValueError):
        return False


def is_valid_price(value) -> bool:
    """NFR-09 / §4.1: a number >= 0.00 with at most two decimals."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return False
    if not math.isfinite(value):  # json.loads accepts NaN/Infinity literals
        return False
    price = Decimal(str(value))
    return price >= 0 and price.as_tuple().exponent >= -2


def is_safe_url(url) -> bool:
    parsed = urlparse(url) if isinstance(url, str) else None
    return bool(parsed and parsed.scheme in SAFE_URL_SCHEMES and parsed.netloc)


def rejection_reason(record, duplicate_ids: set):
    """Return why a record must be rejected (FR-13), or None if it is valid."""
    if not isinstance(record, dict):
        return "not_an_object"
    if any(not isinstance(record.get(field), str) or not record[field].strip()
           for field in IDENTITY_FIELDS):
        return "missing_identity_field"
    if record["product_id"] in duplicate_ids:
        return "duplicate_id"
    if not is_valid_price(record.get("price_usd")):
        return "invalid_price"
    if not is_iso_date(record.get("updated_on")):
        return "invalid_updated_on"
    try:
        validate_product(record)  # type, connection, feature_tags, evidence enums
        if record.get("price_basis") is not None:
            PriceBasis(record["price_basis"])
    except (KeyError, TypeError, ValueError):
        return "out_of_vocabulary"
    for evidence in record.get("evidence", []):
        if not isinstance(evidence, dict):
            return "incomplete_evidence"
        if any(field not in evidence for field in EVIDENCE_FIELDS):
            return "incomplete_evidence"
        if not is_iso_date(evidence["checked_on"]):
            return "invalid_evidence_date"
    return None


def drop_unsafe_evidence(record: dict, position: int) -> dict:
    """Remove evidence with an unsafe source_url. That attribute then shows as "not verified" (C15)."""
    safe = [ev for ev in record.get("evidence", []) if is_safe_url(ev["source_url"])]
    dropped = len(record.get("evidence", [])) - len(safe)
    if dropped:
        logger.warning("Catalog record #%d: dropped %d evidence item(s): unsafe_source_url", position, dropped)
    return {**record, "evidence": safe}


def parse_catalog(raw_records) -> list[dict]:
    """Validate already-parsed JSON. Kept separate from file reading so tests can pass fixtures."""
    if not isinstance(raw_records, list):
        raise CatalogLoadError("Catalog must be a JSON list.")

    # FR-13: every record that shares an ID is rejected, since we can't tell which one is right
    id_counts = Counter(
        r.get("product_id") for r in raw_records
        if isinstance(r, dict) and isinstance(r.get("product_id"), str)
    )
    duplicate_ids = {product_id for product_id, count in id_counts.items() if count > 1}

    products = []
    for position, record in enumerate(raw_records):
        reason = rejection_reason(record, duplicate_ids)
        if reason:
            logger.warning("Catalog record #%d rejected: %s", position, reason)  # SEC-04
            continue
        products.append(drop_unsafe_evidence(record, position))

    if not products:
        raise CatalogLoadError("Catalog has no valid records.")
    logger.info("Catalog loaded: %d valid, %d rejected", len(products), len(raw_records) - len(products))
    return products


def load_catalog() -> list[dict]:
    """Read CATALOG_PATH once at startup. Raises CatalogLoadError on any failure (FR-16)."""
    try:
        raw_records = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        logger.error("Catalog could not be read or parsed.")  # no path or traceback (FR-16)
        raise CatalogLoadError("Catalog could not be read.") from None
    if isinstance(raw_records, dict):
        raw_records = raw_records.get("products")
    return parse_catalog(raw_records)  # non-list shapes raise CatalogLoadError there

