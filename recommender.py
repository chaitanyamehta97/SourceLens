"""FR-04, FR-05, FR-06, FR-10, FR-19: filter, score and rank plain product dicts."""
import json
from pathlib import Path

from constants import Connection, FeatureTag, ProductType, SupportedAttribute
from shared import (
    MET, NOT_MET, NOT_VERIFIED,
    evidenced_attributes, product_has, validate_budget, validate_product,
)

DEFAULT_WEIGHT = 1.0
TOP_N = 3


def load_weights(path) -> dict[str, float]:
    """FR-05: weights config. Unknown keys raise ValueError; missing ones default to 1.0."""
    if path is None or not Path(path).exists():
        return {}
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    return {SupportedAttribute(name): float(weight) for name, weight in raw.items()}


def requested_criteria(prefs: dict) -> dict[str, str]:
    """Map each selected attribute to the value the user asked for.

    A dict, not a set, because TYPE and CONNECTION need their requested value:
        {"TYPE": "OVER_EAR", "CONNECTION": "WIRELESS", "MICROPHONE": "MICROPHONE"}
    """
    criteria = {}
    if prefs.get("type"):
        criteria[SupportedAttribute.TYPE] = ProductType(prefs["type"])
    if prefs.get("connection"):
        criteria[SupportedAttribute.CONNECTION] = Connection(prefs["connection"])
    for feature in prefs.get("features", []):
        tag = FeatureTag(feature)
        criteria[SupportedAttribute(tag.value)] = tag
    return criteria


def split_criteria(prefs: dict) -> tuple[dict, dict]:
    """Split selected criteria into (hard, soft).

    must_haves holds attribute names, e.g. ["CONNECTION", "NOISE_CANCELLING"].
    """
    criteria = requested_criteria(prefs)
    must_have_attributes = {SupportedAttribute(name) for name in prefs.get("must_haves", [])}
    hard = {
        attribute: target
        for attribute, target in criteria.items()
        if attribute in must_have_attributes
    }
    soft = {
        attribute: target
        for attribute, target in criteria.items()
        if attribute not in must_have_attributes
    }
    return hard, soft


def match_status(product: dict, attribute: str, target: str, evidenced: set[str]) -> str:
    """FR-19 / C15: MET only if the product claims the value AND has same-product evidence."""
    if not product_has(product, attribute, target):
        return NOT_MET
    return MET if attribute in evidenced else NOT_VERIFIED


def ranking_key(result: dict) -> tuple:
    """FR-05: highest score first, then lowest price, then product_id."""
    product = result["product"]
    return (-result["score"], product["price_usd"], product["product_id"])


class Recommender:
    def __init__(self, products: list[dict], weights_path):
        for product in products:
            validate_product(product)  # fail loudly once at startup, not on every request
        self.products = products
        self.weights = load_weights(weights_path)

    def recommend(self, prefs: dict) -> list[dict]:
        """Up to 3 results, or [] if nothing passes the hard filters. Never relaxes them (FR-10)."""
        budget = validate_budget(prefs.get("budget_usd"))
        hard, soft = split_criteria(prefs)
        results = []
        for product in self.products:
            # FR-04: budget is always a hard filter
            if product["price_usd"] > budget:
                continue

            # FR-04 / C15: every must-have has to be claimed AND backed by evidence
            evidenced = evidenced_attributes(product)
            meets_required_specs = all(
                product_has(product, attribute, target) for attribute, target in hard.items()
            )
            has_required_evidence = all(attribute in evidenced for attribute in hard)
            if not (meets_required_specs and has_required_evidence):
                continue

            # FR-19: met / not met / not met (not verified) for each soft preference
            match_summary = {
                attribute: match_status(product, attribute, target, evidenced)
                for attribute, target in soft.items()
            }
            met_soft = [attribute for attribute, status in match_summary.items() if status == MET]
            results.append({
                "product": product,
                "score": sum(self.weights.get(attribute, DEFAULT_WEIGHT) for attribute in met_soft),  # FR-05
                "matched_attributes": [*hard, *met_soft],  # every hard criterion passed above
                "match_summary": match_summary,
            })

        # FR-06: top 3 after a deterministic sort
        results.sort(key=ranking_key)
        return results[:TOP_N]



