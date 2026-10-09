"""How often a caller may make NBU-SuperAssistant send mail.

The pattern and the numbers are CourseBench's (`coursebench/signup.py`,
allow_mail): a limit per destination address and one per source, the source
claimed first so that a caller over the limit writes nothing. Buckets are
hashed, so the attempts table counts requests without keeping a second copy
of anybody's address (constitution 6.6: "sending mail is rate-limited").
"""

import hashlib
from datetime import timedelta

from superassistant import db

MAIL_PER_ADDRESS = 3            # in an hour: enough for a lost mail, twice
MAIL_PER_ADDRESS_WINDOW = 3600
MAIL_PER_SOURCE = 10            # in an hour, from one caller
MAIL_PER_SOURCE_WINDOW = 3600
UNKNOWN_SOURCE = "unknown"


def bucket(purpose, value):
    digest = hashlib.sha256((purpose + "|" + (value or "")).encode("utf-8"))
    return digest.hexdigest()[:12]


def claim(connection, name, limit, window):
    """Record one attempt in this bucket if under the limit. Returns whether."""
    since = (db.now_dt() - timedelta(seconds=window)).isoformat(
        timespec="seconds")
    with db.transaction(connection):
        made = connection.execute(
            "SELECT COUNT(*) FROM attempts WHERE bucket = ? AND at > ?",
            (name, since)).fetchone()[0]
        if made >= limit:
            return False
        connection.execute("INSERT INTO attempts (bucket, at) VALUES (?, ?)",
                           (name, db.now()))
        return True


def allow_mail(connection, address_key, source):
    """Both limits: the source first, then the destination."""
    return (claim(connection, bucket("source", source or UNKNOWN_SOURCE),
                  MAIL_PER_SOURCE, MAIL_PER_SOURCE_WINDOW)
            and claim(connection, bucket("address", address_key),
                      MAIL_PER_ADDRESS, MAIL_PER_ADDRESS_WINDOW))
