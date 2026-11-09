from dataclasses import dataclass, field
from re import escape
from typing import Any, List, Optional
from pymongo import ASCENDING
from pymongo.collection import Collection

# Import standard enums from your constants module
from constants import Connection, FeatureTag, ProductType


@dataclass
class SearchResult:
    products: List[dict] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return len(self.errors) == 0


class ProductBackend:
    """Handles query validation and builds MongoDB filters using modular helper methods backed by shared constants."""

    def __init__(self, db: Any):
        """Accepts a ProductDatabase instance (or any object holding `db.collection`)."""
        self.collection: Collection = db.collection

    # -------------------------------------------------------------------------
    # Modular Filter Builders
    # -------------------------------------------------------------------------

    def _build_price_filter(
            self, max_price: float, min_price: Optional[float] = None
    ) -> dict:
        price_clause: dict[str, Any] = {"$lte": max_price}
        if min_price is not None:
            price_clause["$gte"] = min_price
        return {"price_usd": price_clause}

    def _build_type_filter(self, types: List[ProductType]) -> Optional[dict]:
        if not types:
            return None
        return {"type": {"$in": [t.value if hasattr(t, "value") else t for t in types]}}

    def _build_connection_filter(
            self, connections: List[Connection]
    ) -> Optional[dict]:
        if not connections:
            return None

        formatted_conns = [
            c.value if hasattr(c, "value") else c for c in connections
        ]

        # Expanding logic: WIRELESS or WIRED also matches BOTH
        expanded = set(formatted_conns)
        if Connection.WIRELESS.value in expanded or Connection.WIRED.value in expanded:
            expanded.add(Connection.BOTH.value)

        return {"connection": {"$in": list(expanded)}}

    def _build_features_filter(
            self, feature_tags: List[FeatureTag]
    ) -> Optional[dict]:
        if not feature_tags:
            return None
        tags = [t.value if hasattr(t, "value") else t for t in feature_tags]
        return {"feature_tags": {"$all": tags}}

    def _build_brands_filter(self, brands: List[str]) -> Optional[dict]:
        clean_brands = [b.strip() for b in brands if b and b.strip()]
        if not clean_brands:
            return None
        regex_patterns = [f"^{escape(b)}$" for b in clean_brands]
        return {
            "$or": [{"brand": {"$regex": pat, "$options": "i"}} for pat in regex_patterns]
        }

    def _build_search_text_filter(self, search_text: Optional[str]) -> Optional[dict]:
        if not search_text or not search_text.strip():
            return None
        pattern = escape(search_text.strip())
        return {
            "$or": [
                {"name": {"$regex": pattern, "$options": "i"}},
                {"model": {"$regex": pattern, "$options": "i"}},
            ]
        }

    # -------------------------------------------------------------------------
    # Filter Composition
    # -------------------------------------------------------------------------

    def build_filter(self, query: ProductQuery) -> dict:
        """Combines sub-filter dictionaries into a single MongoDB query dictionary."""
        conditions = []

        # Price filter (Required)
        conditions.append(
            self._build_price_filter(query.max_price, query.min_price)
        )

        # Optional filters
        if type_filter := self._build_type_filter(query.types):
            conditions.append(type_filter)

        if conn_filter := self._build_connection_filter(query.connections):
            conditions.append(conn_filter)

        if feat_filter := self._build_features_filter(query.feature_tags):
            conditions.append(feat_filter)

        if brand_filter := self._build_brands_filter(query.brands):
            conditions.append(brand_filter)

        if text_filter := self._build_search_text_filter(query.search_text):
            conditions.append(text_filter)

        return {"$and": conditions} if len(conditions) > 1 else conditions[0]

    # -------------------------------------------------------------------------
    # Validation & Search Execution
    # -------------------------------------------------------------------------

    def validate_query(self, query: ProductQuery) -> List[str]:
        errors = []
        if query.max_price is None:
            errors.append("Please set a maximum price.")
        elif not isinstance(query.max_price, (int, float)) or query.max_price <= 0:
            errors.append("Maximum price must be a number greater than 0.")

        if query.min_price is not None:
            if not isinstance(query.min_price, (int, float)) or query.min_price < 0:
                errors.append("Minimum price cannot be negative.")
            elif query.max_price is not None and query.min_price > query.max_price:
                errors.append("Minimum price cannot be greater than maximum price.")

        return errors

    def search(self, query: ProductQuery) -> SearchResult:
        errors = self.validate_query(query)
        if errors:
            return SearchResult(products=[], errors=errors)

        mongo_filter = self.build_filter(query)
        cursor = self.collection.find(mongo_filter).sort("price_usd", ASCENDING)

        return SearchResult(products=list(cursor), errors=[])