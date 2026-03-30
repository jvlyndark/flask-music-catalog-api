import pytest

from app import create_app


@pytest.fixture()
def client():
    app = create_app("testing")
    yield app.test_client()
    app.db.client.drop_database(app.db.name)


def test_health_returns_healthy(client):
    resp = client.get("/health")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["status"] == "healthy"
    assert isinstance(data["db_latency_ms"], float)
    assert data["db_latency_ms"] > 0


def test_health_response_shape(client):
    resp = client.get("/health")
    data = resp.get_json()
    assert set(data.keys()) == {"status", "db_latency_ms"}
