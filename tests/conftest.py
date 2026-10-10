"""Shared fixtures: a fresh data directory with invented people, a fake mail
relay that records every message and never sends, a settable clock, and
helpers that write records straight into the database.

Nobody here is real: the professors, students and staff are invented
(CLAUDE.md "Data in the repository").

Every test runs isolated from the machine it runs on (isolated_settings):
no SUPERASSISTANT_* variable from the shell, no settings file from the clone,
and no real relay, so neither a developer's nor the host's own settings can
decide a test or make it send a message.
"""

import email
import os
import secrets
from datetime import datetime, timedelta, timezone

import pytest

from superassistant import accounts, db, lists, mail
from superassistant import settings as settings_module
from superassistant.settings import Settings
from superassistant.web import create_app

OWNER_EMAIL = "owner@example.org"


def _never_send(settings, envelope):
    raise mail.MailFailed("tests never use the real relay; use the outbox "
                          "fixture")


@pytest.fixture(autouse=True)
def isolated_settings(monkeypatch, tmp_path_factory):
    """Every test: no SUPERASSISTANT_* variable from the shell, the settings
    file pointed at one that does not exist, and a relay that refuses unless
    the test installs the fake one (outbox). Afterwards any SUPERASSISTANT_*
    variable a test's own settings file left behind is removed."""
    for name in list(os.environ):
        if name.startswith(settings_module.PREFIX):
            monkeypatch.delenv(name)
    monkeypatch.setattr(settings_module, "SETTINGS_FILE",
                        tmp_path_factory.getbasetemp() / "no-settings-file"
                        / ".env.production")
    mail.set_relay(_never_send)
    yield
    mail.set_relay(None)
    for name in list(os.environ):
        if name.startswith(settings_module.PREFIX):
            del os.environ[name]


INVENTED_PROFESSORS = [
    ["ivanov", "доц. д-р", "Петър Иванов", "p.ivanov@example.org"],
    ["georgieva", "проф. д-р", "Елена Георгиева", "e.georgieva@example.org"],
    ["dimitrov", "гл. ас. д-р", "Стоян Димитров", "s.dimitrov@example.org"],
]


def write_professors(lists_dir, rows=None):
    import csv
    import io
    buffer = io.StringIO()
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(lists.HEADERS[lists.PROFESSORS])
    for row in (INVENTED_PROFESSORS if rows is None else rows):
        writer.writerow(row)
    (lists_dir / lists.PROFESSORS).write_text(buffer.getvalue(),
                                              encoding="utf-8")


def make_settings(data_dir, **overrides):
    values = dict(data_dir=data_dir, mail_mode="owner",
                  owner_email=OWNER_EMAIL, base_url="http://127.0.0.1:5002",
                  secret_key="test-secret")
    values.update(overrides)
    return Settings(**values)


def prepare_data_dir(data_dir):
    """A migrated database and the starter lists, with invented professors."""
    data_dir.mkdir(parents=True, exist_ok=True)
    db.migrate(data_dir / "superassistant.sqlite3")
    lists.write_starter(data_dir / "lists")
    write_professors(data_dir / "lists")


class Clock(object):
    """A clock tests move by hand."""

    def __init__(self):
        self.moment = datetime(2026, 10, 12, 9, 0, 0, tzinfo=timezone.utc)

    def __call__(self):
        return self.moment

    def advance(self, **kwargs):
        self.moment = self.moment + timedelta(**kwargs)


@pytest.fixture
def clock():
    c = Clock()
    db.set_clock(c)
    yield c
    db.set_clock(None)


class Outbox(object):
    """The fake relay: keeps every message handed to it; can refuse."""

    def __init__(self):
        self.messages = []
        self.refuse = False

    def __call__(self, settings, envelope):
        if self.refuse:
            raise mail.MailFailed("the fake relay refused the message")
        self.messages.append(Sent(envelope))

    def to(self, address):
        return [m for m in self.messages if m.intended == address]

    def clear(self):
        del self.messages[:]


class Sent(object):
    """One message as the fake relay received it."""

    def __init__(self, envelope):
        self.envelope = envelope
        self.envelope_to = envelope["To"]
        self.subject = envelope["Subject"]
        # Serialized as smtplib's send_message serializes it: with the utf8
        # policy (SMTPUTF8) when an address is not ASCII, as a student's
        # typed address in mode "send" can be; the default policy cannot
        # fold such an address and raises. smtplib does so only with a
        # relay that offers SMTPUTF8; the pilot's does (smtp.resend.com's
        # EHLO on port 587 listed smtputf8 on 10 October 2026), so this fake
        # is that relay.
        addresses = str(envelope["From"]) + str(envelope["To"])
        international = any(ord(ch) > 127 for ch in addresses)
        policy = envelope.policy.clone(utf8=True) if international else None
        parsed = email.message_from_bytes(envelope.as_bytes(policy=policy))
        self.text = ""
        self.html = ""
        for part in parsed.walk():
            if part.get_content_type() == "text/plain":
                self.text = part.get_payload(decode=True).decode("utf-8")
            elif part.get_content_type() == "text/html":
                self.html = part.get_payload(decode=True).decode("utf-8")
        first = self.text.splitlines()[0] if self.text else ""
        marker = "предназначено за: "
        self.intended = first.split(marker, 1)[1].strip() if marker in first \
            else ""


@pytest.fixture
def outbox():
    box = Outbox()
    mail.set_relay(box)
    yield box
    mail.set_relay(None)


@pytest.fixture
def data_dir(tmp_path):
    path = tmp_path / "data"
    prepare_data_dir(path)
    return path


@pytest.fixture
def settings(data_dir):
    return make_settings(data_dir)


@pytest.fixture
def app(settings, outbox, clock):
    application = create_app(settings)
    application.config["TESTING"] = True
    return application


class Client(object):
    """Flask's test client, with the form token every POST must carry."""

    def __init__(self, flask_client):
        self.raw = flask_client
        self.token = secrets.token_hex(8)
        with flask_client.session_transaction() as session:
            session["csrf"] = self.token

    def get(self, *args, **kwargs):
        return self.raw.get(*args, **kwargs)

    def post(self, url, data=None, **kwargs):
        data = dict(data or {})
        data.setdefault("csrf", self.current_token())
        return self.raw.post(url, data=data, **kwargs)

    def current_token(self):
        with self.raw.session_transaction() as session:
            if not session.get("csrf"):
                session["csrf"] = self.token
            return session["csrf"]


@pytest.fixture
def client(app):
    return Client(app.test_client())


@pytest.fixture
def new_client(app):
    """Another browser: a separate cookie jar."""
    return lambda: Client(app.test_client())


def connect(settings):
    return db.connect(settings.db_path)


def make_account(settings, username="staff1", email_address=None,
                 password="парола-123", approved=True):
    connection = connect(settings)
    try:
        record = accounts.create(connection, username,
                                 email_address or username + "@example.org",
                                 password)
        if approved:
            accounts.approve(connection, record["id"], record["id"])
        return accounts.get(connection, record["id"])
    finally:
        connection.close()


# --- Records written straight into the database ----------------------------
# For tests of rules that read the records (reports, documents, tables).
# They follow the schema in superassistant/db.py and nothing else.

def insert_application(settings, email_address, submitted=True, **fields):
    """One application; fields are columns of `applications`."""
    connection = connect(settings)
    try:
        stamp = db.now()
        columns = {"email": email_address,
                   "email_key": email_address.strip().casefold(),
                   "created_at": stamp, "updated_at": stamp,
                   "submitted_at": stamp if submitted else None}
        columns.update(fields)
        names = ", ".join(columns)
        marks = ", ".join("?" for _ in columns)
        with db.transaction(connection):
            cursor = connection.execute(
                "INSERT INTO applications (" + names + ") VALUES (" + marks
                + ")", list(columns.values()))
        return cursor.lastrowid
    finally:
        connection.close()


def insert_request(settings, application_id, answer=None, replaced=False,
                   sup_email="p.ivanov@example.org", professor="ivanov"):
    """One request to a supervisor, answered or not, current or replaced."""
    connection = connect(settings)
    try:
        stamp = db.now()
        with db.transaction(connection):
            cursor = connection.execute(
                "INSERT INTO requests (application_id, created_at, professor, "
                "sup_email, token_hash, sent_at, replaced_at, answer, "
                "answered_at, last_mailed_at) VALUES (?,?,?,?,?,?,?,?,?,?)",
                (application_id, stamp, professor, sup_email,
                 secrets.token_hex(32), stamp, stamp if replaced else None,
                 answer, stamp if answer else None, stamp))
        return cursor.lastrowid
    finally:
        connection.close()


def insert_check(settings, application_id, result, by_account, note=""):
    """One staff check: result is 'passed' or 'not_passed'."""
    connection = connect(settings)
    try:
        with db.transaction(connection):
            connection.execute(
                "INSERT INTO checks (application_id, result, note, "
                "by_account, at) VALUES (?,?,?,?,?)",
                (application_id, result, note, by_account, db.now()))
    finally:
        connection.close()
