"""The object the frontend fills in and passes to the backend."""

from dataclasses import dataclass, field
from typing import Optional

from constants import Connection, FeatureTag, ProductType


@dataclass
class ProductQuery:
    """Everything a user can fill in on the frontend.

    The frontend sends this back with only the fields the user filled in.
    An empty list or None means the user gave no preference for that field.
    """

    search_text: Optional[str] = None                             # name/model text search
    brands: list[str] = field(default_factory=list)               # e.g. ["Sony", "Bose"]
    types: list[ProductType] = field(default_factory=list)        # OVER_EAR, ON_EAR, IN_EAR
    connections: list[Connection] = field(default_factory=list)   # WIRELESS, WIRED, BOTH
    feature_tags: list[FeatureTag] = field(default_factory=list)  # NOISE_CANCELLING, ...
    min_price: Optional[float] = None                             # USD, inclusive
    max_price: Optional[float] = None                             # USD, inclusive
