"""Staff accounts: a username, an email address and a password.

Copied in approach from CourseBench (`coursebench/accounts.py`): passwords are
derived with PBKDF2-HMAC-SHA256 at 600,000 iterations, the parameters kept on
the record; a username may not contain "@", so one sign-in field can take a
username or an address without the two colliding; a session carries a tag
that changes with every new password, which signs out the account's other
browsers; and a missing account costs one derivation, like a wrong password.

What is this project's own (constitution 6.5, NOW.md requirement 5): no
emailed code at registration or anywhere else; a new account sees nothing
until the owner approves it; the owner's account is the one the setting
SUPERASSISTANT_OWNER_USERNAME names, and needs no approval.
"""

import hashlib
import hmac
import secrets

from superassistant import db

KDF = {"algorithm": "pbkdf2-sha256", "iterations": 600000, "dklen": 32}
_ABSENT_SALT = "00000000000000000000000000000000"


class AccountError(ValueError):
    """Why an account could not be made or changed, as a sentence."""


def username_key(username):
    return (username or "").strip().casefold()


def email_key(address):
    return (address or "").strip().casefold()


def _hash(password, salt, iterations, dklen):
    return hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"),
                               bytes.fromhex(salt), iterations,
                               dklen=dklen).hex()


def _password_fields(password):
    salt = secrets.token_hex(16)
    return {"algorithm": KDF["algorithm"], "salt": salt,
            "iterations": KDF["iterations"], "dklen": KDF["dklen"],
            "hash": _hash(password, salt, KDF["iterations"], KDF["dklen"]),
            "session_tag": secrets.token_hex(16)}


# --- Reading ---------------------------------------------------------------

def get(connection, account_id):
    return connection.execute("SELECT * FROM accounts WHERE id = ?",
                              (account_id,)).fetchone()


def by_username(connection, username):
    return connection.execute(
        "SELECT * FROM accounts WHERE username_key = ?",
        (username_key(username),)).fetchone()


def by_login(connection, value):
    """The account a sign-in names: a username or an email address."""
    key = (value or "").strip().casefold()
    if not key:
        return None
    return connection.execute(
        "SELECT * FROM accounts WHERE username_key = ? OR email_key = ? "
        "ORDER BY username_key = ? DESC LIMIT 1", (key, key, key)).fetchone()


def all_accounts(connection):
    return connection.execute(
        "SELECT * FROM accounts ORDER BY created_at, id").fetchall()


def is_owner(record, settings):
    return (record is not None and bool(settings.owner_username)
            and record["username_key"] == username_key(settings.owner_username))


def approved(record, settings):
    """Whether this account may see anything: approved, or the owner's."""
    return record is not None and (record["approved_at"] is not None
                                   or is_owner(record, settings))


def verify_password(record, password):
    """Whether this password opens that account. Constant work either way."""
    if record is None or record["algorithm"] != KDF["algorithm"]:
        _hash(password or "", _ABSENT_SALT, KDF["iterations"], KDF["dklen"])
        return False
    computed = _hash(password or "", record["salt"], record["iterations"],
                     record["dklen"])
    return hmac.compare_digest(computed, record["hash"])


# --- Writing ---------------------------------------------------------------

def check_username(username):
    name = (username or "").strip()
    if not name:
        raise AccountError("username")
    if "@" in name:
        raise AccountError("username-at")
    return name


def create(connection, username, email, password):
    """Register a staff account. Raises AccountError with a reason code.

    Reason codes, for the page to put into words: "username", "username-at",
    "email", "password", "username-taken", "email-taken".
    """
    name = check_username(username)
    address = (email or "").strip()
    if "@" not in address or any(ch.isspace() for ch in address):
        raise AccountError("email")
    if not password:
        raise AccountError("password")
    fields = _password_fields(password)
    with db.transaction(connection):
        if connection.execute("SELECT 1 FROM accounts WHERE username_key = ? "
                              "OR email_key = ?",
                              (username_key(name),
                               username_key(name))).fetchone():
            raise AccountError("username-taken")
        if connection.execute("SELECT 1 FROM accounts WHERE email_key = ? "
                              "OR username_key = ?",
                              (email_key(address),
                               email_key(address))).fetchone():
            raise AccountError("email-taken")
        cursor = connection.execute(
            "INSERT INTO accounts (username, username_key, email, email_key, "
            "algorithm, salt, iterations, dklen, hash, session_tag, "
            "created_at) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
            (name, username_key(name), address, email_key(address),
             fields["algorithm"], fields["salt"], fields["iterations"],
             fields["dklen"], fields["hash"], fields["session_tag"],
             db.now()))
    return get(connection, cursor.lastrowid)


def approve(connection, account_id, by_account_id):
    with db.transaction(connection):
        connection.execute(
            "UPDATE accounts SET approved_at = ?, approved_by = ? "
            "WHERE id = ? AND approved_at IS NULL",
            (db.now(), by_account_id, account_id))


def set_password(connection, account_id, password, by):
    """A new password, and a new session tag that signs out other browsers.

    `by` says how ("owner page" or "host command"); the change is recorded.
    The earlier hash is not kept: a password is not a record anybody entered
    about a student, and keeping old hashes would only keep old secrets.
    """
    if not password:
        raise AccountError("password")
    fields = _password_fields(password)
    with db.transaction(connection):
        connection.execute(
            "UPDATE accounts SET algorithm = ?, salt = ?, iterations = ?, "
            "dklen = ?, hash = ?, session_tag = ? WHERE id = ?",
            (fields["algorithm"], fields["salt"], fields["iterations"],
             fields["dklen"], fields["hash"], fields["session_tag"],
             account_id))
        connection.execute(
            "INSERT INTO password_changes (account_id, by, at) "
            "VALUES (?, ?, ?)", (account_id, by, db.now()))
