"""The records: one SQLite file in the data directory.

Python's own sqlite3, nothing else. The schema grows only by migrations that
keep existing rows (CLAUDE.md "Records"): each entry in MIGRATIONS runs once,
in order, and the number reached is kept in the file itself.

Nothing people entered is ever deleted or overwritten by the application: a
correction is a new row in `corrections`, a check a new row in `checks`, a
changed supervisor a new row in `requests` that marks the earlier one
replaced. Two things are not among them (CLAUDE.md "Protect and verify"). A
generated report: staff may delete one, which removes its rows in `reports`
and `report_students`, and a row in `report_deletions` keeps who deleted
which report and when (constitution 5.14). And an application staff remove:
it waits in the bin (`binned_at`), and a second step deletes it with every
row recorded with it; rows in `bin_events` keep who removed, put back and
deleted which application, when and why, without the student's data
(constitution 5.15).
"""

import fcntl
import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone

# Version 1: everything milestone 1 needs.
MIGRATIONS = [
    """
    CREATE TABLE applications (
        id INTEGER PRIMARY KEY,
        email TEXT NOT NULL,
        email_key TEXT NOT NULL UNIQUE,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        submitted_at TEXT,
        grad_type TEXT,                 -- 'thesis' or 'exam'
        name1 TEXT NOT NULL DEFAULT '', -- собствено име
        name2 TEXT NOT NULL DEFAULT '', -- бащино име
        name3 TEXT NOT NULL DEFAULT '', -- фамилия
        fn TEXT NOT NULL DEFAULT '',
        phone TEXT NOT NULL DEFAULT '',
        programme TEXT NOT NULL DEFAULT '',     -- code in programmes list
        topic TEXT NOT NULL DEFAULT '',
        average_grade TEXT NOT NULL DEFAULT '',
        professor TEXT NOT NULL DEFAULT '',     -- code in professors list
        sup_name TEXT NOT NULL DEFAULT '',      -- typed, from outside
        sup_title TEXT NOT NULL DEFAULT '',     -- from the titles list
        sup_email TEXT NOT NULL DEFAULT '',     -- typed, from outside
        rationale TEXT NOT NULL DEFAULT '',     -- обосновка на темата
        aims TEXT NOT NULL DEFAULT '',          -- цели и задачи
        object_subject TEXT NOT NULL DEFAULT '',-- обект и предмет
        methodology TEXT NOT NULL DEFAULT '',   -- методологична база
        information_base TEXT NOT NULL DEFAULT '', -- информационна база
        plan TEXT NOT NULL DEFAULT '',          -- примерен план-съдържание
        schedule TEXT NOT NULL DEFAULT ''       -- времеви график
    );
    CREATE TABLE corrections (
        id INTEGER PRIMARY KEY,
        application_id INTEGER NOT NULL REFERENCES applications(id),
        field TEXT NOT NULL,
        old_value TEXT NOT NULL,
        new_value TEXT NOT NULL,
        by_account INTEGER NOT NULL REFERENCES accounts(id),
        at TEXT NOT NULL
    );
    CREATE TABLE checks (
        id INTEGER PRIMARY KEY,
        application_id INTEGER NOT NULL REFERENCES applications(id),
        result TEXT NOT NULL,           -- 'passed' or 'not_passed'
        note TEXT NOT NULL DEFAULT '',
        by_account INTEGER NOT NULL REFERENCES accounts(id),
        at TEXT NOT NULL
    );
    CREATE TABLE requests (
        id INTEGER PRIMARY KEY,
        application_id INTEGER NOT NULL REFERENCES applications(id),
        created_at TEXT NOT NULL,
        professor TEXT NOT NULL DEFAULT '',
        sup_name TEXT NOT NULL DEFAULT '',
        sup_title TEXT NOT NULL DEFAULT '',
        sup_email TEXT NOT NULL,
        token_hash TEXT NOT NULL UNIQUE,
        sent_at TEXT,                   -- when the relay accepted it
        replaced_at TEXT,
        answer TEXT,                    -- 'confirm' or 'decline'
        comment TEXT NOT NULL DEFAULT '',
        answered_at TEXT,
        reminders_sent INTEGER NOT NULL DEFAULT 0,
        last_mailed_at TEXT             -- the request or its latest reminder
    );
    CREATE TABLE accounts (
        id INTEGER PRIMARY KEY,
        username TEXT NOT NULL,
        username_key TEXT NOT NULL UNIQUE,
        email TEXT NOT NULL,
        email_key TEXT NOT NULL UNIQUE,
        algorithm TEXT NOT NULL,
        salt TEXT NOT NULL,
        iterations INTEGER NOT NULL,
        dklen INTEGER NOT NULL,
        hash TEXT NOT NULL,
        session_tag TEXT NOT NULL,
        created_at TEXT NOT NULL,
        approved_at TEXT,
        approved_by INTEGER
    );
    CREATE TABLE password_changes (
        id INTEGER PRIMARY KEY,
        account_id INTEGER NOT NULL REFERENCES accounts(id),
        by TEXT NOT NULL,               -- 'owner page', 'host command'
        at TEXT NOT NULL
    );
    CREATE TABLE signins (
        id INTEGER PRIMARY KEY,
        email TEXT NOT NULL,
        email_key TEXT NOT NULL,
        code_salt TEXT NOT NULL,
        code_hash TEXT,
        link_hash TEXT UNIQUE,
        attempts INTEGER NOT NULL DEFAULT 0,
        created_at TEXT NOT NULL,
        expires_at TEXT NOT NULL,
        used_at TEXT
    );
    CREATE TABLE attempts (
        id INTEGER PRIMARY KEY,
        bucket TEXT NOT NULL,
        at TEXT NOT NULL
    );
    CREATE INDEX attempts_bucket ON attempts(bucket, at);
    CREATE TABLE reports (
        id INTEGER PRIMARY KEY,
        programme TEXT NOT NULL,
        faculty TEXT NOT NULL,
        generated_at TEXT NOT NULL,
        generated_by INTEGER NOT NULL REFERENCES accounts(id),
        filename TEXT NOT NULL
    );
    CREATE TABLE report_students (
        report_id INTEGER NOT NULL REFERENCES reports(id),
        position INTEGER NOT NULL,
        application_id INTEGER NOT NULL REFERENCES applications(id),
        fn TEXT NOT NULL,
        name TEXT NOT NULL,
        topic TEXT NOT NULL,
        supervisor TEXT NOT NULL,
        PRIMARY KEY (report_id, position)
    );
    """,
    # Version 2: what the installation has done once, kept with the records,
    # so a lists folder deleted later is never mistaken for a first start.
    """
    CREATE TABLE installation (
        key TEXT PRIMARY KEY,
        value TEXT NOT NULL
    );
    """,
    # Version 3: the task of 13 October 2026. The student's declaration that
    # the credits are covered, ticked in the draft and recorded with when at
    # submission; an application submitted before it holds none. And the log
    # of deleted reports: the report's id is a plain number, not a foreign
    # key, because its row is gone.
    """
    ALTER TABLE applications ADD COLUMN credits_declared INTEGER NOT NULL
        DEFAULT 0;
    ALTER TABLE applications ADD COLUMN credits_declared_at TEXT;
    CREATE TABLE report_deletions (
        id INTEGER PRIMARY KEY,
        report_id INTEGER NOT NULL,
        programme TEXT NOT NULL,
        generated_at TEXT NOT NULL,
        students INTEGER NOT NULL,
        filename TEXT NOT NULL,
        deleted_by INTEGER NOT NULL REFERENCES accounts(id),
        deleted_at TEXT NOT NULL
    );
    """,
    # Version 4: the task of 15 October 2026. An application staff remove
    # waits in the bin: when, by whom, why ('graduated' or 'other') and an
    # optional note, all cleared when it is put back. Each removal, putting
    # back and deletion is a row in `bin_events`, whose application id is a
    # plain number, not a foreign key, because a deleted application's row
    # is gone; it holds no student data, so it may outlive the application.
    """
    ALTER TABLE applications ADD COLUMN binned_at TEXT;
    ALTER TABLE applications ADD COLUMN binned_by INTEGER
        REFERENCES accounts(id);
    ALTER TABLE applications ADD COLUMN bin_reason TEXT;
    ALTER TABLE applications ADD COLUMN bin_note TEXT NOT NULL DEFAULT '';
    CREATE TABLE bin_events (
        id INTEGER PRIMARY KEY,
        application_id INTEGER NOT NULL,
        event TEXT NOT NULL,            -- 'removed', 'restored', 'deleted'
        reason TEXT NOT NULL,           -- 'graduated' or 'other'
        by_account INTEGER NOT NULL REFERENCES accounts(id),
        at TEXT NOT NULL
    );
    """,
]

APPLICATION_TEXT_FIELDS = (
    "name1", "name2", "name3", "fn", "phone", "programme", "topic",
    "average_grade", "professor", "sup_name", "sup_title", "sup_email",
    "rationale", "aims", "object_subject", "methodology", "information_base",
    "plan", "schedule",
)

PROPOSAL_FIELDS = ("rationale", "aims", "object_subject", "methodology",
                   "information_base", "plan", "schedule")


def _system_now():
    return datetime.now(timezone.utc)


_clock = _system_now


def set_clock(fn):
    """Tests replace the clock; everything that reads time reads it here."""
    global _clock
    _clock = fn or _system_now


def now_dt():
    return _clock()


def now():
    """The current moment as stored: UTC, ISO 8601, to the second."""
    return _clock().astimezone(timezone.utc).isoformat(timespec="seconds")


def parse(stamp):
    return datetime.fromisoformat(stamp)


# Dates people read are Sofia's, not UTC: a submission at 00:30 in Sofia is
# that day's, though UTC still says yesterday.
try:
    from zoneinfo import ZoneInfo
    LOCAL_ZONE = ZoneInfo("Europe/Sofia")
except Exception:                       # no time-zone data on this machine
    LOCAL_ZONE = timezone.utc


def local_date(stamp):
    """A stored moment as the date people read: DD.MM.YYYY, Sofia time."""
    if not stamp:
        return ""
    return parse(stamp).astimezone(LOCAL_ZONE).strftime("%d.%m.%Y")


def local_datetime(stamp):
    """A stored moment as DD.MM.YYYY HH:MM, Sofia time."""
    if not stamp:
        return ""
    return parse(stamp).astimezone(LOCAL_ZONE).strftime("%d.%m.%Y %H:%M")


def local_day(stamp):
    """A stored moment's calendar date in Sofia, as a date to count with."""
    return parse(stamp).astimezone(LOCAL_ZONE).date()


def connect(path):
    """One connection, rows readable by column name, foreign keys on."""
    connection = sqlite3.connect(str(path), timeout=30,
                                 isolation_level=None)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


@contextmanager
def transaction(connection):
    """BEGIN IMMEDIATE ... COMMIT, rolled back on any error."""
    connection.execute("BEGIN IMMEDIATE")
    try:
        yield connection
    except BaseException:
        connection.execute("ROLLBACK")
        raise
    else:
        connection.execute("COMMIT")


def migrate(path):
    """Bring the file at path up to the latest schema, keeping every row.

    On the host the service, the reminder timer and the nightly copy's timer
    are separate processes that may start together on a database not yet
    migrated. Each holds an
    exclusive lock on a file beside the database ("<database>.migrate.lock")
    while it reads the version and applies the steps, so the second waits
    and then finds the schema already at the latest version, instead of
    applying the same step again ("table already exists"). The lock file is
    left in place: removing it would let a third process lock a new file
    while the second still holds the old one.
    """
    lock_path = str(path) + ".migrate.lock"
    descriptor = os.open(lock_path, os.O_RDWR | os.O_CREAT, 0o600)
    try:
        fcntl.flock(descriptor, fcntl.LOCK_EX)
        connection = connect(path)
        try:
            version = connection.execute("PRAGMA user_version").fetchone()[0]
            for number, script in enumerate(MIGRATIONS, start=1):
                if number <= version:
                    continue
                # A file already at schema 1 was made by a start that wrote
                # the starting lists: it is an installation, never a first
                # start, so lists missing from it must stop the start, not be
                # recreated.
                known = ("INSERT INTO installation (key, value) VALUES "
                         "('lists', '" + now() + "');"
                         ) if number == 2 and version >= 1 else ""
                connection.executescript("BEGIN IMMEDIATE;" + script + ";"
                                         + known + "PRAGMA user_version = "
                                         + str(number) + ";COMMIT;")
        finally:
            connection.close()
    finally:
        # Closing the descriptor releases the lock.
        os.close(descriptor)
