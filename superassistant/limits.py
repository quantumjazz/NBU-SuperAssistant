"""How often a caller may make NBU-SuperAssistant send mail.

The pattern and the numbers are CourseBench's (`coursebench/signup.py`,
allow_mail): a limit per destination address and one per source, the source
claimed first so that a caller over the limit writes nothing. Buckets are
hashed, so the attempts table counts requests without keeping a second copy
of anybody's address (constitution 6.6: "sending mail is rate-limited").
Every other path that sends mail has a finite bound as well: see allow_send.
"""

import hashlib
from datetime import timedelta

from superassistant import db

MAIL_PER_ADDRESS = 3            # sign-in, in an hour: a lost mail, twice
MAIL_PER_ADDRESS_WINDOW = 3600
MAIL_PER_SOURCE = 10            # sign-in, in an hour, from one caller
MAIL_PER_SOURCE_WINDOW = 3600

# Every other message has a finite bound too (constitution 6.6). One
# supervisor may rightly be asked by many students near a deadline, so the
# bound per supervisor's address is generous; a student receives a notice of
# a supervisor's answer (a confirmation or a decline) only now and then. All
# mail together is capped as well, which is what keeps the sending domain off
# blocklists whatever goes wrong.
SUPERVISOR_PER_ADDRESS = 30     # requests, new requests and reminders, an hour
NOTICE_PER_ADDRESS = 10         # answer notices to one student, an hour
ALL_MAIL = 300                  # every message, an hour
WINDOW = 3600

UNKNOWN_SOURCE = "unknown"


def bucket(purpose, value):
    digest = hashlib.sha256((purpose + "|" + (value or "")).encode("utf-8"))
    return digest.hexdigest()[:12]


def _claim_all(connection, buckets):
    """Record one attempt in every bucket if all are under their limits."""
    stamp = db.now()
    for name, limit, window in buckets:
        since = (db.now_dt() - timedelta(seconds=window)).isoformat(
            timespec="seconds")
        made = connection.execute(
            "SELECT COUNT(*) FROM attempts WHERE bucket = ? AND at > ?",
            (name, since)).fetchone()[0]
        if made >= limit:
            return False
    for name, limit, window in buckets:
        connection.execute("INSERT INTO attempts (bucket, at) VALUES (?, ?)",
                           (name, stamp))
    return True


def claim(connection, name, limit, window):
    """Record one attempt in this bucket if under the limit. Returns whether."""
    with db.transaction(connection):
        return _claim_all(connection, [(name, limit, window)])


def _all_mail():
    return (bucket("all", "mail"), ALL_MAIL, WINDOW)


def allow_mail(connection, address_key, source):
    """Sign-in mail: the source first, then the destination and all mail."""
    if not claim(connection, bucket("source", source or UNKNOWN_SOURCE),
                 MAIL_PER_SOURCE, MAIL_PER_SOURCE_WINDOW):
        return False
    with db.transaction(connection):
        return _claim_all(connection, [
            (bucket("address", address_key), MAIL_PER_ADDRESS,
             MAIL_PER_ADDRESS_WINDOW), _all_mail()])


def allow_send(connection, kind, address_key, in_transaction):
    """Whether one more message of this kind may go to this address now.

    in_transaction: the caller holds a transaction, which also holds the
    claim; if the caller rolls back (the relay refused), the claim goes too.
    """
    limit = {"supervisor": SUPERVISOR_PER_ADDRESS,
             "notice": NOTICE_PER_ADDRESS}[kind]
    buckets = [(bucket(kind, address_key), limit, WINDOW), _all_mail()]
    if in_transaction:
        return _claim_all(connection, buckets)
    with db.transaction(connection):
        return _claim_all(connection, buckets)
