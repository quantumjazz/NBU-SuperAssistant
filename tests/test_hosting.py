"""Milestone 2, the pilot on the laptop-server: the application's side of it
(docs/reviews/milestone-2.md; the builders' contract, items 1 to 9).

The send mode, the visitor's address behind the tunnel, the settings file,
the start refusals, /healthz, the mail test, the startup line and wsgi.py's
exit. Invented people, temporary folders and the fake relay only: nothing is
sent, and the subprocesses read no settings file but the test's own.
"""

import errno
import importlib
import io
import ipaddress
import logging
import os
import shutil
import string
import subprocess
import sys
from pathlib import Path

import pytest
from hypothesis import HealthCheck, assume, given, settings as hsettings
from hypothesis import strategies as st

from superassistant import __main__ as cli
from superassistant import limits, mail, mail_test, texts, web
from superassistant import settings as settings_module
from superassistant.settings import (CLONE_DIR, Settings, from_env,
                                     load_settings_file)
from superassistant.web import StartupError, create_app
from tests.conftest import OWNER_EMAIL, Client, make_settings

CLONE = Path(__file__).resolve().parent.parent
HOSTED = "https://nbu-superassistant.visiometrica.com"
RELAY = {"smtp_host": "smtp.example.org", "mail_from": "pilot@example.org"}
SENDER = "NBU-SuperAssistant <pilot@example.org>"

RULE = hsettings(max_examples=60, deadline=None,
                 suppress_health_check=[HealthCheck.function_scoped_fixture])
SLOW = hsettings(max_examples=15, deadline=None,
                 suppress_health_check=[HealthCheck.function_scoped_fixture])

CYRILLIC = ("абвгдежзийклмнопрстуфхцчшщъьюя"
            "АБВГДЕЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЬЮЯ")
LOCAL = st.text(alphabet=string.ascii_lowercase + string.digits + "._-+"
                + CYRILLIC[:30], min_size=1, max_size=30)
DOMAIN = st.sampled_from(["example.org", "example.bg", "пример.бг"])
WORDS = st.text(alphabet=string.ascii_letters + string.digits + CYRILLIC
                + " .,;:!?-–„“", min_size=1, max_size=60)


@st.composite
def recipients(draw):
    address = draw(LOCAL) + "@" + draw(DOMAIN)
    assume(mail.valid_address(address) and address != OWNER_EMAIL)
    return address


def sending(data_dir, **overrides):
    """Settings in mode "send", with a relay; on this machine unless the
    overrides say otherwise."""
    values = dict(mail_mode="send", **RELAY)
    values.update(overrides)
    return make_settings(data_dir, **values)


def hosted(data_dir, **overrides):
    """A complete hosted installation, as the pilot's."""
    values = dict(base_url=HOSTED)
    values.update(overrides)
    return sending(data_dir, **values)


# --- 1. Mode "send" -----------------------------------------------------------

@RULE
@given(recipient=recipients(), subject=WORDS.map(str.strip).filter(bool),
       lines=st.lists(WORDS, min_size=1, max_size=6), html=st.booleans())
def test_send_mode_delivers_each_message_to_its_recipient_unchanged(
        tmp_path, outbox, recipient, subject, lines, html):
    outbox.clear()
    text = "\n".join(lines)
    markup = "<p>" + texts.escape(text) + "</p>" if html else None
    mail.send(sending(tmp_path), mail.Message(recipient, subject, text,
                                              markup))
    (sent,) = outbox.messages
    assert sent.envelope_to == recipient
    assert sent.envelope["From"] == SENDER
    assert sent.subject == subject
    assert sent.text.rstrip("\n") == text
    assert sent.html.rstrip("\n") == (markup or "")
    assert sent.intended == ""
    assert "предназначено за" not in sent.text + sent.html


def test_send_mode_pages_carry_no_development_banner(tmp_path, outbox):
    page = create_app(sending(tmp_path / "send")).test_client().get(
        "/").get_data(as_text=True)
    assert 'id="dev-note"' not in page
    assert "Режим за разработка" not in page
    # The development modes still say where mail goes, on every page.
    for mode, note in (("", texts.MAIL_DEV_CONSOLE),
                       ("console", texts.MAIL_DEV_CONSOLE),
                       ("owner", texts.MAIL_DEV_OWNER.format(OWNER_EMAIL))):
        app = create_app(make_settings(tmp_path / ("dev" + mode),
                                       mail_mode=mode))
        assert note in app.test_client().get("/").get_data(as_text=True)


# --- 2. The visitor -----------------------------------------------------------

HEADERS = ("", "CF-Connecting-IP", "X-Real-IP")
HEADER_VALUES = st.one_of(st.none(), st.text(
    alphabet=string.ascii_letters + string.digits + ".:-_ ,", max_size=30))


@pytest.fixture
def apps_by_header(tmp_path, outbox):
    return {header: create_app(make_settings(tmp_path / str(number),
                                             client_ip_header=header))
            for number, header in enumerate(HEADERS)}


@RULE
@given(header=st.sampled_from(HEADERS), value=HEADER_VALUES,
       remote=st.sampled_from(["192.0.2.7", "127.0.0.1", "::1"]))
def test_the_visitor_is_the_named_headers_first_value_else_the_connection(
        apps_by_header, header, value, remote):
    # Every other header a caller could forge carries an address; only the
    # one the setting names may count, and only when it carries a value.
    sent = {name: "203.0.113.99" for name in HEADERS[1:] if name != header}
    if header and value is not None:
        sent[header] = value
    first = (value or "").split(",")[0].strip()
    expected = first if header and value is not None and first else remote
    with apps_by_header[header].test_request_context(
            "/", headers=sent, environ_base={"REMOTE_ADDR": remote}):
        assert web.source() == counted_as(expected)


def counted_as(address):
    """The model: an IPv6 visitor counts by its /64, the block one machine
    is given; an IPv4-mapped one as its IPv4 address; anything else as
    written."""
    try:
        ip = ipaddress.ip_address(address)
        if ip.version == 6 and ip.ipv4_mapped is not None:
            return str(ip.ipv4_mapped)
        if ip.version == 6:
            return str(ipaddress.ip_network(address + "/64", strict=False))
    except ValueError:
        pass
    return address


def test_behind_the_tunnel_each_visitor_has_its_own_limit(tmp_path, outbox,
                                                          clock):
    """The tunnel connects from 127.0.0.1; with the setting, the visitor is
    the header's first value. (Without it, a forged header is ignored:
    tests/test_review_findings.py, M1-C7.)"""
    app = create_app(make_settings(tmp_path / "data",
                                   client_ip_header="CF-Connecting-IP"))

    def ask(number, value):
        headers = {} if value is None else {"CF-Connecting-IP": value}
        return Client(app.test_client()).post(
            "/sign-in", data={"email": "v{}@example.org".format(number)},
            headers=headers,
            environ_base={"REMOTE_ADDR": "127.0.0.1"}).status_code

    # One visitor, whatever else the chain carries after its address.
    codes = [ask(n, "198.51.100.1, 10.0.0.{}".format(n))
             for n in range(limits.MAIL_PER_SOURCE + 1)]
    assert codes == [302] * limits.MAIL_PER_SOURCE + [429]
    # Another visitor through the same tunnel is not held by the first.
    assert ask(100, "198.51.100.2") == 302
    # No header, or an empty one: the connection, a bucket of its own.
    fallback = [ask(200 + n, None if n % 2 else "")
                for n in range(limits.MAIL_PER_SOURCE)]
    assert fallback == [302] * limits.MAIL_PER_SOURCE
    assert ask(300, " , 198.51.100.3") == 429
    assert ask(301, "198.51.100.3") == 302


def test_an_ipv6_visitor_is_counted_by_its_64_bit_block(tmp_path, outbox,
                                                        clock):
    """Opus 5.5's review of 0534b19, F3: one machine on IPv6 holds a whole
    /64, so counting each address on its own let one visitor sign in 40
    times where an IPv4 visitor gets 10."""
    app = create_app(make_settings(tmp_path / "data",
                                   client_ip_header="CF-Connecting-IP"))

    def ask(number, value):
        return Client(app.test_client()).post(
            "/sign-in", data={"email": "w{}@example.org".format(number)},
            headers={"CF-Connecting-IP": value},
            environ_base={"REMOTE_ADDR": "127.0.0.1"}).status_code

    codes = [ask(n, "2001:db8:1:2::{:x}".format(n + 1))
             for n in range(limits.MAIL_PER_SOURCE + 1)]
    assert codes == [302] * limits.MAIL_PER_SOURCE + [429]
    assert ask(100, "2001:db8:1:3::1") == 302      # the next /64: another
    assert ask(101, "2001:db8:1:2:ffff::9") == 429  # the same /64 again


# --- 3. The settings file -----------------------------------------------------

def write(path, lines):
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def test_the_settings_file_is_read_as_systemd_reads_it(tmp_path):
    path = write(tmp_path / ".env.production", [
        "# The pilot's settings",
        "",
        "   ",
        "  # an indented comment",
        "SUPERASSISTANT_BASE_URL=https://pilot.example.org",
        "  SUPERASSISTANT_MAIL_FROM = pilot@example.org  ",
        "SUPERASSISTANT_SMTP_PASSWORD=a=b==c#d",
        "SUPERASSISTANT_SMTP_PORT=",
        "SUPERASSISTANT_MAIL_MODE=console",
        "SUPERASSISTANT_MAIL_MODE=send",
        "SUPERASSISTANT_SET_IN_SHELL=from the file",
        "SUPERASSISTANT_EMPTY_IN_SHELL=from the file",
        "a line without an equals sign",
        "export SUPERASSISTANT_EXPORTED=1",
        "=a value with no name",
        "#SUPERASSISTANT_COMMENTED=1",
    ])
    environ = {"SUPERASSISTANT_SET_IN_SHELL": "from the shell",
               "SUPERASSISTANT_EMPTY_IN_SHELL": ""}
    loaded = load_settings_file(path, environ)
    assert environ == {
        "SUPERASSISTANT_BASE_URL": "https://pilot.example.org",
        "SUPERASSISTANT_MAIL_FROM": "pilot@example.org",
        "SUPERASSISTANT_SMTP_PASSWORD": "a=b==c#d",
        "SUPERASSISTANT_SMTP_PORT": "",
        "SUPERASSISTANT_MAIL_MODE": "send",
        "SUPERASSISTANT_SET_IN_SHELL": "from the shell",
        "SUPERASSISTANT_EMPTY_IN_SHELL": "",
    }
    assert sorted(loaded) == sorted(set(environ) - {
        "SUPERASSISTANT_SET_IN_SHELL", "SUPERASSISTANT_EMPTY_IN_SHELL"})


def test_a_missing_settings_file_changes_nothing(tmp_path):
    environ = {"SUPERASSISTANT_DATA_DIR": "/somewhere"}
    assert load_settings_file(tmp_path / "absent", environ) == []
    assert environ == {"SUPERASSISTANT_DATA_DIR": "/somewhere"}


NAMES = st.from_regex(r"[A-Z_][A-Z0-9_]{0,15}", fullmatch=True)
# Values systemd's EnvironmentFile reads exactly as written: no quotes and
# no backslashes, which systemd would remove and the reader refuses.
VALUES = st.text(alphabet=string.ascii_letters + string.digits
                 + "=:/@.-_ #", max_size=30).map(str.strip)
NOISE = st.sampled_from(["", "   ", "# a comment", "#NAME=commented",
                         "no equals sign here", "export NAME=1", "=1"])


@RULE
@given(file_values=st.dictionaries(NAMES, VALUES, max_size=8),
       shell=st.dictionaries(NAMES, VALUES, max_size=4),
       noise=st.lists(NOISE, max_size=5), data=st.data())
def test_a_settings_file_sets_what_the_shell_has_not(
        tmp_path, file_values, shell, noise, data):
    lines = ["{}={}".format(k, v) for k, v in file_values.items()] + noise
    path = write(tmp_path / "settings", data.draw(st.permutations(lines)))
    environ = dict(shell)
    load_settings_file(path, environ)
    expected = dict(file_values)
    expected.update(shell)
    assert environ == expected


@pytest.mark.parametrize("value", ['"re_FAKE_123"', "'re_FAKE_123'",
                                   "re_FA\\KE_123", "re_FAKE_123\\"])
def test_a_value_systemd_would_read_differently_is_refused(tmp_path, value):
    """Opus 5.5's review of 0534b19, F1: systemd removes quotes and
    backslashes that the reader kept, so a host command (mail-test) and the
    service could use different passwords or folders. The reader refuses
    such a line instead, naming its number and setting, never its value, and
    sets nothing from the file."""
    path = write(tmp_path / ".env.production", [
        "# the pilot's settings",
        "SUPERASSISTANT_SMTP_HOST=smtp.example.org",
        "SUPERASSISTANT_SMTP_PASSWORD=" + value,
    ])
    environ = {}
    with pytest.raises(settings_module.SettingsFileError) as caught:
        load_settings_file(path, environ)
    message = str(caught.value)
    assert "SUPERASSISTANT_SMTP_PASSWORD" in message
    assert "line 3" in message
    assert "re_FA" not in message
    assert environ == {}


def test_only_a_newline_ends_a_line_and_only_blanks_are_trimmed(tmp_path):
    """Opus 5.5's review of 0534b19, F1: str.splitlines() and str.strip()
    also act on form feeds, NEL and no-break spaces; systemd does not."""
    path = tmp_path / ".env.production"
    path.write_text("SUPERASSISTANT_SMTP_PASSWORD=re_a\x0cbc\u00a0\r\n"
                    "SUPERASSISTANT_SMTP_HOST=\tsmtp.example.org \r\n",
                    encoding="utf-8")
    environ = {}
    load_settings_file(path, environ)
    assert environ == {"SUPERASSISTANT_SMTP_PASSWORD": "re_a\x0cbc\u00a0",
                       "SUPERASSISTANT_SMTP_HOST": "smtp.example.org"}


def test_a_carriage_return_ends_a_line_as_systemd_reads_it(tmp_path):
    """Codex's M2-C1 (11 October 2026) asked to keep a carriage return
    inside a value. The host's systemd 255, given this very file through a
    transient unit's EnvironmentFile=, gave SUPERASSISTANT_SMTP_PASSWORD
    the value "re_FAKE_before", D the value "x" and y the value "z", and
    left C unset: a carriage return ends a line there, as a line feed does.
    The reader must give the same, or the host commands would test other
    settings than the service runs with."""
    path = tmp_path / ".env.production"
    path.write_bytes(b"SUPERASSISTANT_SMTP_PASSWORD=re_FAKE_before\rafter\n"
                     b"SUPERASSISTANT_A=one\r\n"
                     b"SUPERASSISTANT_B=  two words  \n"
                     b";SUPERASSISTANT_C=semicolon\n"
                     b"SUPERASSISTANT_D=x\ry=z\n")
    environ = {}
    load_settings_file(path, environ)
    assert environ == {"SUPERASSISTANT_SMTP_PASSWORD": "re_FAKE_before",
                       "SUPERASSISTANT_A": "one",
                       "SUPERASSISTANT_B": "two words",
                       "SUPERASSISTANT_D": "x",
                       "y": "z"}


# Taken when this module is imported, before any test repoints it.
REAL_SETTINGS_FILE = settings_module.SETTINGS_FILE


def test_the_settings_file_is_the_clones_whatever_the_working_directory(
        tmp_path, monkeypatch):
    """Opus 5.5's review of 0534b19, T4: a host command run from anywhere
    opens the records the service opens."""
    monkeypatch.chdir(str(tmp_path))
    assert REAL_SETTINGS_FILE == CLONE / ".env.production"
    assert REAL_SETTINGS_FILE.is_absolute()
    assert CLONE_DIR == CLONE


@pytest.mark.parametrize("command, arguments", [
    ("remind", []), ("owner-password", ["--stdin"]),
    ("mail-test", ["tester@example.org"])])
def test_every_host_command_reads_the_settings_file(
        tmp_path, monkeypatch, capsys, outbox, command, arguments):
    """Opus 5.5's review of 0534b19, T3: not only mail-test. A settings
    file naming another records folder and an address no start accepts
    makes each command refuse, naming what came from the file."""
    path = write(tmp_path / ".env.production", [
        "SUPERASSISTANT_BASE_URL=ftp://from-the-file",
        "SUPERASSISTANT_DATA_DIR=" + str(tmp_path / "file-data"),
        "SUPERASSISTANT_OWNER_USERNAME=owner",
        "SUPERASSISTANT_MAIL_MODE=from-the-file",
    ])
    monkeypatch.setattr(settings_module, "SETTINGS_FILE", path)
    monkeypatch.setattr(sys, "stdin", io.StringIO("new-password-1\n"))
    assert cli.main([command] + arguments) == 1
    said = capsys.readouterr().err
    assert "from-the-file" in said or "file-data" in said, said
    assert outbox.messages == []


def test_a_refused_settings_file_stops_a_host_command_in_one_line(
        tmp_path, monkeypatch, capsys):
    path = write(tmp_path / ".env.production", [
        'SUPERASSISTANT_SMTP_PASSWORD="re_FAKE_123"'])
    monkeypatch.setattr(settings_module, "SETTINGS_FILE", path)
    assert cli.main(["remind"]) == 1
    said = capsys.readouterr().err
    assert said.startswith("NBU-SuperAssistant cannot start: ")
    assert said.count("\n") == 1 and "re_FAKE" not in said


def test_host_commands_read_the_settings_file_first(tmp_path, monkeypatch,
                                                    outbox, capsys):
    path = write(tmp_path / ".env.production", [
        "SUPERASSISTANT_MAIL_MODE=send",
        "SUPERASSISTANT_SMTP_HOST=smtp.example.org",
        "SUPERASSISTANT_SMTP_PORT=2525",
        "SUPERASSISTANT_MAIL_FROM=pilot@example.org",
    ])
    monkeypatch.setattr(settings_module, "SETTINGS_FILE", path)
    monkeypatch.setenv("SUPERASSISTANT_SMTP_PORT", "2587")   # the shell wins
    assert cli.main(["mail-test", "tester@example.org"]) == 0
    (sent,) = outbox.messages
    assert sent.envelope_to == "tester@example.org"
    assert "smtp.example.org:2587 (starttls)" in capsys.readouterr().out


def test_app_py_and_create_app_never_read_the_settings_file(
        tmp_path, monkeypatch):
    path = write(tmp_path / ".env.production", [
        "SUPERASSISTANT_BASE_URL=ftp://from-the-file",
        "SUPERASSISTANT_DATA_DIR=" + str(tmp_path / "file-data"),
    ])
    monkeypatch.setattr(settings_module, "SETTINGS_FILE", path)
    monkeypatch.setenv("SUPERASSISTANT_DATA_DIR", str(tmp_path / "data"))
    import flask
    monkeypatch.setattr(flask.Flask, "run", lambda self, *a, **k: None)
    development = importlib.import_module("app")
    assert development.main() == 0
    assert "SUPERASSISTANT_BASE_URL" not in os.environ
    assert not (tmp_path / "file-data").exists()


# --- 5. Start refusals --------------------------------------------------------

GOOD_HOSTS = st.one_of(
    st.from_regex(r"[a-z0-9]([a-z0-9-]{0,8}[a-z0-9])?"
                  r"(\.[a-z0-9]([a-z0-9-]{0,8}[a-z0-9])?){0,3}",
                  fullmatch=True),
    st.sampled_from(["localhost", "LOCALHOST", "127.0.0.1", "[::1]",
                     "Example.ORG", "192.0.2.10", "[2001:db8::1]",
                     # Near misses of this machine, hosted all the same
                     # (Opus 5.5's review of 0534b19, T5).
                     "127.0.0.2", "127.1.2.3", "0.0.0.0",
                     "localhost.localdomain", "[::ffff:127.0.0.1]"]))
BAD_HOSTS = st.sampled_from(["", "exa mple.org", "пример.бг", "[::1",
                             "host!", "a_b c"])
GOOD_PORTS = st.one_of(st.none(), st.integers(1, 65535).map(str))
BAD_PORTS = st.sampled_from(["0", "65536", "99999", "100000", "", "+80",
                             " 80", "8a", "٨٠"])
GOOD_TAILS = st.sampled_from(["", "/", "//"])
BAD_TAILS = st.sampled_from(["/path", "/a/", "?", "?q=1", "#", "#top",
                             "/?x", "/link/abc"])


@st.composite
def base_urls(draw):
    """(base URL, refused as malformed, its host) from generated parts."""
    good = {"scheme": draw(st.booleans()), "user": draw(st.booleans()),
            "host": draw(st.booleans()), "port": draw(st.booleans()),
            "tail": draw(st.booleans())}
    scheme = draw(st.sampled_from(["https", "http"]) if good["scheme"] else
                  st.sampled_from(["ftp", "HTTPS", "Http", "", "https:"]))
    user = "" if good["user"] else draw(st.sampled_from(
        ["pilot@", "pilot:s3cr3t-pw@", ":@"]))
    host = draw(GOOD_HOSTS if good["host"] else BAD_HOSTS)
    port = draw(GOOD_PORTS if good["port"] else BAD_PORTS)
    tail = draw(GOOD_TAILS if good["tail"] else BAD_TAILS)
    url = scheme + "://" + user + host + ("" if port is None else ":" + port) \
        + tail
    return url, not all(good.values()), host.strip("[]").lower()


@RULE
@given(generated=base_urls())
def test_the_base_url_must_be_just_scheme_host_and_port(tmp_path, generated):
    url, malformed, host = generated
    # Everything else a hosted installation needs is in order, so the base
    # URL is the only setting a refusal could name.
    problem = hosted(tmp_path, base_url=url).problem()
    local = host in ("localhost", "127.0.0.1", "::1")
    plain_http_elsewhere = url.startswith("http://") and not local
    refused = malformed or plain_http_elsewhere
    assert ("SUPERASSISTANT_BASE_URL" in problem) == refused, (url, problem)
    assert ("SUPERASSISTANT_" in problem) == refused
    assert "s3cr3t-pw" not in problem


@pytest.mark.parametrize("base_url", ["http://127.0.0.1:5002", HOSTED])
@pytest.mark.parametrize("relay, named", [
    ({"smtp_host": "", "mail_from": "pilot@example.org"},
     "SUPERASSISTANT_SMTP_HOST"),
    ({"smtp_host": "smtp.example.org", "mail_from": ""},
     "SUPERASSISTANT_MAIL_FROM"),
    ({"smtp_host": "smtp.example.org", "mail_from": "not an address"},
     "SUPERASSISTANT_MAIL_FROM"),
])
def test_send_mode_needs_a_relay_and_a_sender(tmp_path, base_url, relay,
                                              named):
    settings = make_settings(tmp_path / "data", mail_mode="send",
                             base_url=base_url, **relay)
    assert named in settings.problem()
    assert "SUPERASSISTANT_MAIL_MODE" in settings.problem()
    with pytest.raises(StartupError) as raised:
        create_app(settings)
    assert named in str(raised.value)
    assert not (tmp_path / "data").exists()     # refused before anything
    assert sending(tmp_path, base_url=base_url).problem() == ""


def test_a_complete_hosted_installation_starts(tmp_path, outbox):
    settings = hosted(tmp_path / "data")
    assert settings.is_hosted() and settings.problem() == ""
    assert create_app(settings).config["SESSION_COOKIE_SECURE"] is True


def test_a_hosted_installation_needs_https(tmp_path):
    problem = hosted(tmp_path, base_url=HOSTED.replace("https", "http")
                     ).problem()
    assert "SUPERASSISTANT_BASE_URL" in problem and "https" in problem
    for local in ("http://localhost:5002", "http://127.0.0.1:5002",
                  "http://[::1]:5002", "http://LocalHost"):
        assert hosted(tmp_path, base_url=local).problem() == ""


def test_a_hosted_installation_names_its_records_folder(tmp_path,
                                                        monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))   # the default folder's home
    for name, value in (("BASE_URL", HOSTED), ("MAIL_MODE", "send"),
                        ("SMTP_HOST", "smtp.example.org"),
                        ("MAIL_FROM", "pilot@example.org")):
        monkeypatch.setenv("SUPERASSISTANT_" + name, value)
    settings = from_env()
    assert not settings.data_dir_explicit
    assert "SUPERASSISTANT_DATA_DIR" in settings.problem()
    monkeypatch.setenv("SUPERASSISTANT_DATA_DIR", str(tmp_path / "records"))
    assert from_env().problem() == ""
    # On this machine the default folder is still allowed (milestone 1).
    monkeypatch.delenv("SUPERASSISTANT_DATA_DIR")
    monkeypatch.delenv("SUPERASSISTANT_BASE_URL")
    assert from_env().problem() == ""


@pytest.mark.parametrize("inside", [
    CLONE, CLONE / "data", CLONE / "a" / ".." / "records",
    CLONE / "superassistant" / "records"])
def test_a_hosted_installation_keeps_no_records_inside_the_clone(inside):
    # Only the rule is asked: nothing is created inside the clone.
    problem = hosted(inside).problem()
    assert "SUPERASSISTANT_DATA_DIR" in problem and "inside the clone" in \
        problem
    assert sending(inside).problem() == ""      # on this machine: allowed


def test_the_clone_is_compared_where_the_records_would_land(tmp_path,
                                                            monkeypatch):
    assert CLONE_DIR == CLONE
    link = tmp_path / "records"
    link.symlink_to(CLONE / "records-through-a-link")   # dangling
    assert "inside the clone" in hosted(link).problem()
    monkeypatch.chdir(str(CLONE))                       # a relative folder
    assert "inside the clone" in hosted(Path("records")).problem()
    beside = Path(str(CLONE) + "-data")                 # same prefix, beside
    assert hosted(beside).problem() == ""
    assert hosted(CLONE.parent / "nbu-superassistant-data").problem() == ""


@pytest.mark.parametrize("mode, refused", [("", True), ("console", True),
                                           ("send", False),
                                           ("owner", False)])
def test_a_hosted_installation_sends_its_mail(tmp_path, mode, refused):
    problem = hosted(tmp_path, mail_mode=mode).problem()
    assert ("SUPERASSISTANT_MAIL_MODE" in problem) == refused
    assert bool(problem) == refused


@pytest.mark.parametrize("name", ["reminder_days", "reminder_count"])
@pytest.mark.parametrize("value", ["3 # calendar days", "three", "2.5"])
def test_a_reminder_setting_that_is_no_whole_number_is_refused_by_name(
        tmp_path, monkeypatch, name, value):
    """Opus 5.5's review of 0534b19, F4: a traceback, not the sentence the
    host's journal is meant to show."""
    setting = "SUPERASSISTANT_" + name.upper()
    monkeypatch.setenv(setting, value)
    monkeypatch.setenv("SUPERASSISTANT_DATA_DIR", str(tmp_path / "data"))
    problem = from_env().problem()
    assert setting in problem and "whole number" in problem
    with pytest.raises(StartupError):
        create_app()


def test_every_refusal_is_named_at_once(tmp_path):
    settings = Settings(tmp_path, base_url="http://pilot.example.org",
                        mail_mode="console", data_dir_explicit=False)
    problem = settings.problem()
    for name in ("SUPERASSISTANT_BASE_URL", "SUPERASSISTANT_DATA_DIR",
                 "SUPERASSISTANT_MAIL_MODE"):
        assert name in problem
    assert "\n" not in problem


# --- 6. /healthz --------------------------------------------------------------

def test_healthz_says_ok_while_the_records_can_be_written(tmp_path, outbox):
    settings = make_settings(tmp_path / "data")
    client = create_app(settings).test_client()           # nobody signed in
    before = sorted(os.listdir(str(settings.data_dir)))
    response = client.get("/healthz")
    assert response.status_code == 200
    assert response.get_json() == {"status": "ok"}
    assert sorted(os.listdir(str(settings.data_dir))) == before
    assert str(tmp_path) not in response.get_data(as_text=True)


@pytest.mark.skipif(hasattr(os, "geteuid") and os.geteuid() == 0,
                    reason="root can write into a read-only folder")
def test_healthz_says_503_when_the_records_cannot_be_written(tmp_path,
                                                            outbox):
    settings = make_settings(tmp_path / "data")
    client = create_app(settings).test_client()
    os.chmod(str(settings.data_dir), 0o500)
    try:
        read_only = client.get("/healthz")
    finally:
        os.chmod(str(settings.data_dir), 0o700)
    shutil.rmtree(str(settings.data_dir))
    gone = client.get("/healthz")
    for response in (read_only, gone):
        assert response.status_code == 503
        assert response.get_json() == {
            "status": "data directory is not writable"}
        assert str(tmp_path) not in response.get_data(as_text=True)


def test_healthz_says_503_when_the_disk_refuses_the_write(tmp_path, outbox,
                                                         monkeypatch):
    """Opus 5.5's review of 0534b19, T2: the failure a host actually has is
    a full disk, which permission bits (os.access) never show."""
    settings = make_settings(tmp_path / "data")
    client = create_app(settings).test_client()
    before = sorted(os.listdir(str(settings.data_dir)))

    def full(descriptor):
        raise OSError(errno.ENOSPC, "No space left on device")

    monkeypatch.setattr(os, "fsync", full)
    response = client.get("/healthz")
    assert response.status_code == 503
    assert response.get_json() == {"status": "data directory is not writable"}
    assert sorted(os.listdir(str(settings.data_dir))) == before


# --- 7. mail-test -------------------------------------------------------------

def mail_test_run(settings, address="tester@example.org"):
    out, err = io.StringIO(), io.StringIO()
    status = mail_test.run(settings, address, out=out, err=err)
    return status, out.getvalue(), err.getvalue()


@pytest.mark.parametrize("mode", ["", "console"])
def test_mail_test_prints_in_console_mode(tmp_path, outbox, mode):
    status, out, err = mail_test_run(make_settings(tmp_path, mail_mode=mode,
                                                   **RELAY))
    assert (status, err, outbox.messages) == (0, "", [])
    assert out.startswith(texts.CLI_MAIL_TEST_PLAN_CONSOLE.format(
        mode=mode or texts.CLI_MAIL_TEST_MODE_UNSET,
        address="tester@example.org"))
    assert "To: tester@example.org" in out
    assert texts.CLI_MAIL_TEST_SUBJECT in out
    assert out.rstrip().endswith(texts.CLI_MAIL_TEST_PRINTED)


def test_mail_test_in_owner_mode_goes_to_the_owner(tmp_path, outbox):
    status, out, err = mail_test_run(make_settings(
        tmp_path, mail_mode="owner", **RELAY))
    assert (status, err) == (0, "")
    (sent,) = outbox.messages
    assert sent.envelope_to == OWNER_EMAIL
    assert sent.intended == "tester@example.org"
    plan = texts.CLI_MAIL_TEST_PLAN_OWNER.format(
        address="tester@example.org", owner=OWNER_EMAIL,
        relay="smtp.example.org:587 (starttls)", sender=SENDER)
    assert out.startswith(plan)
    assert out.rstrip().endswith(texts.CLI_MAIL_TEST_ACCEPTED)


def test_mail_test_in_send_mode_goes_to_the_address(tmp_path, outbox):
    settings = sending(tmp_path, smtp_port="465", smtp_security="ssl",
                       smtp_username="relay-user-name",
                       smtp_password="relay-s3cr3t-pw")
    status, out, err = mail_test_run(settings)
    assert (status, err) == (0, "")
    (sent,) = outbox.messages
    assert sent.envelope_to == "tester@example.org"
    assert sent.envelope["From"] == SENDER and sent.intended == ""
    assert sent.subject == texts.CLI_MAIL_TEST_SUBJECT
    plan = texts.CLI_MAIL_TEST_PLAN_SEND.format(
        address="tester@example.org", relay="smtp.example.org:465 (ssl)",
        sender=SENDER)
    # First what it will do, then that the relay accepted it, and that
    # accepted is not delivered.
    assert out.startswith(plan)
    assert out.index(plan) < out.index(texts.CLI_MAIL_TEST_ACCEPTED)
    assert "спам" in texts.CLI_MAIL_TEST_ACCEPTED
    assert "relay-s3cr3t-pw" not in out + err
    assert "relay-user-name" not in out + err


def test_mail_test_says_when_the_relay_refuses(tmp_path, outbox):
    outbox.refuse = True
    status, out, err = mail_test_run(sending(tmp_path))
    assert status == 1
    assert out.startswith(texts.CLI_MAIL_TEST_PLAN_SEND.split("{")[0])
    assert texts.CLI_MAIL_TEST_ACCEPTED not in out
    assert err == texts.CLI_MAIL_TEST_REFUSED.format(
        "the fake relay refused the message") + "\n"


@pytest.mark.parametrize("overrides, named", [
    ({"mail_mode": "send", "smtp_host": "", "mail_from": "p@example.org"},
     "SUPERASSISTANT_SMTP_HOST"),
    ({"mail_mode": "send", "smtp_host": "smtp.example.org",
      "mail_from": ""}, "SUPERASSISTANT_MAIL_FROM"),
    ({"mail_mode": "owner", "smtp_host": "", "mail_from": "p@example.org"},
     "SUPERASSISTANT_SMTP_HOST"),
    ({"mail_mode": "owner", "owner_email": "", "smtp_host": "s.example.org",
      "mail_from": "p@example.org"}, "SUPERASSISTANT_OWNER_EMAIL"),
    ({"mail_mode": "carrier-pigeon"}, "SUPERASSISTANT_MAIL_MODE"),
])
def test_mail_test_refuses_when_mail_is_not_configured(tmp_path, outbox,
                                                       overrides, named):
    status, out, err = mail_test_run(make_settings(tmp_path, **overrides))
    assert (status, out, outbox.messages) == (1, "", [])
    assert err.startswith(texts.CLI_MAIL_TEST_UNCONFIGURED.format(""))
    assert named in err


@pytest.mark.parametrize("arguments", [
    [], ["a@example.org", "b@example.org"], ["not an address"], ["--to"],
    ["@example.org"]])
def test_mail_test_bad_usage_sends_nothing(outbox, capsys, arguments):
    assert cli.main(["mail-test"] + arguments) == 2
    assert outbox.messages == []
    err = capsys.readouterr().err
    assert texts.CLI_MAIL_TEST_USAGE in err or \
        texts.CLI_MAIL_TEST_BAD_ADDRESS.format(arguments[0]) in err


def test_the_command_line_lists_mail_test(capsys):
    assert cli.main([]) == 2
    assert "mail-test <address>" in capsys.readouterr().err


# --- 8. The startup line ------------------------------------------------------

SECRETS = st.text(alphabet=string.ascii_letters + string.digits,
                  min_size=16, max_size=40)


@SLOW
@given(password=SECRETS, key=SECRETS, username=SECRETS,
       header=st.sampled_from(["", "CF-Connecting-IP"]),
       mode=st.sampled_from(["send", "owner", "console", ""]),
       base_url=st.sampled_from([HOSTED, "http://127.0.0.1:5002"]))
def test_the_startup_line_says_what_was_resolved_and_no_secret(
        tmp_path_factory, capsys, outbox, password, key, username, header,
        mode, base_url):
    assume(mode in ("send", "owner") or base_url != HOSTED)
    data_dir = tmp_path_factory.mktemp("startup")
    settings = make_settings(data_dir, mail_mode=mode, base_url=base_url,
                             smtp_password=password, secret_key=key,
                             smtp_username=username, client_ip_header=header,
                             **RELAY)
    capsys.readouterr()
    create_app(settings)
    (line,) = capsys.readouterr().err.splitlines()
    assert line.startswith("NBU-SuperAssistant started: ")
    assert str(data_dir.resolve()) in line and base_url in line
    assert ("mail " + (mode or "console")) in line
    if mode in ("send", "owner"):
        assert "smtp.example.org:587 (starttls)" in line
        assert "pilot@example.org" in line
    assert (OWNER_EMAIL in line) == (mode == "owner")
    assert ("CF-Connecting-IP" in line) == bool(header)
    assert "the connection" in line
    for secret in (password, key, username):
        assert secret not in line


# --- 9. wsgi.py ---------------------------------------------------------------

# The subprocess reads the settings file the test names (or one that does
# not exist), never a .env.production in the clone, and an environment made
# here, never the shell's.
PRELUDE = ("import sys; from pathlib import Path; "
           "import superassistant.settings as s; "
           "s.SETTINGS_FILE = Path(sys.argv[1]); import wsgi")


def run_wsgi(tmp_path, variables, settings_file=None):
    env = {"PATH": os.environ.get("PATH", ""), "HOME": str(tmp_path / "home"),
           "PYTHONIOENCODING": "utf-8", "PYTHONDONTWRITEBYTECODE": "1"}
    env.update(variables)
    return subprocess.run(
        [sys.executable, "-c", PRELUDE,
         str(settings_file or tmp_path / "no-settings-file")],
        cwd=str(CLONE), env=env, capture_output=True, encoding="utf-8",
        timeout=120)


def test_wsgi_refuses_with_one_clean_line_and_status_3(tmp_path):
    result = run_wsgi(tmp_path, {
        "SUPERASSISTANT_DATA_DIR": str(tmp_path / "data"),
        "SUPERASSISTANT_BASE_URL":
            "https://pilot:s3cr3t-pw@nbu-superassistant.visiometrica.com"})
    assert result.returncode == 3, result.stderr
    (line,) = result.stderr.splitlines()
    assert line.startswith("NBU-SuperAssistant cannot start: ")
    assert "SUPERASSISTANT_BASE_URL" in line
    assert "Traceback" not in result.stderr
    assert "s3cr3t-pw" not in result.stderr + result.stdout
    assert not (tmp_path / "data").exists()


def test_wsgi_reads_the_settings_file_and_the_environment_wins(tmp_path):
    settings_file = write(tmp_path / ".env.production", [
        "SUPERASSISTANT_BASE_URL=ftp://from-the-file",
        "SUPERASSISTANT_DATA_DIR=" + str(tmp_path / "data"),
    ])
    refused = run_wsgi(tmp_path, {}, settings_file)
    assert refused.returncode == 3
    assert "ftp://from-the-file" in refused.stderr
    started = run_wsgi(tmp_path, {
        "SUPERASSISTANT_BASE_URL": HOSTED,
        "SUPERASSISTANT_MAIL_MODE": "send",
        "SUPERASSISTANT_SMTP_HOST": "smtp.example.org",
        "SUPERASSISTANT_MAIL_FROM": "pilot@example.org",
        "SUPERASSISTANT_SMTP_USERNAME": "relay-user-name",
        "SUPERASSISTANT_SMTP_PASSWORD": "relay-s3cr3t-pw",
        "SUPERASSISTANT_SECRET_KEY": "session-s3cr3t-key",
        "SUPERASSISTANT_CLIENT_IP_HEADER": "CF-Connecting-IP",
    }, settings_file)
    assert started.returncode == 0, started.stderr
    (line,) = started.stderr.splitlines()
    assert line.startswith("NBU-SuperAssistant started: ")
    assert str((tmp_path / "data").resolve()) in line      # from the file
    assert HOSTED in line                                   # the shell's
    assert "CF-Connecting-IP" in line and "pilot@example.org" in line
    for secret in ("s3cr3t", "relay-user-name"):
        assert secret not in started.stderr + started.stdout


# --- The journal never holds a token -----------------------------------------

@pytest.mark.parametrize("path, broken", [
    ("/link/SECRET-TOKEN-abc123", "superassistant.web.auth.signin"),
    ("/answer/SECRET-TOKEN-abc123/confirm",
     "superassistant.web.supervisor.supervision"),
])
def test_an_error_on_a_token_page_logs_its_route_not_its_token(
        tmp_path, outbox, monkeypatch, caplog, capsys, path, broken):
    """Opus 5.5's review of 0534b19, F5: the unit writes no access log
    because these addresses carry tokens, but Flask's own error log wrote
    "Exception on <path>" to the journal."""
    app = create_app(make_settings(tmp_path / "data"))
    module_path, _, name = broken.rpartition(".")
    module = importlib.import_module(module_path)

    class Broken(object):
        def __getattr__(self, attribute):
            raise RuntimeError("database is locked")

    monkeypatch.setattr(module, name, Broken())
    with caplog.at_level(logging.ERROR):
        response = app.test_client().get(path)
    assert response.status_code == 500
    logged = caplog.text + capsys.readouterr().err
    assert "SECRET-TOKEN" not in logged
    assert "database is locked" in logged        # the error itself is kept
    assert "<token>" in logged                    # and the route it was on


# --- The stylesheet's address follows its content ------------------------------

def test_the_stylesheet_address_carries_a_hash_of_the_file_served(tmp_path,
                                                                   outbox):
    """The interface restyle (11 October 2026): Cloudflare hands browsers the
    stylesheet with cache-control: max-age=14400, so after a deploy a browser
    would show the new pages with the old stylesheet for up to four hours,
    unless a stylesheet with other content has another address."""
    import hashlib
    import re
    client = create_app(make_settings(tmp_path / "data")).test_client()
    for page in ("/", "/staff/sign-in"):
        html = client.get(page).get_data(as_text=True)
        href = re.search(r'<link rel="stylesheet" href="([^"]+)"',
                         html).group(1)
        path, _, query = href.partition("?")
        assert path == "/static/style.css"
        served = client.get(href)
        assert served.status_code == 200
        assert query == "v=" + hashlib.sha256(served.data).hexdigest()[:12]
        served.close()

    class Copy(object):
        static_folder = str(tmp_path / "static")

    os.mkdir(Copy.static_folder)
    stylesheet = Path(Copy.static_folder) / "style.css"
    stylesheet.write_bytes(b"body { color: #222; }\n")
    before = web.style_version(Copy)
    stylesheet.write_bytes(b"body { color: #1f2933; }\n")
    assert web.style_version(Copy) != before
