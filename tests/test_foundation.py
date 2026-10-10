"""The start-up checks and the mail modes (NOW.md requirements 5 and 6,
proof 1's list bullet, proof 4's mail modes)."""

import io

import pytest

from superassistant import lists, mail
from superassistant.settings import Settings
from superassistant.web import StartupError, create_app
from tests.conftest import make_account, make_settings, prepare_data_dir


def test_starts_from_an_empty_directory(tmp_path):
    settings = make_settings(tmp_path / "empty")
    app = create_app(settings)
    assert app is not None
    loaded = lists.load(settings.lists_dir)
    assert loaded.programme_faculty("УБП-ДО")["name"].startswith(
        "Факултет за дистанционно")
    assert loaded.programme_faculty("АУ-РО")["name"] == "Бакалавърски факултет"
    assert loaded.programme_faculty("БА-РО")["name"] == "Магистърски факултет"
    assert loaded.professors == {}


@pytest.mark.parametrize("filename, text, line", [
    (lists.PROGRAMMES, "код,степен,програма,форма,факултет\n"
                       "X,БП,Програма,РО,НЯМА\n", 2),
    (lists.PROGRAMMES, "код,степен,програма,форма,факултет\n"
                       "X,БП,Програма,РО,БФ\nY,ХХ,Програма,РО,БФ\n", 3),
    (lists.TITLES, "title\nдоц. д-р\n", 1),
    (lists.PROFESSORS, "код,звание,име,email\nа,доц. д-р,Име Фамилия\n", 2),
    (lists.PROFESSORS, "код,звание,име,email\nа,акад.,Име Фамилия,a@b.bg\n",
     2),
])
def test_a_list_with_an_error_stops_the_start(tmp_path, filename, text,
                                              line):
    data_dir = tmp_path / "data"
    prepare_data_dir(data_dir)
    (data_dir / "lists" / filename).write_text(text, encoding="utf-8")
    with pytest.raises(StartupError) as raised:
        create_app(make_settings(data_dir))
    assert filename in str(raised.value)
    assert "line {}".format(line) in str(raised.value)


def test_a_list_lacking_an_entry_in_use_stops_the_start(tmp_path):
    from tests.conftest import insert_application, write_professors
    data_dir = tmp_path / "data"
    prepare_data_dir(data_dir)
    settings = make_settings(data_dir)
    number = insert_application(settings, "s@example.org",
                                professor="georgieva")
    write_professors(data_dir / "lists", rows=[
        ["ivanov", "доц. д-р", "Петър Иванов", "p.ivanov@example.org"]])
    with pytest.raises(StartupError) as raised:
        create_app(settings)
    assert lists.PROFESSORS in str(raised.value)
    assert "georgieva" in str(raised.value)
    assert str(number) in str(raised.value)


def test_an_owner_setting_naming_no_account_stops_the_start(tmp_path):
    data_dir = tmp_path / "data"
    prepare_data_dir(data_dir)
    with pytest.raises(StartupError):
        create_app(make_settings(data_dir, owner_username="nobody"))
    settings = make_settings(data_dir, owner_username="nobody")
    make_account(settings, username="nobody", approved=False)
    assert create_app(settings) is not None


def test_owner_mode_sends_to_the_owner_with_the_recipient_on_top(
        settings, outbox):
    mail.send(settings, mail.Message("someone@example.org", "Тема", "Текст",
                                     "<p>Текст</p>"))
    (sent,) = outbox.messages
    assert sent.envelope_to == settings.owner_email
    assert sent.intended == "someone@example.org"
    assert "Текст" in sent.text and "someone@example.org" in sent.html


@pytest.mark.parametrize("mode", ["console", ""])
def test_console_and_unset_modes_print_and_send_nothing(tmp_path, outbox,
                                                         mode):
    settings = make_settings(tmp_path, mail_mode=mode)
    out = io.StringIO()
    mail.send(settings, mail.Message("someone@example.org", "Тема", "Текст"),
              out=out)
    assert outbox.messages == []
    assert "someone@example.org" in out.getvalue()
    assert "Текст" in out.getvalue()


def test_no_mode_sends_to_the_intended_recipient(tmp_path):
    assert Settings(tmp_path, mail_mode="send").problem()
    assert Settings(tmp_path, mail_mode="owner").problem()   # no owner email


def test_a_refused_message_raises(settings, outbox):
    outbox.refuse = True
    with pytest.raises(mail.MailFailed):
        mail.send(settings, mail.Message("someone@example.org", "Т", "Т"))


def test_no_wording_is_defined_twice():
    """A name assigned twice in texts.py silently replaces the first: the
    staff registration page once showed the student's email label so."""
    import ast
    import collections
    from pathlib import Path
    source = (Path(__file__).resolve().parent.parent / "superassistant"
              / "texts.py").read_text(encoding="utf-8")
    seen = collections.Counter(
        target.id for node in ast.parse(source).body
        if isinstance(node, ast.Assign) for target in node.targets
        if isinstance(target, ast.Name))
    assert [name for name, count in seen.items() if count > 1] == []


def test_every_page_says_where_mail_goes(tmp_path, client):
    from superassistant import texts
    page = client.get("/").get_data(as_text=True)
    assert texts.MAIL_DEV_OWNER.format("owner@example.org") in page
    settings = make_settings(tmp_path / "console", mail_mode="")
    console = create_app(settings).test_client()
    assert texts.MAIL_DEV_CONSOLE in console.get("/").get_data(as_text=True)


def test_a_waiting_account_is_told_how_an_owner_is_named(client, settings):
    from superassistant import texts
    response = client.post("/staff/register", data={
        "username": "first", "email": "first@example.org",
        "password": "парола-1", "password2": "парола-1"})
    assert texts.NO_OWNER_YET in response.get_data(as_text=True)
    response = client.post("/staff/sign-in", data={"login": "first",
                                                   "password": "парола-1"})
    assert response.status_code == 403
    assert texts.NO_OWNER_YET in response.get_data(as_text=True)


def test_with_an_owner_named_the_hint_is_not_shown(tmp_path):
    from superassistant import texts
    from tests.conftest import Client
    data_dir = tmp_path / "data"
    prepare_data_dir(data_dir)
    settings = make_settings(data_dir, owner_username="boss")
    make_account(settings, "boss", approved=False)
    client = Client(create_app(settings).test_client())
    response = client.post("/staff/register", data={
        "username": "second", "email": "second@example.org",
        "password": "парола-2", "password2": "парола-2"})
    page = response.get_data(as_text=True)
    assert texts.STAFF_REGISTERED_WAITING in page
    assert texts.NO_OWNER_YET not in page
