"""Helpers shared by the node API and the web gateway."""

from __future__ import annotations

from flask import Flask, jsonify
from werkzeug.exceptions import HTTPException

from ecoorigem.errors import EcoOrigemError


def error_response(code: str, message: str, status: int):
    """Build the standard JSON error response."""
    return (
        jsonify({"status": "error", "error": {"code": code, "message": message}}),
        status,
    )


def register_error_handlers(app: Flask) -> None:
    """Return domain and HTTP errors as JSON with stable error codes."""

    @app.errorhandler(EcoOrigemError)
    def handle_domain_error(error: EcoOrigemError):
        body = {"status": "rejected", "error": error.to_dict()}
        return jsonify(body), error.http_status

    @app.errorhandler(HTTPException)
    def handle_http_error(error: HTTPException):
        code = error.name.upper().replace(" ", "_")
        return error_response(code, error.description or error.name, error.code or 500)
