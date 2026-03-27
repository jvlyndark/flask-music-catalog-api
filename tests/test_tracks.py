import pytest
from bson import ObjectId
from pymongo import TEXT, ASCENDING

from app import create_app


SAMPLE_TRACKS = [
    {
        "artist": "Alpha Band",
        "title": "First Light",
        "difficulty": 3.0,
        "level": 4,
        "genre": "rock",
        "bpm": 120,
        "released": "2020-01-15",
    },
    {
        "artist": "Alpha Band",
        "title": "Second Wave",
        "difficulty": 7.0,
        "level": 10,
        "genre": "electronic",
        "bpm": 140,
        "released": "2021-06-01",
    },
    {
        "artist": "Beta Crew",
        "title": "Night Drive",
        "difficulty": 5.0,
        "level": 4,
        "genre": "jazz",
        "bpm": 95,
        "released": "2019-11-20",
    },
    {
        "artist": "Gamma Ray",
        "title": "Solar Flare",
        "difficulty": 9.0,
        "level": 13,
        "genre": "electronic",
        "bpm": 160,
        "released": "2023-03-10",
    },
]

TRACK_RESPONSE_FIELDS = {"id", "artist", "title", "difficulty", "level", "genre", "bpm", "released"}


@pytest.fixture()
def client():
    app = create_app("testing")
    db = app.db

    # Recreate the same indexes that seed.py creates so text search works.
    db["tracks"].create_index([("artist", TEXT), ("title", TEXT)], name="text_search")
    db["tracks"].create_index([("level", ASCENDING)], name="idx_level")
    db["tracks"].create_index([("genre", ASCENDING)], name="idx_genre")

    yield app.test_client()

    app.db.client.drop_database(app.db.name)


def _seed_tracks(client, tracks):
    """Insert tracks into the test DB, return list of string IDs."""
    app = client.application
    result = app.db["tracks"].insert_many([dict(t) for t in tracks])
    return [str(oid) for oid in result.inserted_ids]


# GET /tracks

def test_list_tracks_returns_all(client):
    _seed_tracks(client, SAMPLE_TRACKS[:3])
    resp = client.get("/tracks")
    assert resp.status_code == 200
    data = resp.get_json()
    assert len(data["items"]) == 3
    for item in data["items"]:
        assert set(item.keys()) == TRACK_RESPONSE_FIELDS


def test_list_tracks_pagination(client):
    _seed_tracks(client, SAMPLE_TRACKS[:3])

    resp = client.get("/tracks?per_page=2")
    data = resp.get_json()
    assert len(data["items"]) == 2
    assert data["next_cursor"] is not None

    resp2 = client.get(f"/tracks?per_page=2&after={data['next_cursor']}")
    data2 = resp2.get_json()
    assert len(data2["items"]) == 1
    assert data2["next_cursor"] is None


def test_list_tracks_invalid_per_page(client):
    resp = client.get("/tracks?per_page=abc")
    assert resp.status_code == 400
    assert "error" in resp.get_json()


def test_list_tracks_empty(client):
    resp = client.get("/tracks")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["items"] == []
    assert data["next_cursor"] is None


# GET /tracks/avg/difficulty

def test_avg_difficulty_all(client):
    _seed_tracks(client, SAMPLE_TRACKS[:3])
    resp = client.get("/tracks/avg/difficulty")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["average_difficulty"] == 5.0  # (3.0 + 7.0 + 5.0) / 3


def test_avg_difficulty_with_level(client):
    _seed_tracks(client, SAMPLE_TRACKS[:3])
    # Level 4 has difficulties 3.0 and 5.0.
    resp = client.get("/tracks/avg/difficulty?level=4")
    assert resp.status_code == 200
    assert resp.get_json()["average_difficulty"] == 4.0


def test_avg_difficulty_no_match(client):
    _seed_tracks(client, SAMPLE_TRACKS[:3])
    resp = client.get("/tracks/avg/difficulty?level=99")
    assert resp.status_code == 200
    assert resp.get_json()["average_difficulty"] is None


def test_avg_difficulty_invalid_level(client):
    resp = client.get("/tracks/avg/difficulty?level=abc")
    assert resp.status_code == 400


# GET /tracks/search

def test_search_finds_by_artist(client):
    _seed_tracks(client, SAMPLE_TRACKS[:3])
    resp = client.get("/tracks/search?q=Beta")
    assert resp.status_code == 200
    items = resp.get_json()["items"]
    assert len(items) == 1
    assert items[0]["artist"] == "Beta Crew"


def test_search_finds_by_title(client):
    _seed_tracks(client, SAMPLE_TRACKS)
    resp = client.get("/tracks/search?q=Solar")
    assert resp.status_code == 200
    items = resp.get_json()["items"]
    assert len(items) == 1
    assert items[0]["title"] == "Solar Flare"


def test_search_case_insensitive(client):
    _seed_tracks(client, SAMPLE_TRACKS[:3])
    resp = client.get("/tracks/search?q=night")
    assert resp.status_code == 200
    items = resp.get_json()["items"]
    assert len(items) == 1
    assert items[0]["title"] == "Night Drive"


def test_search_no_results(client):
    _seed_tracks(client, SAMPLE_TRACKS[:3])
    resp = client.get("/tracks/search?q=zzzznothing")
    assert resp.status_code == 200
    assert resp.get_json()["items"] == []


def test_search_missing_q(client):
    resp = client.get("/tracks/search")
    assert resp.status_code == 400


def test_search_pagination(client):
    # All three tracks share the artist "Alpha Band", so searching "Alpha"
    # returns all of them and lets us test cursor pagination.
    alpha_tracks = [
        {**SAMPLE_TRACKS[0]},
        {**SAMPLE_TRACKS[1]},
        {**SAMPLE_TRACKS[0], "title": "Third Act"},
    ]
    _seed_tracks(client, alpha_tracks)

    resp = client.get("/tracks/search?q=Alpha&per_page=2")
    data = resp.get_json()
    assert len(data["items"]) == 2
    assert data["next_cursor"] is not None

    resp2 = client.get(f"/tracks/search?q=Alpha&per_page=2&after={data['next_cursor']}")
    data2 = resp2.get_json()
    assert len(data2["items"]) == 1
    assert data2["next_cursor"] is None


# POST /tracks/rating

def _post_rating(client, body):
    return client.post("/tracks/rating", json=body)


def test_add_rating_success(client):
    ids = _seed_tracks(client, SAMPLE_TRACKS[:1])
    resp = _post_rating(client, {"track_id": ids[0], "rating": 4.5})
    assert resp.status_code == 201
    data = resp.get_json()
    assert set(data.keys()) == {"id", "track_id", "rating", "created_at"}
    assert data["track_id"] == ids[0]
    assert data["rating"] == 4.5


def test_add_rating_accumulates(client):
    ids = _seed_tracks(client, SAMPLE_TRACKS[:1])
    resp1 = _post_rating(client, {"track_id": ids[0], "rating": 3.0})
    resp2 = _post_rating(client, {"track_id": ids[0], "rating": 5.0})
    assert resp1.status_code == 201
    assert resp2.status_code == 201
    assert resp1.get_json()["id"] != resp2.get_json()["id"]


def test_add_rating_below_range(client):
    ids = _seed_tracks(client, SAMPLE_TRACKS[:1])
    resp = _post_rating(client, {"track_id": ids[0], "rating": 0})
    assert resp.status_code == 400


def test_add_rating_above_range(client):
    ids = _seed_tracks(client, SAMPLE_TRACKS[:1])
    resp = _post_rating(client, {"track_id": ids[0], "rating": 6})
    assert resp.status_code == 400


def test_add_rating_not_a_number(client):
    ids = _seed_tracks(client, SAMPLE_TRACKS[:1])
    resp = _post_rating(client, {"track_id": ids[0], "rating": "great"})
    assert resp.status_code == 400


def test_add_rating_missing_track_id(client):
    resp = _post_rating(client, {"rating": 3})
    assert resp.status_code == 400


def test_add_rating_nonexistent_track(client):
    resp = _post_rating(client, {"track_id": str(ObjectId()), "rating": 3})
    assert resp.status_code == 404


def test_add_rating_invalid_objectid(client):
    resp = _post_rating(client, {"track_id": "not-an-id", "rating": 3})
    assert resp.status_code == 404


def test_add_rating_empty_body(client):
    resp = client.post("/tracks/rating")
    assert resp.status_code == 400


# GET /tracks/<track_id>/rating

def _add_ratings(client, track_id, ratings):
    for r in ratings:
        _post_rating(client, {"track_id": track_id, "rating": r})


def test_rating_stats_multiple(client):
    ids = _seed_tracks(client, SAMPLE_TRACKS[:1])
    _add_ratings(client, ids[0], [2.0, 4.0, 5.0])

    resp = client.get(f"/tracks/{ids[0]}/rating")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["average"] == 3.67  # round((2+4+5)/3, 2)
    assert data["min"] == 2.0
    assert data["max"] == 5.0


def test_rating_stats_single(client):
    ids = _seed_tracks(client, SAMPLE_TRACKS[:1])
    _add_ratings(client, ids[0], [3.5])

    resp = client.get(f"/tracks/{ids[0]}/rating")
    data = resp.get_json()
    assert data["average"] == 3.5
    assert data["min"] == 3.5
    assert data["max"] == 3.5


def test_rating_stats_no_ratings(client):
    ids = _seed_tracks(client, SAMPLE_TRACKS[:1])
    resp = client.get(f"/tracks/{ids[0]}/rating")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["average"] is None
    assert data["min"] is None
    assert data["max"] is None


def test_rating_stats_invalid_objectid(client):
    resp = client.get("/tracks/not-valid/rating")
    assert resp.status_code == 404


def test_rating_stats_nonexistent_track(client):
    resp = client.get(f"/tracks/{ObjectId()}/rating")
    assert resp.status_code == 404
