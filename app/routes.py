from datetime import datetime

from bson import ObjectId
from bson.errors import InvalidId
from flask import Blueprint, abort, current_app, jsonify, request
from pydantic import ValidationError

from .models import (
    AverageDifficultyResponse,
    PaginatedResponse,
    RatingInput,
    RatingResponse,
    TrackResponse,
)

tracks_bp = Blueprint("tracks", __name__, url_prefix="/tracks")


@tracks_bp.get("")
def list_tracks():
    # Cursor pagination on _id rather than offset/limit: skipping N rows gets
    # slower as N grows because MongoDB still scans the skipped rows. Cursoring
    # on _id keeps every page O(log n) via the default _id index and produces
    # stable results even when documents are inserted mid-traversal.
    raw_per_page = request.args.get("per_page", "10")
    try:
        per_page = int(raw_per_page)
    except ValueError:
        abort(400, f"per_page must be an integer, got: {raw_per_page!r}")

    if not (1 <= per_page <= 100):
        abort(400, "per_page must be between 1 and 100")

    query = {}
    after = request.args.get("after")
    if after:
        try:
            query["_id"] = {"$gt": ObjectId(after)}
        except InvalidId:
            abort(400, f"invalid cursor: {after!r}")

    collection = current_app.db["tracks"]
    # Fetch one extra document to know whether a next page exists without
    # running a separate count query.
    docs = list(collection.find(query).sort("_id", 1).limit(per_page + 1))

    has_next = len(docs) > per_page
    if has_next:
        docs = docs[:per_page]

    items = [TrackResponse.from_mongo(doc) for doc in docs]
    next_cursor = items[-1].id if has_next else None

    response = PaginatedResponse(items=items, per_page=per_page, next_cursor=next_cursor)
    return jsonify(response.model_dump()), 200


@tracks_bp.get("/avg/difficulty")
def avg_difficulty():
    # Aggregation pipeline vs fetching docs into Python: the pipeline runs the
    # average computation on the MongoDB server and returns a single number.
    # Pulling all matching docs into Python to compute the mean would transfer
    # O(n) documents over the wire for a result that is always one float.
    raw_level = request.args.get("level")
    level = None
    if raw_level is not None:
        try:
            level = int(raw_level)
        except ValueError:
            abort(400, f"level must be an integer, got: {raw_level!r}")

    pipeline = []
    if level is not None:
        pipeline.append({"$match": {"level": level}})
    pipeline.append({"$group": {"_id": None, "avg": {"$avg": "$difficulty"}}})

    collection = current_app.db["tracks"]
    results = list(collection.aggregate(pipeline))

    average = round(results[0]["avg"], 2) if results else None

    response = AverageDifficultyResponse(average_difficulty=average)
    return jsonify(response.model_dump()), 200


@tracks_bp.get("/search")
def search_tracks():
    # MongoDB text indexes tokenize on word boundaries (spaces, hyphens, etc.)
    # and match whole tokens. This means "cascade" matches "Cascade Protocol"
    # but "cascad" does not. True substring/prefix matching would require
    # $regex, which cannot use the text index and performs a collection scan.
    q = request.args.get("q", "").strip()
    if not q:
        abort(400, "q parameter is required")

    raw_per_page = request.args.get("per_page", "10")
    try:
        per_page = int(raw_per_page)
    except ValueError:
        abort(400, f"per_page must be an integer, got: {raw_per_page!r}")

    if not (1 <= per_page <= 100):
        abort(400, "per_page must be between 1 and 100")

    query = {"$text": {"$search": q}}
    after = request.args.get("after")
    if after:
        try:
            query["_id"] = {"$gt": ObjectId(after)}
        except InvalidId:
            abort(400, f"invalid cursor: {after!r}")

    collection = current_app.db["tracks"]
    docs = list(collection.find(query).sort("_id", 1).limit(per_page + 1))

    has_next = len(docs) > per_page
    if has_next:
        docs = docs[:per_page]

    items = [TrackResponse.from_mongo(doc) for doc in docs]
    next_cursor = items[-1].id if has_next else None

    response = PaginatedResponse(items=items, per_page=per_page, next_cursor=next_cursor)
    return jsonify(response.model_dump()), 200


@tracks_bp.post("/rating")
def add_rating():
    # Ratings live in a separate collection rather than embedded in the track
    # document. Embedding would create an unbounded array that grows with every
    # rating, bloating the track document and eventually hitting the 16MB BSON
    # limit. A separate collection also lets us query and aggregate ratings
    # independently without loading the full track.
    body = request.get_json(silent=True)
    if body is None:
        abort(400, "request body must be valid JSON")

    try:
        data = RatingInput.model_validate(body)
    except ValidationError as e:
        abort(400, e.errors())

    try:
        track_oid = ObjectId(data.track_id)
    except InvalidId:
        abort(404, "track not found")

    if current_app.db["tracks"].find_one({"_id": track_oid}) is None:
        abort(404, "track not found")

    rating_doc = {
        "track_id": track_oid,
        "rating": data.rating,
        "created_at": datetime.utcnow(),
    }
    result = current_app.db["ratings"].insert_one(rating_doc)
    rating_doc["_id"] = result.inserted_id

    response = RatingResponse.from_mongo(rating_doc)
    return jsonify(response.model_dump(mode="json")), 201
