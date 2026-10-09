"""The host's entry point: gunicorn wsgi:app (listening on 127.0.0.1:8791)."""

from superassistant.web import create_app

app = create_app()
