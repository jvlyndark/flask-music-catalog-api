import pytest
from app import create_app


@pytest.fixture()
def client():
    app = create_app("testing")
    yield app.test_client()
    app.db.client.drop_database(app.db.name)


def test_rate_limit_headers_present(client):
    resp = client.get("/tracks")
    assert "X-RateLimit-Limit" in resp.headers
    assert "X-RateLimit-Remaining" in resp.headers


def test_health_exempt_from_rate_limit(client):
    resp = client.get("/health")
    assert "X-RateLimit-Limit" not in resp.headers
    assert "X-RateLimit-Remaining" not in resp.headers
