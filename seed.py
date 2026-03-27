import json
import os
from pymongo import MongoClient, TEXT, ASCENDING

MONGO_URI = os.environ.get("MONGO_URI", "mongodb://localhost:27017/musiccatalog")
DATA_FILE = os.path.join(os.path.dirname(__file__), "tracks.json")


def seed():
    client = MongoClient(MONGO_URI)

    # Parse the database name from the URI instead of hardcoding it so this
    # script stays consistent with whatever URI the caller passes in.
    db_name = MONGO_URI.rstrip("/").split("/")[-1] or "musiccatalog"
    db = client[db_name]
    collection = db["tracks"]

    print(f"Connected to {MONGO_URI}")

    # Drop first to make this fully idempotent: safe to run repeatedly.
    collection.drop()
    print("Dropped existing 'tracks' collection.")

    with open(DATA_FILE) as f:
        tracks = [json.loads(line) for line in f if line.strip()]

    collection.insert_many(tracks)
    print(f"Inserted {len(tracks)} tracks.")

    # Text index enables full-text search across artist and title fields.
    collection.create_index([("artist", TEXT), ("title", TEXT)], name="text_search")
    # These support filtered queries and sorting by level or genre.
    collection.create_index([("level", ASCENDING)], name="idx_level")
    collection.create_index([("genre", ASCENDING)], name="idx_genre")

    print("Indexes created: text_search, idx_level, idx_genre")
    print("Seeding complete.")


if __name__ == "__main__":
    seed()
