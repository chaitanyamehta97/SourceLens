"""Unit tests for preferences.py (W9): FR-02 request shape, FR-03 budget rules.

Run from the repo root:  python -m pytest -q tests
"""

import json
from pathlib import Path

import pytest

from constants import Connection, FeatureTag, ProductType
from preferences import (
    build_request,
    feature_options,
    label,
    validate_budget,
)

BUDGETS = json.loads(
    (Path(__file__).parent / "fixtures" / "inputs_budget.json").read_text(
        encoding="utf-8"
    )
)


@pytest.mark.parametrize("value", BUDGETS["accept"])
def test_budget_accepts(value):
    clean, error = validate_budget(value)
    assert error is None and clean == value.strip()


@pytest.mark.parametrize("case", BUDGETS["reject"], ids=lambda c: repr(c["value"]))
def test_budget_rejects(case):
    clean, error = validate_budget(case["value"])
    assert clean is None and error, case["why"]


def test_budget_messages_are_field_specific():
    assert validate_budget("")[1] == "Enter a maximum budget."
    assert "two decimal places" in validate_budget("12.345")[1]
    assert "$1.00 and $2,000.00" in validate_budget("2000.01")[1]
    assert "number" in validate_budget("nan")[1]


def test_invalid_budget_returns_no_request():
    request, errors = build_request("abc", features=[FeatureTag.MICROPHONE.value])
    assert request is None and set(errors) == {"budget"}


def test_request_shape_matches_fixtures():
    request, errors = build_request(
        "150",
        ProductType.OVER_EAR.value,
        Connection.WIRELESS.value,
        [FeatureTag.NOISE_CANCELLING.value, FeatureTag.MICROPHONE.value],
        {Connection.WIRELESS.value: True, FeatureTag.NOISE_CANCELLING.value: True},
    )
    assert errors == {}
    assert request.to_dict() == {
        "budget": "150",
        "criteria": [
            {"attribute": "type", "value": "OVER_EAR", "must_have": False},
            {"attribute": "connection", "value": "WIRELESS", "must_have": True},
            {"attribute": "feature", "value": "NOISE_CANCELLING", "must_have": True},
            {"attribute": "feature", "value": "MICROPHONE", "must_have": False},
        ],
    }
    assert [c.value for c in request.hard()] == ["WIRELESS", "NOISE_CANCELLING"]


def test_unmarked_selections_default_to_soft():
    request, _ = build_request("99", features=[FeatureTag.FOLDABLE.value])
    assert request.hard() == [] and len(request.soft()) == 1


def test_no_preferences_is_a_valid_request():
    request, errors = build_request("2000")
    assert errors == {} and request.criteria == ()


def test_values_outside_constants_are_rejected():
    _, errors = build_request("50", type_value="over-ear", features=["ANC"])
    assert set(errors) == {"type", "features"}


def test_every_constant_has_a_readable_label():
    for value in feature_options():
        assert label(value) and "_" not in label(value)


def test_recommender_prefs_shape():
    request, _ = build_request(
        "150",
        ProductType.IN_EAR.value,
        Connection.WIRELESS.value,
        [FeatureTag.MICROPHONE.value, FeatureTag.WATER_RESISTANT.value],
        {ProductType.IN_EAR.value: True, FeatureTag.MICROPHONE.value: True},
    )
    assert request.to_recommender_prefs() == {
        "budget_usd": "150",
        "type": "IN_EAR",
        "connection": "WIRELESS",
        "features": ["MICROPHONE", "WATER_RESISTANT"],
        "must_haves": ["TYPE", "MICROPHONE"],
    }


def test_must_haves_are_respected_by_the_real_recommender():
    from catalog_loader import load_catalog
    from recommender import Recommender

    request, _ = build_request(
        "2000",
        features=[FeatureTag.WATER_RESISTANT.value],
        must_have={FeatureTag.WATER_RESISTANT.value: True},
    )
    results = Recommender(load_catalog()).recommend(request.to_recommender_prefs())
    assert results
    for r in results:
        product = r["product"]
        assert "WATER_RESISTANT" in product["feature_tags"]
        assert "WATER_RESISTANT" in {
            e["supported_attribute"] for e in product["evidence"]
        }
