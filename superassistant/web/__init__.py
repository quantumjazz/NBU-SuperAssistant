"""The Flask application: one factory, the start-up checks, and the blueprints.

create_app refuses to build an application the records or the lists would
make wrong (NOW.md, requirements 5 and 6): unknown settings, a list that
cannot be read or no longer holds an entry an application uses, or an owner
setting that names no account. app.py prints the reason and exits.
"""

import secrets
from functools import wraps

from flask import Flask, abort, g, redirect, request, session

from superassistant import accounts, db, lists, texts
from superassistant.settings import from_env


class StartupError(Exception):
    """The service cannot start; the message says why."""


def _check_owner(settings, connection):
    if not settings.owner_username:
        return
    if accounts.by_username(connection, settings.owner_username) is None:
        raise StartupError(
            "SUPERASSISTANT_OWNER_USERNAME is " + repr(settings.owner_username)
            + ", but no account has that username. Register it first, then "
            "set the setting and start again.")


def prepare(settings):
    """Make the data directory ready and check it. Returns the lists."""
    problem = settings.problem()
    if problem:
        raise StartupError(problem)
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    settings.reports_dir.mkdir(parents=True, exist_ok=True)
    db.migrate(settings.db_path)
    lists.write_starter(settings.lists_dir)
    connection = db.connect(settings.db_path)
    try:
        try:
            loaded = lists.load(settings.lists_dir)
            lists.check_used(loaded, connection)
        except lists.ListError as exc:
            raise StartupError(str(exc))
        _check_owner(settings, connection)
    finally:
        connection.close()
    return loaded


def create_app(settings=None):
    """The application for these settings, or StartupError."""
    settings = settings or from_env()
    loaded = prepare(settings)
    app = Flask(__name__.rsplit(".", 1)[0], template_folder="pages",
                static_folder="static")
    app.config.update(
        SECRET_KEY=settings.ensure_secret_key(),
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_SECURE=settings.base_url.startswith("https://"),
        MAX_CONTENT_LENGTH=2 * 1024 * 1024,
    )
    app.extensions["superassistant"] = {"settings": settings,
                                        "lists": loaded}

    @app.before_request
    def _guard_posts():
        if request.method == "POST":
            sent = request.form.get("csrf") or ""
            expected = session.get("csrf") or ""
            if not expected or not secrets.compare_digest(sent, expected):
                abort(400, texts.CROSS_SITE)

    @app.teardown_appcontext
    def _close(exc):
        connection = g.pop("db", None)
        if connection is not None:
            connection.close()

    @app.context_processor
    def _globals():
        return {"t": texts, "csrf_token": csrf_token,
                "student": session_student(), "staff": session_staff(),
                "is_owner": is_owner(session_staff())}

    from superassistant.web import (auth, documents, owner, staff, student,
                                    supervisor)
    for module in (auth, student, supervisor, staff, owner, documents):
        app.register_blueprint(module.blueprint)
    return app


# --- What every page needs -------------------------------------------------

def settings():
    from flask import current_app
    return current_app.extensions["superassistant"]["settings"]


def current_lists():
    from flask import current_app
    return current_app.extensions["superassistant"]["lists"]


def connection():
    if "db" not in g:
        g.db = db.connect(settings().db_path)
    return g.db


def csrf_token():
    if not session.get("csrf"):
        session["csrf"] = secrets.token_hex(16)
    return session["csrf"]


def source():
    """Who is asking, for rate limits: the address the request came from."""
    return (request.headers.get("CF-Connecting-IP")
            or request.remote_addr or "")


def session_student():
    """The email key of the signed-in student, or None."""
    return session.get("student")


def session_staff():
    """The signed-in, approved staff account (owner included), or None."""
    account_id = session.get("staff")
    if not account_id:
        return None
    record = accounts.get(connection(), account_id)
    if record is None or not secrets.compare_digest(
            str(session.get("tag") or ""), record["session_tag"]):
        return None
    if not accounts.approved(record, settings()):
        return None
    return record


def is_owner(record):
    return record is not None and accounts.is_owner(record, settings())


def session_student_email():
    """The address the signed-in student typed, as typed."""
    return session.get("student_email")


def sign_in_student(email_key, email):
    keep = session.get("csrf")
    session.clear()
    session["student"] = email_key
    session["student_email"] = email
    session["csrf"] = keep or secrets.token_hex(16)
    session.permanent = True


def sign_in_staff(record):
    keep = session.get("csrf")
    session.clear()
    session["staff"] = record["id"]
    session["tag"] = record["session_tag"]
    session["csrf"] = keep or secrets.token_hex(16)
    session.permanent = True


def sign_out():
    session.clear()


# --- Who may see a page ----------------------------------------------------

def student_required(view):
    """A page for a signed-in student; anybody else goes to the sign-in page."""
    @wraps(view)
    def wrapped(*args, **kwargs):
        if session_student() is None:
            return redirect("/")
        return view(*args, **kwargs)
    return wrapped


def staff_required(view):
    """A page for an approved staff account (the owner's included)."""
    @wraps(view)
    def wrapped(*args, **kwargs):
        if session_staff() is None:
            return redirect("/staff/sign-in")
        return view(*args, **kwargs)
    return wrapped


def owner_required(view):
    """A page only the owner's account reaches."""
    @wraps(view)
    def wrapped(*args, **kwargs):
        record = session_staff()
        if record is None:
            return redirect("/staff/sign-in")
        if not is_owner(record):
            abort(403)
        return view(*args, **kwargs)
    return wrapped
