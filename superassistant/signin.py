"""Students' sign-in: an address, then one message carrying a link and a code.

Copied in approach from CourseBench (`coursebench/signup.py`): a six-digit
code derived with the same slow salted PBKDF2 passwords use (`_slow_hash`),
because a million possibilities fall to a fast hash in a moment; a link token
of 256 random bits stored as a plain SHA-256 (`_token_hash`), because there is
nothing in it to guess; both expire, both are single-use, the code allows five
wrong guesses; every path that checks a code costs exactly one derivation, so
a stopwatch cannot tell "no such sign-in" from "wrong code"; and a message the
relay refused takes its sign-in record with it.

What is this project's own (constitution 5.2 and 6.6, NOW.md requirement 1):
opening the link only shows a page with a „Влез“ button and spends nothing,
because mail scanners open links; pressing the button, or typing the code,
spends the sign-in. The student behind an address is the address casefolded,
so signing in again with the same address reaches the same application.

No Flask here. What a request does with these answers is web/auth.py's.
"""

import hashlib
import hmac
import secrets
from datetime import timedelta, timezone

from superassistant import accounts, db, limits, mail, texts

CODE_DIGITS = 6
VALID_MINUTES = 20
CODE_ATTEMPTS = 5

# Derived against when there is nothing to check, so that every path through
# check_code costs one derivation (CourseBench's _ABSENT_SALT, same reason).
_ABSENT_SALT = "00000000000000000000000000000000"


class BadAddress(ValueError):
    """What was typed is not an email address; nothing was sent."""


class TooMany(RuntimeError):
    """This source or this address has asked for too much mail this hour."""


# --- Hashes ----------------------------------------------------------------

def _slow_hash(value, salt):
    """The derivation accounts.py uses for passwords (CourseBench's
    _slow_hash): six digits are too few for anything faster."""
    return hashlib.pbkdf2_hmac(
        "sha256", value.encode("utf-8"), bytes.fromhex(salt),
        accounts.KDF["iterations"], dklen=accounts.KDF["dklen"]).hex()


def _token_hash(token):
    return hashlib.sha256((token or "").encode("utf-8")).hexdigest()


def _new_code():
    """Exactly six digits, leading zeros included."""
    return "{:0{}d}".format(secrets.randbelow(10 ** CODE_DIGITS), CODE_DIGITS)


def _burn_code_cost():
    _slow_hash(_new_code(), _ABSENT_SALT)


def normalise_code(code):
    """What the student typed, without spaces anywhere in it."""
    return "".join((code or "").split())


# --- Beginning a sign-in ---------------------------------------------------

def begin(connection, address):
    """Record one sign-in for this address. Returns (id, link token, code).

    The token and the code are returned rather than stored: the only thing
    that ever holds them in the clear is the message on its way.
    """
    address = (address or "").strip()
    token = secrets.token_urlsafe(32)
    code = _new_code()
    salt = secrets.token_hex(16)
    created = db.now_dt().astimezone(timezone.utc)
    expires = created + timedelta(minutes=VALID_MINUTES)
    with db.transaction(connection):
        cursor = connection.execute(
            "INSERT INTO signins (email, email_key, code_salt, code_hash, "
            "link_hash, created_at, expires_at) VALUES (?,?,?,?,?,?,?)",
            (address, accounts.email_key(address), salt,
             _slow_hash(code, salt), _token_hash(token),
             created.isoformat(timespec="seconds"),
             expires.isoformat(timespec="seconds")))
    return cursor.lastrowid, token, code


def message(settings, address, token, code):
    """The one message a sign-in sends: the link and the code."""
    link = settings.base_url + "/link/" + token
    return mail.Message(address.strip(), texts.SIGNIN_MAIL_SUBJECT,
                        texts.SIGNIN_MAIL_TEXT.format(
                            link=link, code=code, minutes=VALID_MINUTES))


def offer(connection, settings, address, source):
    """Send this address a link and a code. Returns the sign-in's id.

    Raises BadAddress, TooMany, or mail.MailFailed. The limits are claimed
    before anything is written (limits.allow_mail: the source first, then the
    address). A message the relay refused leaves no sign-in behind: nothing
    is recorded as sent that was not.
    """
    address = (address or "").strip()
    if not mail.valid_address(address):
        raise BadAddress(address)
    if not limits.allow_mail(connection, accounts.email_key(address), source):
        raise TooMany(address)
    signin_id, token, code = begin(connection, address)
    try:
        mail.send(settings, message(settings, address, token, code))
    except mail.MailFailed:
        with db.transaction(connection):
            connection.execute("DELETE FROM signins WHERE id = ?",
                               (signin_id,))
        raise
    return signin_id


# --- Spending a sign-in ----------------------------------------------------

def _alive(row):
    return (row is not None and row["used_at"] is None
            and row["expires_at"] > db.now())


def _spend(connection, signin_id):
    """Used: and the link and code hashes go, not merely marked."""
    connection.execute(
        "UPDATE signins SET used_at = ?, code_hash = NULL, link_hash = NULL "
        "WHERE id = ?", (db.now(), signin_id))


def _get(connection, signin_id):
    try:
        number = int(signin_id)
    except (TypeError, ValueError):
        return None
    return connection.execute("SELECT * FROM signins WHERE id = ?",
                              (number,)).fetchone()


def check_code(connection, signin_id, code):
    """Spend a sign-in with its code. Returns its row, or None.

    One locked step: the read, the comparison, the attempt count and the
    spending, so two submissions of one code cannot both succeed and
    simultaneous wrong guesses cannot slip past the cap (CourseBench's
    check). One sentence for every failure at the page, and one derivation
    on every path. After five wrong guesses the code is spent; the link from
    the same message still works until it is used or expires, since 256
    random bits are not guessed.
    """
    derived = False
    result = None
    with db.transaction(connection):
        row = _get(connection, signin_id)
        if (_alive(row) and row["code_hash"]
                and row["attempts"] < CODE_ATTEMPTS):
            derived = True
            computed = _slow_hash(normalise_code(code), row["code_salt"])
            if hmac.compare_digest(computed, row["code_hash"]):
                _spend(connection, row["id"])
                result = row
            elif row["attempts"] + 1 >= CODE_ATTEMPTS:
                connection.execute(
                    "UPDATE signins SET attempts = attempts + 1, "
                    "code_hash = NULL WHERE id = ?", (row["id"],))
            else:
                connection.execute(
                    "UPDATE signins SET attempts = attempts + 1 WHERE id = ?",
                    (row["id"],))
    if not derived:
        _burn_code_cost()
    return result


def open_link(connection, token):
    """The live sign-in this link names, or None. Reads only."""
    if not token:
        return None
    row = connection.execute("SELECT * FROM signins WHERE link_hash = ?",
                             (_token_hash(token),)).fetchone()
    return row if _alive(row) else None


def spend_link(connection, token):
    """Spend the sign-in this link names. Returns its row, or None.

    The check and the spending are one locked step, so a link pressed twice
    at once signs in once.
    """
    if not token:
        return None
    with db.transaction(connection):
        row = connection.execute("SELECT * FROM signins WHERE link_hash = ?",
                                 (_token_hash(token),)).fetchone()
        if not _alive(row):
            return None
        _spend(connection, row["id"])
    return row
