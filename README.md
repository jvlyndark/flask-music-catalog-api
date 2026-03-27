# flask-music-catalog-api

Production-grade Flask + MongoDB REST API for browsing, searching, and rating music tracks.

## Quick Start

Prerequisites: Docker and Docker Compose.

```bash
git clone https://github.com/jvlyndark/flask-music-catalog-api.git && cd flask-music-catalog-api
docker-compose up -d --build
docker-compose exec app python seed.py
```

API is now running at http://localhost:8000

## API Reference

| Method | Endpoint | Description | Key Params |
|--------|----------|-------------|------------|
| GET | `/tracks` | List tracks with cursor pagination | `per_page` (default 10, max 100), `after` (cursor) |
| GET | `/tracks/avg/difficulty` | Average difficulty across tracks | `level` (optional filter) |
| GET | `/tracks/search` | Full-text search on artist and title | `q` (required), `per_page`, `after` |
| POST | `/tracks/rating` | Submit a rating for a track | Body: `track_id`, `rating` (1-5) |
| GET | `/tracks/<track_id>/rating` | Rating statistics for a track | None |

## Running Tests

```bash
docker-compose exec -e PYTHONPATH=/app -e MONGO_URI_TEST=mongodb://mongo:27017/musiccatalog_test app pytest tests/ -v
```

Or via the Makefile (requires the stack to be running):

```bash
make test
```

## Design Decisions

**Cursor-based pagination over offset.** Offset pagination degrades as page depth increases because MongoDB must scan and skip all preceding rows. Cursor pagination on `_id` uses the default index, keeping every page O(log n) with stable results during concurrent inserts.

**Aggregation pipelines over computing in Python.** Operations like averages, min, and max run on the MongoDB server and return a single result. Pulling all matching documents into Python to compute the same value transfers O(n) documents over the wire unnecessarily.

**Separate ratings collection over embedding.** Embedding ratings in track documents creates an unbounded array that grows with every rating, eventually hitting the 16MB BSON document limit. A separate collection also supports independent queries and aggregation without loading full track documents.

**Pydantic for validation and response shaping.** Pydantic models define explicit contracts for both input validation and output serialization. Invalid requests fail with structured error messages before reaching the database layer.

**Null for absent data instead of 0.** Zero is a valid value (a track could have a 0.0 difficulty or a zero-star rating in another system). Null communicates "no data exists," which is semantically different from "the value is zero."

## Tech Stack

- Python 3.11, Flask, gunicorn
- MongoDB 7.0, pymongo
- Pydantic v2
- pytest
- Docker, Docker Compose
