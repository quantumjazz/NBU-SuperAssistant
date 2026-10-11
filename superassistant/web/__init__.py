"""The Flask application: one factory, the start-up checks, and the blueprints.

create_app refuses to build an application the records or the lists would
make wrong (NOW.md, requirements 5 and 6): unknown settings, a list that
cannot be read or no longer holds an entry an application uses, or an owner
setting that names no account; and, for a hosted installation, settings that
would expose it or lose mail (Settings.problems). app.py and wsgi.py print the
reason and exit. A start that succeeds says on one line of standard error
what it resolved (startup_line), because on the host that is read through
journalctl.
"""

import hashlib
import ipaddress
import os
import secrets
import sys
from functools import wraps

from flask import Flask, abort, g, redirect, request, session

from superassistant import accounts, db, lists, mail, texts
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
    connection = db.connect(settings.db_path)
    try:
        # The starting lists are written once, on the first start, and that
        # start is recorded in the database, not read from the lists folder:
        # a list or the whole folder missing later is an error to report,
        # never one to quietly replace, as the owner may have changed every
        # entry since.
        with db.transaction(connection):
            first = connection.execute(
                "SELECT 1 FROM installation WHERE key = 'lists'"
            ).fetchone() is None
            if first:
                lists.write_starter(settings.lists_dir)
                connection.execute(
                    "INSERT INTO installation (key, value) VALUES "
                    "('lists', ?)", (db.now(),))
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
    # The unit writes no access log because sign-in links and supervisors'
    # answer pages carry their tokens in the address; Flask's own error log
    # would still write "Exception on <that address>" to the journal. It
    # names the route instead ("/link/<token>"), keeping the error itself.
    app.log_exception = _route_not_address(app)
    app.jinja_env.filters["date"] = db.local_date
    app.jinja_env.filters["datetime"] = db.local_datetime
    app.extensions["superassistant"] = {"settings": settings,
                                        "lists": loaded}
    version = style_version(app)

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
                "mail_note": mail_note(settings),
                "student": session_student(), "staff": session_staff(),
                "is_owner": is_owner(session_staff()),
                "style_version": version}

    from superassistant.web import (auth, documents, health, owner, staff,
                                    student, supervisor)
    for module in (auth, student, supervisor, staff, owner, documents,
                   health):
        app.register_blueprint(module.blueprint)
    sys.stderr.write(startup_line(settings) + "\n")
    sys.stderr.flush()
    return app


def _route_not_address(app):
    def log_exception(exc_info):
        rule = request.url_rule.rule if request.url_rule else "(no route)"
        app.logger.error("Exception on %s [%s]", rule, request.method,
                         exc_info=exc_info)
    return log_exception


def style_version(app):
    """A short hash of the stylesheet, for the ?v= on every page's link.

    Cloudflare tells browsers to keep /static/style.css for four hours
    (cache-control: max-age=14400 at the edge, although Flask sends
    no-cache), so after a deploy a browser could show the new pages with the
    old stylesheet. A stylesheet with other content gets another address.
    Read at start: the documented update restarts the service.
    """
    with open(os.path.join(app.static_folder, "style.css"), "rb") as handle:
        return hashlib.sha256(handle.read()).hexdigest()[:12]


def mail_note(settings):
    """The line every page shows in a development mail mode, or ""."""
    mode = settings.effective_mail_mode()
    if mode == "console":
        return texts.MAIL_DEV_CONSOLE
    if mode == "owner":
        return texts.MAIL_DEV_OWNER.format(settings.owner_email)
    return ""


def startup_line(settings):
    """What this start resolved, as one line for the log. Never a secret.

    The records folder, the address, the mail mode (with the relay and the
    sender when mail leaves) and where a visitor's address comes from. As
    CourseBench's hosting.describe: when a deploy behaves oddly, the first
    question is what the process resolved, not what someone believes is in
    the settings file. No password, key or username is among it.
    """
    mode = settings.effective_mail_mode()
    if mode == "send":
        how = ("send, to each intended recipient, through "
               + mail.relay_description(settings) + " from "
               + settings.mail_from)
    elif mode == "owner":
        how = ("owner, every message to " + settings.owner_email
               + ", through " + mail.relay_description(settings) + " from "
               + (settings.mail_from or "(SUPERASSISTANT_MAIL_FROM not set)"))
    else:
        how = ("console, printed and never sent"
               + ("" if settings.mail_mode else " (SUPERASSISTANT_MAIL_MODE "
                  "not set)"))
    if settings.client_ip_header:
        visitor = ("the " + settings.client_ip_header + " header, else the "
                   "connection")
    else:
        visitor = "the connection"
    return ("NBU-SuperAssistant started: records "
            + str(settings.data_dir.resolve())
            + "; address " + settings.base_url + "; mail " + how
            + "; visitor address from " + visitor + ".")


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
    """Who is asking, for rate limits.

    Unless SUPERASSISTANT_CLIENT_IP_HEADER names a header, the connection's
    own address, and never a forwarded header: any caller can set
    CF-Connecting-IP to a new value on every request and so never meet the
    per-source limit. On the host the tunnel connects from 127.0.0.1, so
    every visitor would share one source; there the setting names the header
    Cloudflare writes, and the first value in it is the visitor (copied from
    CourseBench's coursebench/web/app.py, _caller: a forwarding chain
    appends, and the first entry is the one nearest the visitor). Absent or
    empty, the connection again; either way an IPv6 address counts by its
    /64 (counted_as). The setting is safe only where every
    request comes through the tunnel; anywhere reachable directly, a caller
    could name a new source on every request.
    """
    header = settings().client_ip_header
    if header:
        stated = (request.headers.get(header) or "").split(",")[0].strip()
        if stated:
            return counted_as(stated)
    return counted_as(request.remote_addr or "")


def counted_as(address):
    """The source a limit counts for an address.

    An IPv6 visitor counts by its /64, the block a single machine is given
    and can pick addresses from at will, so it meets the same limit as an
    IPv4 visitor; an IPv4-mapped IPv6 address counts as its IPv4 address.
    Anything else, a name or a value that is no address, as written.
    """
    try:
        ip = ipaddress.ip_address(address)
        if ip.version == 6 and ip.ipv4_mapped is not None:
            return str(ip.ipv4_mapped)
        if ip.version == 6:
            return str(ipaddress.ip_network(address + "/64", strict=False))
    except ValueError:
        pass
    return address


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
