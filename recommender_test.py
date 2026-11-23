"""NOT READY YET"""
from pathlib import Path

import catalog_loader
from catalog_loader import load_catalog
from recommender import Recommender

TEST_CATALOG = Path(__file__).parent / "catalog_loader.json"
WEIGHTS = Path(__file__).parent / "weights.json"



def test_recommend():
    # 1) Dummy user requirements
    prefs = {
        "budget_usd": 300,
        "connection": "BOTH",
        "features": ["NOISE_CANCELLING", "MULTIPOINT", "FOLDABLE",'WATER_RESISTANT','MICROPHONE'],
        "must_haves": ["CONNECTION",'MULTIPOINT'],
    }

    # 2) Load the clean dataset through the real loader
    recommender = Recommender(load_catalog(), WEIGHTS)

    # 3) Check output
    results = recommender.recommend(prefs)

    print(len(results))
    assert [r["product"]["product_id"] for r in results] == [
        "soundcore-space-one",
        "sony-wf-c510",
        "beats-solo-4",
    ]
    assert [r["score"] for r in results] == [3.0, 1.0, 1.0]

    assert results[0]["matched_attributes"] == ["CONNECTION", "NOISE_CANCELLING", "MULTIPOINT", "FOLDABLE"]
    assert results[1]["match_summary"] == {
        "NOISE_CANCELLING": "not met",
        "MULTIPOINT": "met",
        "FOLDABLE": "not met",
    }



test_recommend()