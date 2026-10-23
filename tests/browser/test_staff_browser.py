"""Staff accounts in a real browser at desktop width (NOW.md proof 5's staff
bullet): registered, approved on the owner's page, signed in by username and
by email address; a wrong password refused; a password reset on the owner's
page, after which only the new one works, its form naming the account to
the browser's password manager without sending it; and the owner's own
password set by the host command.

/staff belongs to the staff pages; a sign-in here is proved by arriving at
its address, whatever that page then shows.
"""

import io
import sys
from urllib.parse import parse_qs

import pytest

from superassistant import accounts, db, owner_password, texts
from tests.browser.conftest import DESKTOP, OWNER_PASSWORD, OWNER_USERNAME

sync_api = pytest.importorskip("playwright.sync_api")
expect = sync_api.expect

pytestmark = pytest.mark.browser


def register(page, url, username, email, password):
    page.goto(url + "/staff/register")
    page.fill("#username", username)
    page.fill("#email", email)
    page.fill("#password", password)
    page.fill("#password2", password)
    page.get_by_role("button", name=texts.STAFF_REGISTER_BUTTON).click()


def sign_in(page, url, login, password):
    page.goto(url + "/staff/sign-in")
    page.fill("#login", login)
    page.fill("#password", password)
    page.get_by_role("button", name=texts.STAFF_SIGNIN_BUTTON).click()


def assert_signed_in(page, url):
    expect(page).to_have_url(url + "/staff")


def assert_refused(page, url, sentence):
    expect(page.get_by_role("alert")).to_have_text(sentence)
    expect(page).to_have_url(url + "/staff/sign-in")


def stored(settings, username):
    connection = db.connect(settings.db_path)
    try:
        return dict(accounts.by_username(connection, username))
    finally:
        connection.close()


def test_staff_accounts_in_the_browser(live_server, open_page, monkeypatch):
    url = live_server.url

    # Registered in the browser; the password kept only as a slow hash.
    page = open_page(DESKTOP)
    register(page, url, "mariya", "mariya.koleva@example.org", "Мария-парола-1")
    expect(page.get_by_role("status")).to_have_text(
        texts.STAFF_REGISTERED_WAITING)
    row = stored(live_server.settings, "mariya")
    assert row["algorithm"] == "pbkdf2-sha256"
    assert row["iterations"] == 600000 and len(row["salt"]) == 32
    assert all("Мария-парола-1" not in str(value) for value in row.values())

    # Not yet approved: not signed in.
    sign_in(page, url, "mariya", "Мария-парола-1")
    assert_refused(page, url, texts.STAFF_SIGNIN_WAITING)

    # The owner approves it on the owner's page.
    owner = open_page(DESKTOP)
    sign_in(owner, url, OWNER_USERNAME, OWNER_PASSWORD)
    assert_signed_in(owner, url)
    owner.goto(url + "/owner")
    waiting = owner.locator('#waiting tr[data-username="mariya"]')
    waiting.get_by_role("button", name=texts.OWNER_APPROVE).click()
    expect(owner.get_by_role("status")).to_have_text(
        texts.OWNER_APPROVED.format("mariya"))
    expect(owner.locator("#waiting")).to_have_count(0)

    # Signed in by username, and by email address, with the password.
    by_name = open_page(DESKTOP)
    sign_in(by_name, url, "mariya", "Мария-парола-1")
    assert_signed_in(by_name, url)
    by_address = open_page(DESKTOP)
    sign_in(by_address, url, "Mariya.Koleva@example.org", "Мария-парола-1")
    assert_signed_in(by_address, url)

    # A wrong password is refused.
    wrong = open_page(DESKTOP)
    sign_in(wrong, url, "mariya", "Мария-парола-2")
    assert_refused(wrong, url, texts.STAFF_SIGNIN_FAILED)

    # The owner sets a new password; only the new one works. The form names
    # the account, read-only, so a password manager files the password under
    # it and not under the owner's own sign-in; the name is not sent.
    account = owner.locator('#accounts tr[data-username="mariya"]')
    whose = account.locator('input[autocomplete="username"]')
    expect(whose).to_be_visible()
    expect(whose).to_have_value("mariya")
    expect(whose).not_to_be_editable()
    account.locator('input[name="password"]').fill("Нова-парола-2")
    account.locator('input[name="password2"]').fill("Нова-парола-2")
    with owner.expect_request(
            lambda request: request.method == "POST"
            and "/owner/password/" in request.url) as sent:
        account.get_by_role("button", name=texts.OWNER_SET_PASSWORD).click()
    assert sorted(parse_qs(sent.value.post_data)) == [
        "csrf", "password", "password2"]
    expect(owner.get_by_role("status")).to_have_text(
        texts.OWNER_PASSWORD_SET.format("mariya"))
    assert live_server.outbox.messages == []
    after = open_page(DESKTOP)
    sign_in(after, url, "mariya", "Мария-парола-1")
    assert_refused(after, url, texts.STAFF_SIGNIN_FAILED)
    sign_in(after, url, "mariya", "Нова-парола-2")
    assert_signed_in(after, url)

    # The owner's own password, set by the host command.
    monkeypatch.setenv("SUPERASSISTANT_DATA_DIR",
                       str(live_server.settings.data_dir))
    monkeypatch.setenv("SUPERASSISTANT_OWNER_USERNAME", OWNER_USERNAME)
    monkeypatch.setattr(sys, "stdin", io.StringIO("Собственик-нова-3\n"))
    assert owner_password.main(["--stdin"]) == 0
    again = open_page(DESKTOP)
    sign_in(again, url, OWNER_USERNAME, OWNER_PASSWORD)
    assert_refused(again, url, texts.STAFF_SIGNIN_FAILED)
    sign_in(again, url, OWNER_USERNAME, "Собственик-нова-3")
    assert_signed_in(again, url)
    again.goto(url + "/owner")
    expect(again.get_by_role("heading", level=1)).to_have_text(
        texts.OWNER_TITLE)
