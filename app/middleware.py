import uuid

from flask import Flask, g, request


def register_middleware(app: Flask):
    @app.before_request
    def set_request_id():
        g.request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))

    @app.after_request
    def add_request_id_header(response):
        response.headers["X-Request-ID"] = g.request_id
        return response
