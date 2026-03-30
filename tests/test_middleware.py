import uuid

import pytest

from app import create_app


@pytest.fixture()
def client():
    app = create_app("testing")
    yield app.test_client()
    app.db.client.drop_database(app.db.name)


def test_request_id_generated(client):
    resp = client.get("/health")
    assert "X-Request-ID" in resp.headers


def test_request_id_passthrough(client):
    resp = client.get("/health", headers={"X-Request-ID": "test-123"})
    assert resp.headers["X-Request-ID"] == "test-123"


def test_request_id_is_uuid_when_not_provided(client):
    resp = client.get("/health")
    value = resp.headers["X-Request-ID"]
    # Raises ValueError if not a valid UUID.
    parsed = uuid.UUID(value, version=4)
    assert str(parsed) == value
