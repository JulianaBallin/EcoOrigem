"""WSGI entry points used by Gunicorn (``ecoorigem.wsgi:node_app()``)."""

from __future__ import annotations

from flask import Flask

from ecoorigem.bootstrap import build_node, build_web
from ecoorigem.config import Settings


def node_app() -> Flask:
    """Return the WSGI application of the blockchain node."""
    return build_node(Settings.from_env())[1]


def web_app() -> Flask:
    """Return the WSGI application of the web interface."""
    return build_web(Settings.from_env())
