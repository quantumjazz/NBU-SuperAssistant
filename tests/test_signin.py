"""Students' sign-in by an emailed link or code (NOW.md requirement 1; proof
1's sign-in bullet; proof 4's sign-in message).

Every rule runs over generated addresses: Latin, Cyrillic and both mixed in
one address, any case, padded with spaces as people type them. Each example
first signs out and moves the clock two hours on, so neither an earlier
example's student nor its hourly mail limits decide a later one.
"""

import re
import string
from datetime import timedelta

from hypothesis import HealthCheck, given, settings as hsettings
from hypothesis import strategies as st

from superassistant import db, limits, signin, texts
from tests.conftest import connect

SLOW = hsettings(max_examples=25, deadline=None,
                 suppress_health_check=[HealthCheck.function_scoped_fixture])
SLOWER = hsettings(max_examples=10, deadline=None,
                   suppress_health_check=[HealthCheck.function_scoped_fixture])

CYRILLIC = "абвгдежзийклмнопрстуфхцчшщъьюя"
LETTERS = string.ascii_lowercase + CYRILLIC
LOCAL = st.text(alphabet=LETTERS + string.digits + "._-+", min_size=1,
                max_size=40)
DOMAIN = st.sampled_from(["example.org", "example.bg", "пример.бг",
                          "поща.example.org"])
PAD = st.sampled_from(["", " ", "  ", "\t"])


@st.composite
def addresses(draw):
    """An address in lower case; tests make other cases of it themselves."""
    return draw(LOCAL) + "@" + draw(DOMAIN)


def recase(address, flips):
    """The same address with some letters in capitals."""
    out = []
    for index, ch in enumerate(address):
        out.append(ch.upper() if flips[index % len(flips)] else ch)
    return "".join(out)


def fresh(client, clock):
    """A new example: signed out, and two hours after the last one."""
    client.post("/sign-out")
    clock.advance(hours=2)


def ask(client, address, source="127.0.0.1"):
    return client.post("/sign-in", {"email": address},
                       environ_base={"REMOTE_ADDR": source})


def sent(outbox, address):
    """(token, code) from the latest sign-in message for this address."""
    message = outbox.to(address)[-1]
    token = re.search(r"/link/([A-Za-z0-9_-]+)", message.text).group(1)
    code = re.search(r"^(\d{6})$", message.text, re.M).group(1)
    return token, code


def session_of(client):
    with client.raw.session_transaction() as session:
        return dict(session)


def signins(settings):
    connection = connect(settings)
    try:
        return [dict(row) for row in
                connection.execute("SELECT * FROM signins ORDER BY id")]
    finally:
        connection.close()


def signin_count(settings):
    return len(signins(settings))


# --- The link --------------------------------------------------------------

@SLOW
@given(address=addresses(), pad=PAD)
def test_opening_the_link_spends_nothing_and_its_button_signs_in_once(
        client, outbox, clock, settings, address, pad):
    fresh(client, clock)
    assert ask(client, pad + address + pad).status_code == 302
    token, code = sent(outbox, address)

    for _ in range(2):
        page = client.get("/link/" + token)
        assert page.status_code == 200
        body = page.get_data(as_text=True)
        assert 'action="/link/' + token + '"' in body
        assert texts.SIGNIN_LINK_BUTTON in body
        assert "student" not in session_of(client)
    row = signins(settings)[-1]
    assert row["used_at"] is None and row["link_hash"] and row["code_hash"]

    pressed = client.post("/link/" + token)
    assert pressed.status_code == 302
    assert pressed.headers["Location"].endswith("/application")
    assert session_of(client)["student"] == address.casefold()

    again = client.post("/link/" + token)
    assert again.status_code == 400
    assert texts.SIGNIN_REFUSED in again.get_data(as_text=True)
    assert client.get("/link/" + token).status_code == 400
    # The code from the same message was spent with it.
    other = signin_browser(client.raw.application, row["id"])
    assert other.post("/sign-in/code", {"code": code}).status_code == 400


def signin_browser(application, signin_id):
    """Another browser holding the same sign-in waiting for its code."""
    from tests.conftest import Client
    browser = Client(application.test_client())
    with browser.raw.session_transaction() as session:
        session["signin"] = signin_id
    return browser


@SLOW
@given(address=addresses(), spaced=st.booleans())
def test_the_code_signs_in_once(client, outbox, clock, settings, address,
                                spaced):
    fresh(client, clock)
    ask(client, address)
    token, code = sent(outbox, address)
    page = client.get("/sign-in/code")
    assert page.status_code == 200
    assert texts.SIGNIN_CODE in page.get_data(as_text=True)
    typed = " ".join([code[:3], code[3:]]) if spaced else code
    signed = client.post("/sign-in/code", {"code": typed})
    assert signed.status_code == 302
    assert signed.headers["Location"].endswith("/application")
    assert session_of(client)["student"] == address.casefold()

    row_id = signins(settings)[-1]["id"]
    other = signin_browser(client.raw.application, row_id)
    refused = other.post("/sign-in/code", {"code": code})
    assert refused.status_code == 400
    assert texts.SIGNIN_REFUSED in refused.get_data(as_text=True)
    assert "student" not in session_of(other)
    # The link from the same message was spent with it.
    assert client.post("/link/" + token).status_code == 400


@SLOW
@given(address=addresses(), seconds=st.integers(0, 3 * 60 * 20),
       by_link=st.booleans())
def test_an_expired_link_or_code_is_refused(client, outbox, clock, settings,
                                            address, seconds, by_link):
    fresh(client, clock)
    ask(client, address)
    token, code = sent(outbox, address)
    clock.advance(seconds=seconds)
    alive = seconds < signin.VALID_MINUTES * 60
    if by_link:
        assert client.get("/link/" + token).status_code == (
            200 if alive else 400)
        answer = client.post("/link/" + token)
    else:
        answer = client.post("/sign-in/code", {"code": code})
    if alive:
        assert answer.status_code == 302
        assert session_of(client)["student"] == address.casefold()
    else:
        assert answer.status_code == 400
        assert texts.SIGNIN_REFUSED in answer.get_data(as_text=True)
        assert "student" not in session_of(client)


@SLOWER
@given(address=addresses(), wrong=st.lists(
    st.text(alphabet=string.digits + CYRILLIC + "Xx ", max_size=8),
    min_size=1, max_size=signin.CODE_ATTEMPTS + 1))
def test_five_wrong_codes_spend_the_code_but_not_the_link(
        client, outbox, clock, settings, address, wrong):
    fresh(client, clock)
    ask(client, address)
    token, code = sent(outbox, address)
    wrong = [w for w in wrong if signin.normalise_code(w) != code]
    for guess in wrong:
        refused = client.post("/sign-in/code", {"code": guess})
        assert refused.status_code == 400
        assert texts.SIGNIN_REFUSED in refused.get_data(as_text=True)
    answer = client.post("/sign-in/code", {"code": code})
    if len(wrong) < signin.CODE_ATTEMPTS:
        assert answer.status_code == 302
    else:
        assert answer.status_code == 400
        assert "student" not in session_of(client)
        assert client.post("/link/" + token).status_code == 302
    assert session_of(client)["student"] == address.casefold()


def test_no_waiting_sign_in_refuses_any_code(client, outbox, clock):
    answer = client.post("/sign-in/code", {"code": "123456"})
    assert answer.status_code == 400
    assert texts.SIGNIN_REFUSED in answer.get_data(as_text=True)
    assert client.get("/sign-in/code").status_code == 302
    assert client.get("/link/no-such-token").status_code == 400
    assert client.post("/link/no-such-token").status_code == 400


# --- Limits ----------------------------------------------------------------

@SLOWER
@given(address=addresses(),
       flips=st.lists(st.booleans(), min_size=1, max_size=8))
def test_requests_per_address_are_limited(client, outbox, clock, settings,
                                          address, flips):
    """Three an hour to one mailbox, however its address is capitalised."""
    fresh(client, clock)
    before = signin_count(settings)
    sources = ["10.0.0.{}".format(n) for n in range(limits.MAIL_PER_ADDRESS)]
    for number, source in enumerate(sources):
        typed = recase(address, flips[number:] + flips[:number])
        assert ask(client, typed, source).status_code == 302
    outbox.clear()
    refused = ask(client, recase(address, flips), "10.0.1.1")
    assert refused.status_code == 429
    assert texts.SIGNIN_TOO_MANY in refused.get_data(as_text=True)
    assert outbox.messages == []
    assert signin_count(settings) == before + limits.MAIL_PER_ADDRESS
    clock.advance(seconds=limits.MAIL_PER_ADDRESS_WINDOW + 1)
    assert ask(client, address, "10.0.1.2").status_code == 302


@hsettings(max_examples=5, deadline=None,
           suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(source=st.text(alphabet=string.printable + CYRILLIC, min_size=1,
                      max_size=30), local=LOCAL)
def test_requests_per_source_are_limited(client, outbox, clock, settings,
                                         source, local):
    """Ten an hour from one caller, whatever addresses it names."""
    fresh(client, clock)
    for number in range(limits.MAIL_PER_SOURCE):
        address = "{}{}@example.org".format(local, number)
        assert ask(client, address, source).status_code == 302
    outbox.clear()
    before = signin_count(settings)
    refused = ask(client, local + "x@example.org", source)
    assert refused.status_code == 429
    assert texts.SIGNIN_TOO_MANY in refused.get_data(as_text=True)
    assert outbox.messages == [] and signin_count(settings) == before
    assert ask(client, local + "x@example.org",
               source + "-other").status_code == 302


# --- What is stored and what is sent ---------------------------------------

@SLOW
@given(address=addresses(), pad=PAD, use=st.sampled_from(["", "link",
                                                          "code"]))
def test_no_link_or_code_is_stored_in_the_clear(client, outbox, clock,
                                                settings, address, pad, use):
    fresh(client, clock)
    ask(client, pad + address)
    token, code = sent(outbox, address)
    if use == "link":
        client.post("/link/" + token)
    elif use == "code":
        client.post("/sign-in/code", {"code": code})
    for row in signins(settings):
        for column, value in row.items():
            assert token not in str(value), column
            assert code not in str(value), column
    assert token.encode() not in settings.db_path.read_bytes()


@SLOW
@given(address=addresses(), pad=PAD)
def test_the_message_carries_the_link_and_the_code(client, outbox, clock,
                                                   settings, address, pad):
    fresh(client, clock)
    outbox.clear()
    answer = ask(client, pad + address + pad)
    assert answer.headers["Location"].endswith("/sign-in/code")
    (message,) = outbox.messages
    assert message.intended == address
    assert message.envelope_to == settings.owner_email
    assert message.subject == texts.SIGNIN_MAIL_SUBJECT
    token, code = sent(outbox, address)
    assert settings.base_url + "/link/" + token in message.text
    assert len(code) == signin.CODE_DIGITS and code.isdigit()
    page = client.get("/sign-in/code").get_data(as_text=True)
    assert texts.escape(address) in page


def test_a_refused_message_leaves_no_sign_in_and_says_so(client, outbox,
                                                         clock, settings):
    outbox.refuse = True
    answer = ask(client, "ana.petrova@example.org")
    assert answer.status_code == 502
    assert texts.SIGNIN_NOT_SENT in answer.get_data(as_text=True)
    assert signins(settings) == []
    assert outbox.messages == []
    assert "signin" not in session_of(client)
    outbox.refuse = False
    assert ask(client, "ana.petrova@example.org").status_code == 302
    assert len(signins(settings)) == 1


def test_an_address_that_is_not_one_is_refused(client, outbox, clock,
                                               settings):
    for typed in ["", "ana", "ana@", "ana petrova@example.org"]:
        answer = ask(client, typed)
        assert answer.status_code == 400
        assert texts.MAIL_BAD_ADDRESS in answer.get_data(as_text=True)
    assert outbox.messages == [] and signins(settings) == []


def test_the_code_is_stored_with_the_slow_salted_derivation(
        client, outbox, clock, settings):
    import hashlib
    ask(client, "ana.petrova@example.org")
    token, code = sent(outbox, "ana.petrova@example.org")
    (row,) = signins(settings)
    assert row["code_hash"] == hashlib.pbkdf2_hmac(
        "sha256", code.encode(), bytes.fromhex(row["code_salt"]), 600000,
        dklen=32).hex()
    assert row["link_hash"] == hashlib.sha256(token.encode()).hexdigest()
    assert db.parse(row["expires_at"]) - db.parse(row["created_at"]) \
        == timedelta(minutes=20)


# --- Who the student is ----------------------------------------------------

@SLOW
@given(address=addresses(),
       flips=st.lists(st.booleans(), min_size=1, max_size=8), pad=PAD)
def test_the_same_address_is_the_same_student_at_every_sign_in(
        client, outbox, clock, settings, address, flips, pad):
    fresh(client, clock)
    ask(client, address)
    token, _ = sent(outbox, address)
    client.post("/link/" + token)
    first = session_of(client)["student"]
    client.post("/sign-out")
    assert "student" not in session_of(client)

    typed = recase(address, flips)
    ask(client, pad + typed)
    _, code = sent(outbox, typed)
    client.post("/sign-in/code", {"code": code})
    after = session_of(client)
    assert after["student"] == first == address.casefold()
    assert after["student_email"] == typed


def test_the_start_page_sends_each_kind_of_user_on(client, outbox, clock,
                                                   settings):
    from tests.conftest import make_account
    page = client.get("/")
    assert page.status_code == 200
    assert texts.SIGNIN_TITLE in page.get_data(as_text=True)
    ask(client, "ana.petrova@example.org")
    token, _ = sent(outbox, "ana.petrova@example.org")
    client.post("/link/" + token)
    assert client.get("/").headers["Location"].endswith("/application")
    assert client.post("/sign-out").headers["Location"].endswith("/")
    assert client.get("/").status_code == 200
    make_account(settings, "staff1", password="парола-123")
    client.post("/staff/sign-in", {"login": "staff1",
                                   "password": "парола-123"})
    assert client.get("/").headers["Location"].endswith("/staff")
    client.post("/sign-out")
    assert client.get("/").status_code == 200
