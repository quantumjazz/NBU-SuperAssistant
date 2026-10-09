"""Staff registration and sign-in (NOW.md requirement 5; proof 3's bullet
on accounts not yet approved; constitution 6.5).

Usernames, addresses and passwords are generated: Latin, Cyrillic, both
mixed, spaces and punctuation. Each example gets names no earlier example
used, by a number in front, so the rules about duplicates are tested on
purpose and never by accident.
"""

import hashlib
import itertools
import string

from hypothesis import HealthCheck, given, settings as hsettings
from hypothesis import strategies as st

from superassistant import accounts, texts
from tests.conftest import connect, insert_application, make_account

SLOW = hsettings(max_examples=25, deadline=None,
                 suppress_health_check=[HealthCheck.function_scoped_fixture])

CYRILLIC = "абвгдежзийклмнопрстуфхцчшщъьюяАБВГДЕЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЬЮЯ"
NAME = st.text(alphabet=string.ascii_letters + string.digits + CYRILLIC
               + " ._-'", max_size=30)
LOCAL = st.text(alphabet=string.ascii_letters + string.digits + CYRILLIC
                + "._-", max_size=20)
PASSWORD = st.text(alphabet=st.characters(blacklist_categories=("Cs",),
                                          blacklist_characters="\x00"),
                   min_size=1, max_size=40)
ERRORS = texts.STAFF_REGISTER_ERRORS
_numbers = itertools.count(1)


def unique():
    return "n{}".format(next(_numbers))


def register(client, username, email, password, again=None):
    return client.post("/staff/register", {
        "username": username, "email": email, "password": password,
        "password2": password if again is None else again})


def sign_in(client, login, password):
    return client.post("/staff/sign-in", {"login": login,
                                          "password": password})


def signed_in_as(client):
    with client.raw.session_transaction() as session:
        return session.get("staff")


def account_count(settings):
    connection = connect(settings)
    try:
        return connection.execute("SELECT COUNT(*) FROM accounts").fetchone()[0]
    finally:
        connection.close()


def by_username(settings, username):
    connection = connect(settings)
    try:
        return accounts.by_username(connection, username)
    finally:
        connection.close()


# --- Registration ----------------------------------------------------------

@SLOW
@given(name=NAME, local=LOCAL, password=PASSWORD, at=st.integers(0, 30))
def test_registration_rules(client, settings, name, local, password, at):
    prefix = unique()
    username = prefix + name.replace("@", "")
    email = prefix + local + "@example.org"
    before = account_count(settings)

    with_at = username[:at] + "@" + username[at:]
    answer = register(client, with_at, "x" + email, password)
    assert answer.status_code == 400
    assert ERRORS["username-at"] in answer.get_data(as_text=True)

    answer = register(client, username, email, "")
    assert answer.status_code == 400
    assert ERRORS["password"] in answer.get_data(as_text=True)

    answer = register(client, username, email, password, password + "x")
    assert ERRORS["mismatch"] in answer.get_data(as_text=True)
    assert account_count(settings) == before

    answer = register(client, "  " + username + " ", email, password)
    assert answer.status_code == 200
    assert texts.STAFF_REGISTERED_WAITING in answer.get_data(as_text=True)
    record = by_username(settings, username)
    assert record["username"] == username.strip()
    assert record["email"] == email and record["approved_at"] is None

    answer = register(client, username.upper(), "y" + email, password)
    assert ERRORS["username-taken"] in answer.get_data(as_text=True)
    answer = register(client, username + "y", email.upper(), password)
    assert ERRORS["email-taken"] in answer.get_data(as_text=True)
    assert account_count(settings) == before + 1


def test_a_blank_username_or_address_is_refused(client, settings):
    for username, email, reason in [("   ", "a@example.org", "username"),
                                    ("ana", "", "email"),
                                    ("ana", "ana example.org", "email")]:
        answer = register(client, username, email, "парола")
        assert answer.status_code == 400
        assert ERRORS[reason] in answer.get_data(as_text=True)
    assert account_count(settings) == 0


@hsettings(max_examples=15, deadline=None,
           suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(password=PASSWORD)
def test_the_password_is_stored_only_as_a_slow_salted_hash(
        client, settings, password):
    password = password + "п"          # never a substring of hex or a date
    username = unique()
    register(client, username, username + "@example.org", password)
    record = dict(by_username(settings, username))
    assert record["algorithm"] == "pbkdf2-sha256"
    assert record["iterations"] == 600000
    assert len(record["salt"]) == 32
    assert record["hash"] == hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), bytes.fromhex(record["salt"]),
        600000, dklen=32).hex()
    for column, value in record.items():
        assert password not in str(value), column


# --- Signing in ------------------------------------------------------------

@SLOW
@given(name=NAME, local=LOCAL, password=PASSWORD, wrong=PASSWORD,
       upper=st.booleans())
def test_sign_in_by_username_or_address_with_the_password(
        client, settings, name, local, password, wrong, upper):
    client.post("/sign-out")
    prefix = unique()
    username = prefix + name.replace("@", "").strip()
    email = prefix + local + "@example.org"
    record = make_account(settings, username, email, password)

    for login in (username, email):
        typed = " " + (login.upper() if upper else login) + " "
        if wrong != password:
            refused = sign_in(client, typed, wrong)
            assert refused.status_code == 400
            assert texts.STAFF_SIGNIN_FAILED in refused.get_data(as_text=True)
            assert signed_in_as(client) is None
        answer = sign_in(client, typed, password)
        assert answer.status_code == 302
        assert answer.headers["Location"].endswith("/staff")
        assert signed_in_as(client) == record["id"]
        client.post("/sign-out")
        assert signed_in_as(client) is None


def test_an_unknown_login_is_refused_with_the_same_sentence(client,
                                                            settings):
    make_account(settings, "staff1", password="парола-123")
    for login, password in [("nobody", "парола-123"), ("", "парола-123"),
                            ("staff1", ""), ("staff1", "парола-12")]:
        answer = sign_in(client, login, password)
        assert answer.status_code == 400
        assert texts.STAFF_SIGNIN_FAILED in answer.get_data(as_text=True)
    assert signed_in_as(client) is None


# --- An account not yet approved sees nothing ------------------------------

STAFF_PAGES = ["/staff", "/staff/application/1", "/owner", "/staff/reports"]


def assert_sees_nothing(client):
    """No staff page, and none of the invented student's data."""
    for url in STAFF_PAGES:
        answer = client.get(url)
        assert answer.status_code != 200, url
        if answer.status_code == 302:
            assert answer.headers["Location"].endswith("/staff/sign-in")
        body = answer.get_data(as_text=True)
        assert "Калина" not in body and "F123456" not in body, url


def test_an_account_not_yet_approved_is_not_signed_in_and_sees_nothing(
        client, new_client, settings):
    insert_application(settings, "kalina@example.org", name1="Калина",
                       name2="Петрова", name3="Тодорова", fn="F123456")
    register(client, "waiting1", "waiting1@example.org", "парола-123")
    for login in ("waiting1", "waiting1@example.org"):
        answer = sign_in(client, login, "парола-123")
        assert answer.status_code == 403
        assert texts.STAFF_SIGNIN_WAITING in answer.get_data(as_text=True)
        assert signed_in_as(client) is None
    assert_sees_nothing(client)

    # Even a browser that holds the account's session sees nothing.
    record = by_username(settings, "waiting1")
    with client.raw.session_transaction() as session:
        session["staff"] = record["id"]
        session["tag"] = record["session_tag"]
    assert_sees_nothing(client)
    assert client.get("/").status_code == 200

    assert_sees_nothing(new_client())
