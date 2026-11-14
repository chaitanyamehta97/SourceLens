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

#todo: This is hard to read. Can this be a set?
# must_haves may name the attribute ("CONNECTION") or its value ("WIRELESS")
MUST_HAVE_ALIASES = {
    **{v: SupportedAttribute.TYPE for v in ProductType.values()},
    **{v: SupportedAttribute.CONNECTION for v in Connection.values()},
}


def load_weights(path) -> dict[str, float]:
    """FR-05: weights config. Unknown keys raise ValueError; missing ones default to 1.0."""
    if path is None or not Path(path).exists():
        return {}
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    return {SupportedAttribute(k): float(v) for k, v in raw.items()}


def split_criteria(prefs: dict) -> tuple[dict, dict]:
    """Validate the user's selections and split them into (hard, soft) {attribute: target} maps."""
    criteria = {}
    # todo: Why do we need a dict here? can we use a set?

    if prefs.get("type"):
        criteria[SupportedAttribute.TYPE] = ProductType(prefs["type"])
    if prefs.get("connection"):
        criteria[SupportedAttribute.CONNECTION] = Connection(prefs["connection"])
    for tag in map(FeatureTag, prefs.get("features", [])):
        criteria[SupportedAttribute(tag.value)] = tag

    # todo: make this easier to read. Use more readable names (not "a", "must"
    must = {MUST_HAVE_ALIASES.get(m) or SupportedAttribute(m) for m in prefs.get("must_haves", [])}
    hard = {a: t for a, t in criteria.items() if a in must}
    soft = {a: t for a, t in criteria.items() if a not in must}
    return hard, soft


def status(product: dict, attribute: str, target: str, evidenced: set[str]) -> str:
    """MET only if the product claims the value AND has same-product evidence (C15)."""
    if not product_has(product, attribute, target):
        return NOT_MET
    return MET if attribute in evidenced else NOT_VERIFIED


class Recommender:
    def __init__(self, products: list[dict], weights_path: str | None = None):
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
            if product["price_usd"] > budget:  # FR-04: budget is always hard
                continue
            evidenced = evidenced_attributes(product)

            #todo: make this easier to read. Spit in has evidence and has required product specs
            if any(status(product, a, t, evidenced) != MET for a, t in hard.items()):  # FR-04
                continue

            summary = {a: status(product, a, t, evidenced) for a, t in soft.items()}  # FR-19
            met = [a for a, s in summary.items() if s == MET]
            results.append({
                "product": product,
                "score": sum(self.weights.get(a, DEFAULT_WEIGHT) for a in met),  # FR-05
                "matched_attributes": [*hard, *met],  # every hard criterion is MET here
                "match_summary": summary,
            })

        # FR-05 / FR-06: score desc, then price asc, then product_id asc; top 3
        results.sort(key=lambda r: (-r["score"], r["product"]["price_usd"], r["product"]["product_id"]))
        return results[:TOP_N]



