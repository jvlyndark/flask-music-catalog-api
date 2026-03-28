import time

from flask import Blueprint, Flask, Response, g, request
from prometheus_client import Counter, Histogram, generate_latest

from .limiter import limiter

http_requests_total = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status"],
)

http_request_duration_seconds = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint"],
)

# Endpoints that are infrastructure, not application traffic. Tracking these
# would dominate the counts since monitoring tools poll them constantly.
_EXCLUDED_ENDPOINTS = frozenset({"health.health_check", "metrics.metrics"})

metrics_bp = Blueprint("metrics", __name__)


@metrics_bp.get("/metrics")
@limiter.exempt
def metrics():
    return Response(generate_latest(), content_type="text/plain; charset=utf-8")


def register_metrics(app: Flask):
    @app.before_request
    def start_timer():
        g.metrics_start = time.monotonic()

    @app.after_request
    def record_metrics(response):
        endpoint = request.endpoint or "unknown"
        if endpoint in _EXCLUDED_ENDPOINTS:
            return response

        elapsed = time.monotonic() - g.metrics_start
        http_request_duration_seconds.labels(
            method=request.method,
            endpoint=endpoint,
        ).observe(elapsed)
        http_requests_total.labels(
            method=request.method,
            endpoint=endpoint,
            status=response.status_code,
        ).inc()

        return response
