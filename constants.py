"""Shared constants and Enums for the headphone products loader.

Every categorical field is a strict string Enum with UPPER_SNAKE_CASE values
(e.g. "OVER_EAR"). Data must already use these exact values; anything else
raises ValueError, so bad data fails loudly instead of silently splitting
your queries.

    ProductType("OVER_EAR")   # ProductType.OVER_EAR
    ProductType("over-ear")   # ValueError

Because the Enums subclass `str`, members compare equal to their values and
serialize to plain strings, so they can go straight into JSON and MongoDB:

    {"type": ProductType.OVER_EAR}   # stored as "OVER_EAR"
"""

from enum import Enum

# ---------- database defaults ----------

DEFAULT_MONGO_URI = "mongodb://localhost:27017"
DEFAULT_DB_NAME = "headphones"
DEFAULT_COLLECTION_NAME = "products"

# ---------- formats ----------

DATE_FORMAT = "%Y-%m-%d"


# ---------- base enum ----------


class StrEnum(str, Enum):
    """String Enum whose str() is its value, with a helper for valid values."""

    def __str__(self) -> str:
        return self.value

    @classmethod
    def values(cls) -> list[str]:
        """All valid string values (handy for $jsonSchema enums)."""
        return [member.value for member in cls]


# ---------- product fields ----------


class ProductType(StrEnum):
    OVER_EAR = "OVER_EAR"
    ON_EAR = "ON_EAR"
    IN_EAR = "IN_EAR"


class Connection(StrEnum):
    WIRELESS = "WIRELESS"
    WIRED = "WIRED"
    BOTH = "BOTH"


class PriceBasis(StrEnum):
    MANUFACTURER_LIST = "MANUFACTURER_LIST"
    LAUNCH_MSRP = "LAUNCH_MSRP"


class FeatureTag(StrEnum):
    NOISE_CANCELLING = "NOISE_CANCELLING"
    COMFORT = "COMFORT"
    LONG_BATTERY = "LONG_BATTERY"
    WATER_RESISTANT = "WATER_RESISTANT"
    MICROPHONE = "MICROPHONE"
    MULTIPOINT = "MULTIPOINT"
    FOLDABLE = "FOLDABLE"


# ---------- evidence fields ----------


class EvidenceKind(StrEnum):
    SPEC = "SPEC"
    REVIEW_EXCERPT = "REVIEW_EXCERPT"


class SupportedAttribute(StrEnum):
    """What an evidence entry backs up: a structural field or a feature tag."""

    TYPE = "TYPE"
    CONNECTION = "CONNECTION"
    NOISE_CANCELLING = "NOISE_CANCELLING"
    COMFORT = "COMFORT"
    LONG_BATTERY = "LONG_BATTERY"
    WATER_RESISTANT = "WATER_RESISTANT"
    MICROPHONE = "MICROPHONE"
    MULTIPOINT = "MULTIPOINT"
    FOLDABLE = "FOLDABLE"


# Guard against the two tag lists drifting apart.
_missing = {t.name for t in FeatureTag} - {a.name for a in SupportedAttribute}
if _missing:  # not assert: asserts are stripped under python -O
    raise RuntimeError(f"SupportedAttribute is missing feature tags: {_missing}")
