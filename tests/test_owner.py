"""The owner's page and the owner's host command (NOW.md requirement 5;
proof 3's owner bullet; constitution 6.5, decision 8.1).

The owner's account here is "owner", named by the setting as on the host,
and registered before the service starts, as the start-up check requires.
"""

import io
import itertools
import os
import subprocess
import sys

import pytest
from hypothesis import HealthCheck, assume, given, settings as hsettings
from hypothesis import strategies as st

from superassistant import accounts, owner_password, texts
from tests.conftest import connect, make_account, make_settings

OWNER_PASSWORD = "собственик-парола-1"
PASSWORD = st.text(alphabet=st.characters(blacklist_categories=("Cs",),
                                          blacklist_characters="\x00\r\n"),
                   min_size=1, max_size=40)
_numbers = itertools.count(1)
SLOW = hsettings(max_examples=12, deadline=None,
                 suppress_health_check=[HealthCheck.function_scoped_fixture])


@pytest.fixture
def settings(data_dir):
    values = make_settings(data_dir, owner_username="owner")
    make_account(values, "owner", "owner@example.org", OWNER_PASSWORD,
                 approved=False)
    return values


def sign_in(client, login, password):
    return client.post("/staff/sign-in", {"login": login,
                                          "password": password})


def owner_client(new_client):
    browser = new_client()
    assert sign_in(browser, "owner", OWNER_PASSWORD).status_code == 302
    return browser


def record_of(settings, username):
    connection = connect(settings)
    try:
        return accounts.by_username(connection, username)
    finally:
        connection.close()


def password_changes(settings, account_id):
    connection = connect(settings)
    try:
        return [row["by"] for row in connection.execute(
            "SELECT by FROM password_changes WHERE account_id = ? "
            "ORDER BY id", (account_id,))]
    finally:
        connection.close()


def signed_in(client):
    """Whether this browser is still signed in as approved staff."""
    return client.get("/").status_code == 302


# --- Who reaches the owner's page ------------------------------------------

def test_only_the_owners_account_reaches_the_owners_page(client, new_client,
                                                        settings):
    assert client.get("/owner").headers["Location"].endswith(
        "/staff/sign-in")
    make_account(settings, "staff1", password="парола-123")
    assert sign_in(client, "staff1", "парола-123").status_code == 302
    assert client.get("/owner").status_code == 403
    staff1 = record_of(settings, "staff1")
    assert client.post("/owner/approve/{}".format(staff1["id"])
                       ).status_code == 403
    assert client.post("/owner/password/{}".format(staff1["id"]), {
        "password": "x", "password2": "x"}).status_code == 403

    owner = owner_client(new_client)
    page = owner.get("/owner")
    assert page.status_code == 200
    assert texts.OWNER_TITLE in page.get_data(as_text=True)
    assert texts.NAV_OWNER in page.get_data(as_text=True)
    assert texts.NAV_OWNER not in client.get("/").get_data(as_text=True)


def test_the_owner_approves_a_waiting_account(client, new_client, settings,
                                              outbox):
    client.post("/staff/register", {
        "username": "staff2", "email": "staff2@example.org",
        "password": "парола-123", "password2": "парола-123"})
    assert sign_in(client, "staff2", "парола-123").status_code == 403
    owner = owner_client(new_client)
    page = owner.get("/owner").get_data(as_text=True)
    staff2 = record_of(settings, "staff2")
    assert 'action="/owner/approve/{}"'.format(staff2["id"]) in page
    assert texts.OWNER_STATE_WAITING in page

    answer = owner.post("/owner/approve/{}".format(staff2["id"]))
    assert answer.headers["Location"].endswith("/owner")
    page = owner.get("/owner").get_data(as_text=True)
    assert texts.OWNER_APPROVED.format("staff2") in page
    assert texts.OWNER_NONE_WAITING in page
    approved = record_of(settings, "staff2")
    assert approved["approved_by"] == record_of(settings, "owner")["id"]
    assert sign_in(client, "staff2", "парола-123").status_code == 302
    assert outbox.messages == []
    assert owner.post("/owner/approve/9999").status_code == 404


@SLOW
@given(new=PASSWORD)
def test_the_owner_sets_a_new_password_and_only_it_works(
        new_client, settings, outbox, new):
    assume(new != "парола-123")
    username = "staff{}".format(next(_numbers))
    staff = make_account(settings, username, password="парола-123")
    browser = new_client()
    assert sign_in(browser, username, "парола-123").status_code == 302
    owner = owner_client(new_client)
    outbox.clear()

    answer = owner.post("/owner/password/{}".format(staff["id"]),
                        {"password": new, "password2": new})
    assert answer.headers["Location"].endswith("/owner")
    page = owner.get("/owner").get_data(as_text=True)
    assert texts.escape(texts.OWNER_PASSWORD_SET.format(username)) in page
    assert outbox.messages == []
    assert not signed_in(browser)           # its other browsers are out
    assert sign_in(browser, username, "парола-123").status_code == 400
    assert sign_in(browser, username, new).status_code == 302
    assert password_changes(settings, staff["id"]) == ["owner page"]


def test_a_new_password_must_be_typed_twice_alike(client, new_client,
                                                  settings):
    staff1 = make_account(settings, "staff1", password="парола-123")
    owner = owner_client(new_client)
    for first, second, sentence in [
            ("", "", texts.OWNER_PASSWORD_EMPTY),
            ("нова-1", "нова-2", texts.OWNER_PASSWORD_MISMATCH)]:
        owner.post("/owner/password/{}".format(staff1["id"]),
                   {"password": first, "password2": second})
        assert sentence in owner.get("/owner").get_data(as_text=True)
    assert sign_in(client, "staff1", "парола-123").status_code == 302
    assert password_changes(settings, staff1["id"]) == []
    assert owner.post("/owner/password/9999", {
        "password": "a", "password2": "a"}).status_code == 404


def test_the_owner_may_set_their_own_password_and_stay_signed_in(
        new_client, settings):
    owner = owner_client(new_client)
    elsewhere = owner_client(new_client)
    me = record_of(settings, "owner")
    owner.post("/owner/password/{}".format(me["id"]),
               {"password": "нова-парола", "password2": "нова-парола"})
    assert owner.get("/owner").status_code == 200
    assert not signed_in(elsewhere)
    assert sign_in(elsewhere, "owner", OWNER_PASSWORD).status_code == 400
    assert sign_in(elsewhere, "owner", "нова-парола").status_code == 302


# --- The host command ------------------------------------------------------

@pytest.fixture
def host_env(monkeypatch, settings):
    monkeypatch.setenv("SUPERASSISTANT_DATA_DIR", str(settings.data_dir))
    monkeypatch.setenv("SUPERASSISTANT_OWNER_USERNAME", "owner")
    return monkeypatch


def run_command(monkeypatch, typed, argv=("--stdin",)):
    monkeypatch.setattr(sys, "stdin", io.StringIO(typed))
    return owner_password.main(list(argv))


@SLOW
@given(new=PASSWORD)
def test_the_host_command_sets_the_owners_password(
        new_client, settings, host_env, capsys, new):
    assume(new != OWNER_PASSWORD)
    owner = record_of(settings, "owner")
    connection = connect(settings)
    try:                                # each example starts from the old one
        accounts.set_password(connection, owner["id"], OWNER_PASSWORD,
                              by="test setup")
    finally:
        connection.close()
    elsewhere = owner_client(new_client)
    capsys.readouterr()

    assert run_command(host_env, new + "\n") == 0
    assert capsys.readouterr().out == \
        texts.CLI_PASSWORD_SET.format("owner") + "\n"
    assert not signed_in(elsewhere)
    browser = new_client()
    assert sign_in(browser, "owner", OWNER_PASSWORD).status_code == 400
    assert sign_in(browser, "owner", new).status_code == 302
    assert browser.get("/owner").status_code == 200
    assert password_changes(settings, owner["id"])[-1] == "host command"


def test_the_host_command_reads_the_password_twice(client, settings,
                                                   host_env, capsys):
    typed = iter(["нова-парола", "друга-парола"])
    host_env.setattr("getpass.getpass", lambda prompt="": next(typed))
    assert owner_password.main([]) == 1
    assert texts.CLI_PASSWORD_MISMATCH in capsys.readouterr().err
    typed = iter(["нова-парола", "нова-парола"])
    assert owner_password.main([]) == 0
    assert sign_in(client, "owner", "нова-парола").status_code == 302


def test_the_host_command_fails_with_a_reason(client, settings, host_env,
                                              capsys, tmp_path):
    host_env.setenv("SUPERASSISTANT_OWNER_USERNAME", "nobody")
    assert run_command(host_env, "нова\n") == 1
    assert texts.CLI_NO_ACCOUNT.format(settings.data_dir, "nobody") \
        in capsys.readouterr().err

    host_env.delenv("SUPERASSISTANT_OWNER_USERNAME")
    assert run_command(host_env, "нова\n") == 1
    assert texts.CLI_NO_OWNER_SETTING in capsys.readouterr().err

    host_env.setenv("SUPERASSISTANT_OWNER_USERNAME", "owner")
    assert run_command(host_env, "\n") == 1
    assert texts.CLI_PASSWORD_EMPTY in capsys.readouterr().err

    host_env.setenv("SUPERASSISTANT_DATA_DIR", str(tmp_path / "elsewhere"))
    assert run_command(host_env, "нова\n") == 1
    assert "elsewhere" in capsys.readouterr().err
    assert not (tmp_path / "elsewhere").exists()

    assert sign_in(client, "owner", OWNER_PASSWORD).status_code == 302
    assert password_changes(settings, record_of(settings, "owner")["id"]) \
        == []


def test_the_host_command_runs_as_a_module(client, settings):
    env = dict(os.environ, SUPERASSISTANT_DATA_DIR=str(settings.data_dir),
               SUPERASSISTANT_OWNER_USERNAME="owner", PYTHONIOENCODING="utf-8")
    done = subprocess.run(
        [sys.executable, "-m", "superassistant", "owner-password", "--stdin"],
        input="от-командата-1\n".encode("utf-8"), capture_output=True,
        env=env, cwd=os.path.dirname(os.path.dirname(__file__)))
    assert done.returncode == 0, done.stderr.decode("utf-8")
    assert sign_in(client, "owner", "от-командата-1").status_code == 302
