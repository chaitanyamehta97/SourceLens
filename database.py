import json
from datetime import datetime
from typing import Any, Optional

from pymongo import ASCENDING, MongoClient, UpdateOne
from pymongo.collection import Collection
from pymongo.errors import PyMongoError


class ProductDatabase:
    """Handles all MongoDB operations for the headphone products collection."""

    def __init__(
        self,
        uri: str = "mongodb://localhost:27017",
        db_name: str = "headphones",
        collection_name: str = "products",
    ):
        self.client = MongoClient(uri)
        self.collection: Collection = self.client[db_name][collection_name]

    # ---------- lifecycle ----------

    def close(self) -> None:
        self.client.close()

    def __enter__(self) -> "ProductDatabase":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    # ---------- helpers ----------

    @staticmethod
    def _parse_dates(product: dict) -> dict:
        """Convert ISO date strings into datetime objects."""
        product = dict(product)  # don't mutate the caller's data
        product["updated_on"] = datetime.strptime(product["updated_on"], "%Y-%m-%d")
        product["evidence"] = [
            {**ev, "checked_on": datetime.strptime(ev["checked_on"], "%Y-%m-%d")}
            for ev in product.get("evidence", [])
        ]
        return product

    # ---------- setup ----------

    def create_indexes(self) -> None:
        self.collection.create_index([("brand", ASCENDING)])
        self.collection.create_index([("feature_tags", ASCENDING)])
        self.collection.create_index([("price_usd", ASCENDING)])
        self.collection.create_index([("type", ASCENDING), ("connection", ASCENDING)])
        self.collection.create_index([("evidence.supported_attribute", ASCENDING)])
        self.collection.create_index([("evidence.checked_on", ASCENDING)])

    # ---------- create / update ----------
    def upsert_product(self, product: dict) -> bool:
        """Insert or update one product. Returns True if a new document was created."""
        doc = self._parse_dates(product)
        result = self.collection.update_one(
            {"_id": doc["product_id"]}, {"$set": doc}, upsert=True
        )
        return result.upserted_id is not None

    def upsert_many(self, products: list[dict]) -> dict[str, int]:
        """Bulk upsert. Returns counts of inserted and modified documents."""
        if not products:
            return {"inserted": 0, "modified": 0}
        ops = []
        for p in products:
            doc = self._parse_dates(p)
            ops.append(UpdateOne({"_id": doc["product_id"]}, {"$set": doc}, upsert=True))
        result = self.collection.bulk_write(ops)
        return {"inserted": result.upserted_count, "modified": result.modified_count}

    def load_from_json(self, path: str) -> dict[str, int]:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return self.upsert_many(data["products"])

    # ---------- read ----------

    def get_product(self, product_id: str) -> Optional[dict]:
        return self.collection.find_one({"_id": product_id})

    def search_products(
        self,
        brand: Optional[str] = None,
        type_: Optional[str] = None,
        connection: Optional[str] = None,
        max_price: Optional[float] = None,
        feature_tag: Optional[str] = None,
    ) -> list[dict]:
        query: dict[str, Any] = {}
        if brand:
            query["brand"] = brand
        if type_:
            query["type"] = type_
        if connection:
            query["connection"] = connection
        if max_price is not None:
            query["price_usd"] = {"$lte": max_price}
        if feature_tag:
            query["feature_tags"] = feature_tag
        return list(self.collection.find(query).sort("price_usd", ASCENDING))

    def get_evidence(
        self, product_id: str, supported_attribute: Optional[str] = None
    ) -> list[dict]:
        product = self.get_product(product_id)
        if not product:
            return []
        evidence = product.get("evidence", [])
        if supported_attribute:
            evidence = [e for e in evidence if e["supported_attribute"] == supported_attribute]
        return evidence

    def find_stale_evidence(self, before: datetime) -> list[dict]:
        """Return products with any evidence last checked before the given date."""
        pipeline = [
            {"$match": {"evidence.checked_on": {"$lt": before}}},
            {
                "$project": {
                    "name": 1,
                    "stale_evidence": {
                        "$filter": {
                            "input": "$evidence",
                            "as": "ev",
                            "cond": {"$lt": ["$$ev.checked_on", before]},
                        }
                    },
                }
            },
        ]
        return list(self.collection.aggregate(pipeline))

    # ---------- delete ----------

    def delete_product(self, product_id: str) -> bool:
        return self.collection.delete_one({"_id": product_id}).deleted_count == 1


def process_catalog_to_new_sql_database():
    try:
        with ProductDatabase() as db:
            db.create_indexes()

            counts = db.load_from_json("sample_test_catalog.json")
            print(f"Load complete: {counts}")

            print("\nWireless over-ear under $150 with noise cancelling:")
            for p in db.search_products(
                type_="OVER_EAR",
                connection="WIRELESS",
                max_price=150,
                feature_tag="noise cancelling",
            ):
                print(f"  {p['product_id']}: {p['name']} (${p['price_usd']})")

            print("\nEvidence for hp-001 battery:")
            for ev in db.get_evidence("hp-001", "long battery"):
                print(f"  {ev['evidence_id']}: {ev['factual_claim']}")

            print("\nStale evidence (checked before 2026-06-01):")
            for p in db.find_stale_evidence(datetime(2026, 6, 1)):
                for ev in p["stale_evidence"]:
                    print(f"  {p['name']}: {ev['evidence_id']} checked {ev['checked_on']:%Y-%m-%d}")

    except PyMongoError as e:
        print(f"Database error: {e}")


if __name__ == "__main__":
    # process_catalog_to_new_sql_database()
    with ProductDatabase() as db:
        for p in db.search_products():
            print(p)

