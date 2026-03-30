import pytest

from app import create_app


@pytest.fixture()
def client():
    app = create_app("testing")
    yield app.test_client()
    app.db.client.drop_database(app.db.name)


def test_metrics_endpoint_returns_prometheus_format(client):
    resp = client.get("/metrics")
    assert resp.status_code == 200
    body = resp.data.decode()
    assert "http_requests_total" in body


def test_metrics_tracks_requests(client):
    client.get("/tracks")
    resp = client.get("/metrics")
    body = resp.data.decode()
    assert 'endpoint="tracks.list_tracks"' in body


def test_metrics_excludes_health(client):
    client.get("/health")
    resp = client.get("/metrics")
    body = resp.data.decode()
    # Health endpoint should not appear as a labeled metric.
    assert 'endpoint="health.health_check"' not in body
