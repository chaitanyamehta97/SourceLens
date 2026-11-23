"""Preference request model and input validation for the SourceLens UI (W9).

Pure functions only, no Streamlit, so every rule here is unit-testable
(NFR-06). app.py collects raw form values and calls `build_request`.

Requirements covered:
    FR-02  budget plus optional type, connection and features, each with a
           must-have toggle; unmarked criteria are soft preferences
    FR-03  budget validation runs before any ranking

The request shape matches the test fixtures (tests/fixtures/requests.json):
    {"budget": "150", "criteria": [{"attribute": "feature",
                                    "value": "NOISE_CANCELLING",
                                    "must_have": True}]}

All option values come from constants.py, the single source of truth for
catalog vocabularies. This module never hard-codes a type, connection or tag.
"""

import re
from dataclasses import asdict, dataclass, field
from decimal import Decimal
from typing import Optional

from constants import Connection, FeatureTag, ProductType

BUDGET_MIN = Decimal("1.00")
BUDGET_MAX = Decimal("2000.00")

# Plain decimal: digits, optional point, at most two decimal places.
# Rejects "nan", "inf", "1e3", "1_000", "$50" and "-5" before any number
# is parsed, because Python's float() accepts several of those (FR-03).
_PLAIN_DECIMAL = re.compile(r"^\d+(\.\d+)?$")

# Display labels for the form. Members without a label still appear, with a
# readable fallback, so a vocabulary change in constants.py shows up in the
# UI without editing this file.
LABELS = {
    ProductType.OVER_EAR.value: "Over-ear",
    ProductType.ON_EAR.value: "On-ear",
    ProductType.IN_EAR.value: "In-ear",
    Connection.WIRELESS.value: "Wireless",
    Connection.WIRED.value: "Wired",
    Connection.BOTH.value: "Wired and wireless",
    FeatureTag.NOISE_CANCELLING.value: "Active noise cancelling",
    FeatureTag.WATER_RESISTANT.value: "Water resistant",
    FeatureTag.MICROPHONE.value: "Microphone",
    FeatureTag.MULTIPOINT.value: "Multipoint (two devices at once)",
    FeatureTag.FOLDABLE.value: "Foldable",
}


def label(value: str) -> str:
    """Human-readable label for a vocabulary value, e.g. OVER_EAR -> Over-ear."""
    return LABELS.get(value, value.replace("_", " ").capitalize())


def type_options() -> list[str]:
    return ProductType.values()


def connection_options() -> list[str]:
    return Connection.values()


def feature_options() -> list[str]:
    return FeatureTag.values()


@dataclass(frozen=True)
class Criterion:
    attribute: str  # "type", "connection" or "feature"
    value: str  # a value from constants.py
    must_have: bool = False


@dataclass(frozen=True)
class PreferenceRequest:
    budget: str  # validated plain decimal string, kept as text (no float rounding)
    criteria: tuple[Criterion, ...] = field(default_factory=tuple)

    def hard(self) -> list[Criterion]:
        return [c for c in self.criteria if c.must_have]

    def soft(self) -> list[Criterion]:
        return [c for c in self.criteria if not c.must_have]

    def to_dict(self) -> dict:
        """The shape the test fixtures use (tests/fixtures/requests.json)."""
        return {"budget": self.budget, "criteria": [asdict(c) for c in self.criteria]}

    def value_of(self, attribute: str) -> Optional[str]:
        """The value chosen for "type" or "connection", or None."""
        return next((c.value for c in self.criteria if c.attribute == attribute), None)

    def to_recommender_prefs(self) -> dict:
        """The dict recommender.Recommender.recommend() takes.

        must_haves holds attribute names from constants.SupportedAttribute:
        "TYPE", "CONNECTION", or the feature tag itself (e.g. "NOISE_CANCELLING").
        """
        must_haves = []
        for c in self.hard():
            if c.attribute == "feature":
                must_haves.append(c.value)
            else:
                must_haves.append(c.attribute.upper())  # "type" -> "TYPE"
        return {
            "budget_usd": self.budget,
            "type": self.value_of("type"),
            "connection": self.value_of("connection"),
            "features": [c.value for c in self.criteria if c.attribute == "feature"],
            "must_haves": must_haves,
        }


def validate_budget(raw: Optional[str]) -> tuple[Optional[str], Optional[str]]:
    """Return (clean_budget, None) if valid, or (None, field_message) if not (FR-03)."""
    text = (raw or "").strip()
    if not text:
        return None, "Enter a maximum budget."
    if not _PLAIN_DECIMAL.match(text):
        return (
            None,
            "Enter the budget as a number, like 150 or 149.99, without a $ sign.",
        )
    if "." in text and len(text.split(".")[1]) > 2:
        return None, "Use at most two decimal places."
    amount = Decimal(text)
    if amount < BUDGET_MIN or amount > BUDGET_MAX:
        return None, "Enter a budget between $1.00 and $2,000.00."
    return text, None


def build_request(
    budget_raw: Optional[str],
    type_value: Optional[str] = None,
    connection_value: Optional[str] = None,
    features: Optional[list[str]] = None,
    must_have: Optional[dict[str, bool]] = None,
) -> tuple[Optional[PreferenceRequest], dict[str, str]]:
    """Validate the form and build a request.

    `must_have` maps a value (e.g. "NOISE_CANCELLING") to its toggle state;
    anything not marked is a soft preference (FR-02).

    Returns (request, {}) on success or (None, {field: message}) on failure,
    so the UI can show each message next to its own field.
    """
    errors: dict[str, str] = {}
    budget, budget_error = validate_budget(budget_raw)
    if budget_error:
        errors["budget"] = budget_error

    # Defensive checks: the form only offers valid values, but the request
    # must never carry a value outside constants.py.
    if type_value is not None and type_value not in type_options():
        errors["type"] = "Choose a headphone type from the list."
    if connection_value is not None and connection_value not in connection_options():
        errors["connection"] = "Choose a connection from the list."
    unknown = [f for f in (features or []) if f not in feature_options()]
    if unknown:
        errors["features"] = "Choose features from the list."

    if errors:
        return None, errors

    flags = must_have or {}
    criteria: list[Criterion] = []
    if type_value:
        criteria.append(Criterion("type", type_value, bool(flags.get(type_value))))
    if connection_value:
        criteria.append(
            Criterion("connection", connection_value, bool(flags.get(connection_value)))
        )
    for f in dict.fromkeys(features or []):  # keep order, drop duplicates
        criteria.append(Criterion("feature", f, bool(flags.get(f))))
    return PreferenceRequest(budget=budget, criteria=tuple(criteria)), {}
