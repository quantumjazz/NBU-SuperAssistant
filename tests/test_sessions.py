"""The schedule of sessions (constitution 5.13): requirement 4 of the
milestone-3 plan, built before the milestone (the owner, 16 October 2026:
"Yes, all of it").

- the sessions list's rules, over generated lists in any characters, and the
  starting list as the department's 2026/2027 schedule prints it;
- a session's date with its weekday, and a deadline, in Bulgarian, from any
  ISO date;
- which sessions are offered and which are marked passed on a given day in
  Sofia;
- a submission refused without a session or the tick, the session refused
  unless offered, both recorded and shown to the student and to staff, an
  earlier application showing „—“; staff correcting the session to any listed
  session, a correction like any other; who may see and change what;
- the first start after the update writing the list once; a database of the
  15 October version upgrading from several processes at once;
- the nightly copy holding both; no document printing either.

Everyone is invented.
"""

import io
import multiprocessing
import re
import shutil
import sqlite3
import tempfile
import traceback
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import docx
import pytest
from hypothesis import HealthCheck, example, given
from hypothesis import settings as hsettings
from hypothesis import strategies as st

from superassistant import (applications, db, documents, lists, sessions,
                            snapshot, texts)
from superassistant.web import StartupError, create_app
from tests.conftest import (LATER_SESSION, Clock, Client, Outbox, connect,
                            insert_application, make_account, make_settings,
                            prepare_data_dir, write_sessions)
from tests.test_application_flow import (THESIS_TAB_1, THESIS_TAB_2,
                                         as_staff, as_student, record_for,
                                         save)
from tests.test_documents import every_paragraph

RULE = hsettings(max_examples=150, deadline=None)
SLOW = hsettings(max_examples=20, deadline=None,
                 suppress_health_check=[HealthCheck.too_slow])

EXAM = {"name1": "Калина", "name2": "Иванова", "name3": "Стоева",
        "fn": "500003", "grad_type": "exam", "credits_declared": "1"}
TICKED = {"grad_session": "2027-01", "schedule_ack": "1"}

# The words, written out here rather than read from texts, as the oracle.
MONTHS = ["януари", "февруари", "март", "април", "май", "юни", "юли",
          "август", "септември", "октомври", "ноември", "декември"]
WEEKDAYS = ["понеделник", "вторник", "сряда", "четвъртък", "петък",
            "събота", "неделя"]
# A Tuesday, from the department's schedule: „26 януари 2027 г. (вторник)“.
ANCHOR = date(2027, 1, 26)


def weekday_of(day):
    """The weekday's name, counted from the schedule's Tuesday."""
    return WEEKDAYS[(1 + (day - ANCHOR).days) % 7]


def staff_client(new_client, settings, username="staff1"):
    return as_staff(new_client(), make_account(settings, username))


def row_of(page, number):
    return page.split('data-id="{}"'.format(number))[1].split("</tr>")[0]


def dd(page, element_id):
    found = re.search(r'<dd id="{}">(.*?)</dd>'.format(element_id), page,
                      re.S)
    return found.group(1) if found else None


# --- Dates in Bulgarian ------------------------------------------------------

@RULE
@given(day=st.dates(min_value=date(1000, 1, 1), max_value=date(2999, 12, 31)))
@example(day=ANCHOR)
@example(day=date(2026, 9, 26))
def test_a_sessions_date_and_a_deadline_from_any_date(day):
    shown = sessions.long_date(day)
    assert shown == "{} {} {} г. ({})".format(day.day, MONTHS[day.month - 1],
                                              day.year, weekday_of(day))
    assert sessions.deadline(day) == "до {} {} {} г.".format(
        day.day, MONTHS[day.month - 1], day.year)
    # Seven days later is the same weekday, the next day the next one.
    assert sessions.long_date(day + timedelta(days=7)).endswith(
        "({})".format(weekday_of(day)))


def test_the_starting_schedule_is_the_departments_2026_2027_schedule(
        tmp_path):
    prepare_data_dir(tmp_path / "data")
    loaded = lists.load(tmp_path / "data" / "lists")
    shown = [(row["code"], row["date"], row["deadlines"])
             for row in sessions.schedule(loaded, date(2026, 10, 16))]
    assert shown == [
        ("2026-04", "21 април 2026 г. (вторник)",
         ["до 14 ноември 2025 г.", "до 6 февруари 2026 г.",
          "до 6 февруари 2026 г."]),
        ("2026-07", "7 юли 2026 г. (вторник)",
         ["до 6 февруари 2026 г.", "до 30 април 2026 г.",
          "до 30 април 2026 г."]),
        ("2026-09", "26 септември 2026 г. (събота)",
         ["до 30 април 2026 г.", "до 17 юли 2026 г.", "до 17 юли 2026 г."]),
        ("2027-01", "26 януари 2027 г. (вторник)",
         ["до 11 септември 2026 г.", "до 13 ноември 2026 г.",
          "до 13 ноември 2026 г."]),
    ]
    assert (tmp_path / "data" / "lists" / lists.SESSIONS).read_text(
        encoding="utf-8").splitlines()[0] == ",".join(
        lists.HEADERS[lists.SESSIONS])


# --- The list's rules --------------------------------------------------------

def a_code():
    """A code as the owner may type one: any characters a document can
    hold, mixed scripts included, no line break, not blank."""
    return st.text(min_size=1, max_size=12).map(str.strip).filter(
        lambda code: code and not applications.forbidden_characters(code)
        and "\n" not in code and "\r" not in code)


@st.composite
def a_schedule(draw, max_size=6):
    """Sessions with distinct codes and dates, each deadline on or before
    its session's date; in any order."""
    days = draw(st.lists(st.dates(min_value=date(2020, 1, 1),
                                  max_value=date(2035, 12, 31)),
                         min_size=1, max_size=max_size, unique=True))
    codes = draw(st.lists(a_code(), min_size=len(days), max_size=len(days),
                          unique=True))
    rows = []
    for code, day in zip(codes, days):
        before = [day - timedelta(days=draw(st.integers(0, 400)))
                  for _ in range(3)]
        rows.append([code, day.isoformat()] + [d.isoformat() for d in before])
    return draw(st.permutations(rows))


def lists_with_sessions(rows, header=None):
    """A lists folder of the starting lists, its sessions list these rows."""
    folder = Path(tempfile.mkdtemp())
    lists.write_starter(folder, [name for name in lists.STARTER
                                 if name != lists.SESSIONS])
    import csv
    buffer = io.StringIO()
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(header or lists.HEADERS[lists.SESSIONS])
    for row in rows:
        writer.writerow(row)
    (folder / lists.SESSIONS).write_text(buffer.getvalue(), encoding="utf-8")
    return folder


@RULE
@given(rows=a_schedule())
def test_a_sessions_list_loads_in_date_order_whatever_its_order(rows):
    folder = lists_with_sessions(rows)
    try:
        loaded = lists.load(folder)
    finally:
        shutil.rmtree(str(folder))
    expected = sorted(rows, key=lambda row: row[1])
    assert list(loaded.sessions) == [row[0] for row in expected]
    for row in expected:
        session = loaded.sessions[row[0]]
        assert [session[key].isoformat() for key in lists.SESSION_DATES] \
            == row[1:]


def is_iso_date(text):
    """The oracle: some date writes itself exactly so."""
    try:
        return date(int(text[0:4]), int(text[5:7]),
                    int(text[8:10])).isoformat() == text
    except (ValueError, IndexError):
        return False


def a_cell():
    """Any one-line cell the list can hold."""
    return st.text(min_size=1, max_size=12).filter(
        lambda text: not applications.forbidden_characters(text)
        and "\n" not in text and "\r" not in text)


@RULE
@given(text=st.one_of(a_cell(),
                      st.dates().map(lambda d: d.strftime("%d.%m.%Y")),
                      st.dates().map(lambda d: "{}-{}-{}".format(
                          d.year, d.month, d.day)),
                      st.from_regex(r"[0-9]{4}-[0-9]{2}-[0-9]{2}",
                                    fullmatch=True),
                      st.dates().map(date.isoformat)),
       column=st.integers(1, 4))
@example(text="２０２７-01-26", column=1)
@example(text="2027-02-29", column=1)
@example(text="2027-01-26T00:00", column=1)
def test_a_date_not_written_yyyy_mm_dd_stops_the_start_naming_the_line(
        text, column):
    row = ["2027-01", "2027-01-26", "2026-09-11", "2026-11-13", "2026-11-13"]
    row[column] = text
    folder = lists_with_sessions([LATER_SESSION, row])
    try:
        if not is_iso_date(text.strip()):
            with pytest.raises(lists.ListError) as raised:
                lists.load(folder)
            assert (raised.value.filename, raised.value.line) == (
                lists.SESSIONS, 3)
            if text.strip():
                assert "YYYY-MM-DD" in str(raised.value)
        else:
            try:
                lists.load(folder)
            except lists.ListError as exc:
                # A valid date may still break another rule.
                assert exc.line == 3 and ("after the session" in str(exc)
                                          or "listed twice" in str(exc))
    finally:
        shutil.rmtree(str(folder))


@pytest.mark.parametrize("rows, line, words", [
    ([LATER_SESSION, LATER_SESSION[:1] + ["2027-01-26", "2026-09-11",
                                          "2026-11-13", "2026-11-13"]],
     3, "used twice"),
    ([LATER_SESSION, ["другa", LATER_SESSION[1], "2026-09-11", "2026-11-13",
                      "2026-11-13"]], 3, "listed twice"),
    ([["2027-01", "2027-01-26", "2027-01-27", "2026-11-13", "2026-11-13"]],
     2, "after the session's date"),
    ([["2027-01", "2027-01-26", "2026-09-11", "2026-11-13", "2027-02-01"]],
     2, "after the session's date"),
    ([["2027-01", "2027-01-26", "2026-09-11", "2026-11-13"]], 2,
     "expected 5 columns"),
    ([["2027-01", "2027-01-26", "", "2026-11-13", "2026-11-13"]], 2,
     "a column is empty"),
])
def test_a_sessions_list_breaking_a_rule_stops_the_start_naming_the_line(
        rows, line, words):
    folder = lists_with_sessions(rows)
    try:
        with pytest.raises(lists.ListError) as raised:
            lists.load(folder)
    finally:
        shutil.rmtree(str(folder))
    assert (raised.value.filename, raised.value.line) == (lists.SESSIONS,
                                                          line)
    assert words in str(raised.value)


def test_a_changed_header_stops_the_start():
    folder = lists_with_sessions([LATER_SESSION], header=[
        "код", "дата", "теми", "изпит", "тези"])
    try:
        with pytest.raises(lists.ListError) as raised:
            lists.load(folder)
    finally:
        shutil.rmtree(str(folder))
    assert raised.value.line == 1 and "header must be" in str(raised.value)


def test_a_session_an_application_holds_must_stay_listed(settings, clock):
    number = insert_application(settings, "held@example.org",
                                submitted=False, grad_session="2026-07")
    create_app(settings)                                  # listed: starts
    write_sessions(settings.lists_dir, [LATER_SESSION])
    with pytest.raises(StartupError) as raised:
        create_app(settings)
    assert lists.SESSIONS in str(raised.value)
    assert "'2026-07'" in str(raised.value) and str(number) in str(
        raised.value)


# --- Offered and passed, by the day in Sofia ---------------------------------

def schedule_of(rows):
    return lists.Lists([], {}, {}, {}, dict(
        (row[0], {"date": date.fromisoformat(row[1]),
                  "topics": date.fromisoformat(row[2]),
                  "exam": date.fromisoformat(row[3]),
                  "theses": date.fromisoformat(row[4])})
        for row in sorted(rows, key=lambda row: row[1])))


@RULE
@given(rows=a_schedule(), moment=st.datetimes(
    min_value=datetime(2019, 12, 1), max_value=datetime(2036, 2, 1),
    timezones=st.just(timezone.utc)))
# Sofia is two hours ahead in January: 22:00 UTC is already the next day.
@example(rows=[["j", "2027-01-26", "2026-09-11", "2026-11-13",
                "2026-11-13"]],
         moment=datetime(2027, 1, 25, 22, 30, tzinfo=timezone.utc))
@example(rows=[["j", "2027-01-26", "2026-09-11", "2026-11-13",
                "2026-11-13"]],
         moment=datetime(2027, 1, 26, 21, 59, 59, tzinfo=timezone.utc))
@example(rows=[["j", "2027-01-26", "2026-09-11", "2026-11-13",
                "2026-11-13"]],
         moment=datetime(2027, 1, 26, 22, 0, tzinfo=timezone.utc))
def test_sessions_dated_today_or_later_are_offered_and_earlier_ones_passed(
        rows, moment):
    loaded = schedule_of(rows)
    clock = Clock()
    clock.moment = moment
    db.set_clock(clock)
    try:
        offered = sessions.offered(loaded)
        shown = sessions.schedule(loaded)
    finally:
        db.set_clock(None)
    # Sofia: UTC+2 in winter, UTC+3 from the last Sunday of March to the
    # last Sunday of October, as the zone database has it.
    from zoneinfo import ZoneInfo
    today = moment.astimezone(ZoneInfo("Europe/Sofia")).date()
    by_date = sorted(rows, key=lambda row: row[1])
    assert offered == [row[0] for row in by_date
                       if date.fromisoformat(row[1]) >= today]
    assert [(row["code"], row["passed"]) for row in shown] == [
        (row[0], date.fromisoformat(row[1]) < today) for row in by_date]
    if moment == datetime(2027, 1, 25, 22, 30, tzinfo=timezone.utc):
        assert offered == ["j"]                 # 00:30 on the day, Sofia
    if moment == datetime(2027, 1, 26, 22, 0, tzinfo=timezone.utc):
        assert offered == []                    # midnight after, Sofia


# --- The student's application ----------------------------------------------

def test_tab_1_shows_the_schedule_and_offers_only_sessions_not_passed(
        client):
    as_student(client, "tab1@example.org")
    page = client.get("/application").get_data(as_text=True)
    table = page.split('id="schedule"')[1].split("</table>")[0]
    rows = re.findall(r'<tr class="(passed)?" data-session="([^"]+)">', table)
    assert rows == [("passed", "2026-04"), ("passed", "2026-07"),
                    ("passed", "2026-09"), ("", "2027-01")]
    for heading in texts.SCHEDULE_COLUMNS:
        assert heading in table
    assert table.count(texts.SCHEDULE_PASSED) == 3
    assert "26 януари 2027 г. (вторник)" in table
    assert "до 13 ноември 2026 г." in table
    assert texts.SCHEDULE_NOTE in page and texts.ACK_SCHEDULE in page
    assert re.findall(r'name="grad_session" value="([^"]+)"', page) == [
        "2027-01"]
    assert re.search(r'<input type="checkbox" id="schedule_ack" '
                     r'name="schedule_ack"', page)
    # For both types, outside the thesis fields; before the buttons.
    thesis = page.split('id="thesis-fields"')[1].split('id="session-card"')[0]
    assert "grad_session" not in thesis
    assert page.index('id="session-card"') < page.index(
        'id="credits_declared"') < page.index('name="action"')


def test_with_no_session_ahead_the_page_says_so_and_nothing_submits(
        client, settings, clock, outbox):
    clock.moment = datetime(2027, 1, 26, 22, 0, tzinfo=timezone.utc)
    as_student(client, "late@example.org")
    page = client.get("/application").get_data(as_text=True)
    assert 'name="grad_session"' not in page
    assert texts.SESSION_NONE_OFFERED in page
    assert page.count(texts.SCHEDULE_PASSED) == 4
    response = save(client, 1, dict(EXAM, schedule_ack="1"), "submit")
    assert response.status_code == 400
    assert re.search(r'id="grad_session-error">' + re.escape(
        texts.REFUSED_SESSION), response.get_data(as_text=True))
    assert record_for(settings, "late@example.org")["submitted_at"] is None


@pytest.mark.parametrize("left_out", [("grad_session",), ("schedule_ack",),
                                      ("grad_session", "schedule_ack")])
def test_a_state_exam_without_the_session_or_the_tick_is_not_submitted(
        client, settings, outbox, clock, left_out):
    as_student(client, "exam-session@example.org")
    data = dict(EXAM, **TICKED)
    for key in left_out:
        data.pop(key)
    response = save(client, 1, data, "submit")
    page = response.get_data(as_text=True)
    assert response.status_code == 400
    if "grad_session" in left_out:
        assert re.search(r'id="grad_session-error">' + re.escape(
            texts.REFUSED_SESSION), page)
    if "schedule_ack" in left_out:
        assert re.search(r'id="schedule_ack-error">' + re.escape(
            texts.TICK_REQUIRED), page)
    assert ("grad_session-error" in page) == ("grad_session" in left_out)
    assert ("schedule_ack-error" in page) == ("schedule_ack" in left_out)
    record = record_for(settings, "exam-session@example.org")
    assert record["submitted_at"] is None and record["schedule_ack_at"] is None
    assert record["name1"] == "Калина"            # the draft is still saved
    assert save(client, 1, dict(EXAM, **TICKED), "submit").status_code == 302
    record = record_for(settings, "exam-session@example.org")
    assert (record["grad_session"], record["schedule_ack"]) == ("2027-01", 1)
    assert record["schedule_ack_at"] == record["submitted_at"] == \
        clock().isoformat(timespec="seconds")


@pytest.mark.parametrize("left_out", [("grad_session",), ("schedule_ack",)])
def test_a_thesis_without_the_session_or_the_tick_goes_back_to_tab_1(
        client, settings, outbox, clock, left_out):
    as_student(client, "thesis-session@example.org")
    data = dict(THESIS_TAB_1)
    for key in left_out:
        data.pop(key)
    assert save(client, 1, data, "next").status_code == 302
    response = save(client, 2, THESIS_TAB_2, "submit")
    page = response.get_data(as_text=True)
    assert response.status_code == 400
    assert '<input type="hidden" name="tab" value="1">' in page
    assert "{}-error".format(left_out[0]) in page
    assert outbox.messages == []                  # no request to a supervisor
    assert save(client, 1, THESIS_TAB_1, "next").status_code == 302
    assert save(client, 2, THESIS_TAB_2, "submit").status_code == 302
    record = record_for(settings, "thesis-session@example.org")
    assert record["grad_session"] == "2027-01"
    assert record["schedule_ack_at"] == record["submitted_at"]
    assert len(outbox.messages) == 1


@pytest.mark.parametrize("code", ["2026-09", "2026-04", "няма-такава",
                                  "2027-01 ", "<b>"])
def test_a_session_not_offered_is_refused_when_saved(client, settings, code):
    as_student(client, "refused-session@example.org")
    response = save(client, 1, dict(EXAM, grad_session=code,
                                    schedule_ack="1"))
    if code.strip() == "2027-01":                 # ends trimmed, as typed
        assert response.status_code == 302
        return
    assert response.status_code == 400
    assert re.search(r'id="grad_session-error">' + re.escape(
        texts.REFUSED_SESSION), response.get_data(as_text=True))
    record = record_for(settings, "refused-session@example.org")
    assert record is None or record["grad_session"] == ""


def test_a_draft_whose_session_has_passed_is_not_submitted(
        settings, clock, outbox):
    # The lists are read at the start: this one before it.
    write_sessions(settings.lists_dir, [
        ["2027-01", "2027-01-26", "2026-09-11", "2026-11-13", "2026-11-13"],
        LATER_SESSION])
    client = as_student(Client(create_app(settings).test_client()),
                        "passed-draft@example.org")
    assert save(client, 1, dict(EXAM, **TICKED)).status_code == 302
    clock.moment = datetime(2027, 1, 27, 9, 0, tzinfo=timezone.utc)
    page = client.get("/application").get_data(as_text=True)
    assert re.findall(r'name="grad_session" value="([^"]+)"', page) == [
        LATER_SESSION[0]]
    response = save(client, 1, dict(EXAM, **TICKED), "submit")
    assert response.status_code == 400
    assert record_for(settings, "passed-draft@example.org")[
        "submitted_at"] is None
    # Even a submission that sends no form fields at all.
    response = client.post("/application", data={"tab": "2",
                                                  "action": "submit"})
    assert response.status_code == 400
    assert record_for(settings, "passed-draft@example.org")[
        "submitted_at"] is None
    assert save(client, 1, dict(EXAM, grad_session=LATER_SESSION[0],
                                schedule_ack="1"), "submit").status_code == 302


def test_the_session_and_the_tick_are_saved_with_the_draft_and_shown_again(
        client, settings):
    as_student(client, "draft-session@example.org")
    save(client, 1, dict(EXAM, **TICKED))
    record = record_for(settings, "draft-session@example.org")
    assert (record["grad_session"], record["schedule_ack"],
            record["schedule_ack_at"]) == ("2027-01", 1, None)
    page = client.get("/application").get_data(as_text=True)
    assert re.search(r'value="2027-01" checked', page)
    assert re.search(r'id="schedule_ack"[^>]*checked', page)
    refused = save(client, 1, dict(EXAM, name1="Kалина", **TICKED))
    assert refused.status_code == 400
    shown = refused.get_data(as_text=True)
    assert re.search(r'value="2027-01" checked', shown)
    assert re.search(r'id="schedule_ack"[^>]*checked', shown)
    save(client, 1, EXAM)
    record = record_for(settings, "draft-session@example.org")
    assert (record["grad_session"], record["schedule_ack"]) == ("", 0)


def test_the_submitted_page_shows_the_session_the_tick_and_the_schedule(
        client, settings, outbox):
    as_student(client, "shown@example.org")
    save(client, 1, dict(EXAM, **TICKED), "submit")
    page = client.get("/application").get_data(as_text=True)
    assert dd(page, "chosen-session") == "26 януари 2027 г. (вторник)"
    assert dd(page, "acknowledged") == "да"
    assert 'id="schedule"' in page and texts.SCHEDULE_NOTE in page
    assert 'name="grad_session"' not in page and "schedule_ack" not in page
    # Nothing the student sends now changes the session.
    client.post("/application", data=dict(EXAM, grad_session="2026-09",
                                          tab="1", action="save"))
    assert record_for(settings, "shown@example.org")[
        "grad_session"] == "2027-01"


# --- Staff ------------------------------------------------------------------

def test_staff_see_the_session_and_the_tick_and_an_earlier_one_shows_none(
        client, new_client, settings, outbox):
    as_student(client, "session-staff@example.org")
    save(client, 1, dict(EXAM, **TICKED), "submit")
    chosen = record_for(settings, "session-staff@example.org")["id"]
    earlier = insert_application(settings, "pilot@example.org",
                                 grad_type="exam", name1="Пилот",
                                 name2="Тестов", name3="Студент", fn="F1")
    viewer = staff_client(new_client, settings)
    table = viewer.get("/staff").get_data(as_text=True)
    assert "<th>Сесия</th>" in table and "<th>График</th>" in table
    for number, session, ticked in (
            (chosen, "26 януари 2027 г. (вторник)", "да"),
            (earlier, "—", "—")):
        row = row_of(table, number)
        assert '<td class="session">{}</td>'.format(session) in row
        assert '<td class="acknowledged">{}</td>'.format(ticked) in row
        page = viewer.get("/staff/application/{}".format(number)).get_data(
            as_text=True)
        assert dd(page, "session") == session
        assert dd(page, "acknowledged") == ticked


def test_staff_correct_the_session_to_any_listed_session(
        new_client, settings, clock):
    staff = make_account(settings, "staff1")
    viewer = as_staff(new_client(), staff)
    number = insert_application(settings, "corrected@example.org",
                                grad_type="exam", name1="Ана", name2="Б",
                                name3="В", fn="F2")
    url = "/staff/application/{}".format(number)
    page = viewer.get(url).get_data(as_text=True)
    options = re.findall(r'<option value="([^"]*)"[^>]*>([^<]*)</option>',
                         page.split('id="grad_session"')[1].split(
                             "</select>")[0])
    assert options == [
        ("", "—"),
        ("2026-04", "21 април 2026 г. (вторник) – отминала"),
        ("2026-07", "7 юли 2026 г. (вторник) – отминала"),
        ("2026-09", "26 септември 2026 г. (събота) – отминала"),
        ("2027-01", "26 януари 2027 г. (вторник)")]
    steps = ["2027-01", "2026-09", "2026-09", "2026-04"]
    for code in steps:
        clock.advance(minutes=1)
        assert viewer.post(url + "/session",
                           data={"grad_session": code}).status_code == 302
    connection = connect(settings)
    try:
        assert applications.get(connection, number)["grad_session"] == \
            "2026-04"
        made = [(c["field"], c["old_value"], c["new_value"], c["username"])
                for c in applications.corrections_of(connection, number)]
    finally:
        connection.close()
    # The repeated choice changed nothing and left no row.
    assert made == [("grad_session", "", "2027-01", "staff1"),
                    ("grad_session", "2027-01", "2026-09", "staff1"),
                    ("grad_session", "2026-09", "2026-04", "staff1")]
    page = viewer.get(url).get_data(as_text=True)
    assert "Сесия: от „—“ на „26 януари 2027 г. (вторник)“" in page
    assert ("Сесия: от „26 септември 2026 г. (събота)“ на „21 април 2026 г. "
            "(вторник)“") in page
    assert dd(page, "session") == "21 април 2026 г. (вторник)"


@pytest.mark.parametrize("code", ["", "2028-01", "2027-01 x"])
def test_a_session_not_listed_is_not_recorded(new_client, settings, code):
    viewer = staff_client(new_client, settings)
    number = insert_application(settings, "unlisted@example.org",
                                grad_type="exam", grad_session="2027-01")
    response = viewer.post("/staff/application/{}/session".format(number),
                           data={"grad_session": code})
    assert response.status_code == 400
    assert re.search(r'id="session-error">' + re.escape(
        texts.REFUSED_SESSION), response.get_data(as_text=True))
    connection = connect(settings)
    try:
        assert applications.get(connection, number)["grad_session"] == \
            "2027-01"
        assert applications.corrections_of(connection, number) == []
    finally:
        connection.close()


def test_a_session_correction_in_the_bin_changes_nothing(new_client,
                                                         settings):
    viewer = staff_client(new_client, settings)
    number = insert_application(settings, "binned@example.org",
                                grad_type="exam", grad_session="2027-01")
    url = "/staff/application/{}".format(number)
    assert viewer.post(url + "/remove", data={
        "reason": "other"}).status_code == 302
    page = viewer.get(url).get_data(as_text=True)
    assert 'id="session-form"' not in page
    assert dd(page, "session") == "26 януари 2027 г. (вторник)"
    response = viewer.post(url + "/session", data={"grad_session": "2026-09"})
    assert response.status_code == 302 and response.headers[
        "Location"].endswith("/staff/bin")
    connection = connect(settings)
    try:
        assert applications.get(connection, number)["grad_session"] == \
            "2027-01"
        assert applications.corrections_of(connection, number) == []
    finally:
        connection.close()


def test_a_type_correction_neither_needs_nor_changes_the_session(
        new_client, settings, outbox):
    number = insert_application(settings, "type@example.org",
                                grad_type="exam", name1="Ана",
                                name2="Бойкова", name3="Вълчева",
                                fn="F600002")
    viewer = staff_client(new_client, settings)
    base = "/staff/application/{}".format(number)
    data = dict(THESIS_TAB_1)
    data.update(THESIS_TAB_2)
    for key in ("grad_type", "professor", "credits_declared", "fn",
                "grad_session", "schedule_ack"):
        data.pop(key)
    for field, value in data.items():
        assert viewer.post(base + "/correct", data={
            "field": field, "value": value}).status_code == 302
    assert viewer.post(base + "/type", data={
        "grad_type": "thesis", "professor": "ivanov"}).status_code == 302
    connection = connect(settings)
    try:
        row = applications.get(connection, number)
    finally:
        connection.close()
    assert row["grad_type"] == "thesis"
    assert (row["grad_session"], row["schedule_ack"],
            row["schedule_ack_at"]) == ("", 0, None)


# --- Who sees and changes what ----------------------------------------------

def test_only_staff_see_or_correct_a_session(client, new_client, settings,
                                             outbox):
    as_student(client, "first@example.org")
    save(client, 1, dict(EXAM, **TICKED), "submit")
    first = record_for(settings, "first@example.org")["id"]
    staff_client(new_client, settings).post(
        "/staff/application/{}/session".format(first),
        data={"grad_session": "2026-09"})
    other = as_student(new_client(), "second@example.org")
    page = other.get("/application").get_data(as_text=True)
    assert "Калина" not in page and 'id="chosen-session"' not in page
    unapproved = as_staff(new_client(), make_account(
        settings, "waiting", approved=False))
    for viewer in (other, unapproved, new_client()):
        for url in ("/staff", "/staff/application/{}".format(first)):
            response = viewer.get(url)
            assert response.status_code == 302
            assert texts.ACKNOWLEDGED not in response.get_data(as_text=True)
        response = viewer.post("/staff/application/{}/session".format(first),
                               data={"grad_session": "2027-01"})
        assert response.status_code == 302
    assert record_for(settings, "first@example.org")[
        "grad_session"] == "2026-09"


# --- The first start after the update, and the migration ---------------------

def test_the_first_start_after_the_update_writes_the_sessions_list_once(
        tmp_path, clock):
    """The pilot as the update finds it: the four lists, written and
    recorded at its first start, and no sessions list."""
    data_dir = tmp_path / "data"
    prepare_data_dir(data_dir)
    sessions_file = data_dir / "lists" / lists.SESSIONS
    sessions_file.unlink()
    settings = make_settings(data_dir)
    connection = connect(settings)
    with db.transaction(connection):
        connection.execute("INSERT INTO installation VALUES ('lists', ?)",
                           (db.now(),))
    connection.close()
    create_app(settings)
    assert sessions_file.read_text(encoding="utf-8").splitlines()[-1] == \
        "2027-01,2027-01-26,2026-09-11,2026-11-13,2026-11-13"
    connection = connect(settings)
    assert [r["key"] for r in connection.execute(
        "SELECT key FROM installation ORDER BY key")] == [
        "lists", "sessions list"]
    connection.close()
    # The owner's edit is kept by every later start.
    write_sessions(data_dir / "lists", [LATER_SESSION])
    edited = sessions_file.read_text(encoding="utf-8")
    loaded = create_app(settings).extensions["superassistant"]["lists"]
    assert list(loaded.sessions) == [LATER_SESSION[0]]
    assert sessions_file.read_text(encoding="utf-8") == edited
    # Missing later, it is an error to report, never written again.
    sessions_file.unlink()
    with pytest.raises(StartupError) as raised:
        create_app(settings)
    assert lists.SESSIONS in str(raised.value) and "missing" in str(
        raised.value)
    assert not sessions_file.exists()


def _migrate_when_released(barrier, path, results):
    try:
        barrier.wait(timeout=60)
        db.migrate(path)
        results.put("ok")
    except BaseException:
        results.put(traceback.format_exc())


@pytest.mark.parametrize("round_number", range(3))
def test_schema_5_upgrades_from_several_processes_keeping_every_row(
        tmp_path, round_number):
    """A database of the 15 October version, as the pilot's: a submitted
    application with its tick, a draft, a request and a check."""
    path = tmp_path / "superassistant.sqlite3"
    connection = sqlite3.connect(str(path))
    connection.executescript(";".join(db.MIGRATIONS[:5])
                             + ";PRAGMA user_version = 5;")
    connection.executescript("""
        INSERT INTO accounts (username, username_key, email, email_key,
            algorithm, salt, iterations, dklen, hash, session_tag,
            created_at, approved_at) VALUES ('staff', 'staff',
            's@example.org', 's@example.org', 'none', '00', 1, 1, '00',
            'tag', 't', 't');
        INSERT INTO applications (email, email_key, created_at, updated_at,
            submitted_at, grad_type, name1, fn, credits_declared,
            credits_declared_at) VALUES ('old@example.org',
            'old@example.org', 't', 't', 't', 'thesis', 'Старо', 'F1', 1,
            't');
        INSERT INTO applications (email, email_key, created_at, updated_at,
            name1) VALUES ('draft@example.org', 'draft@example.org', 't',
            't', 'Чернова');
        INSERT INTO requests (application_id, created_at, sup_email,
            token_hash, sent_at, answer, answered_at) VALUES (1, 't',
            'p@example.org', 'h', 't', 'confirm', 't');
        INSERT INTO checks (application_id, result, by_account, at) VALUES
            (1, 'passed', 1, 't');
    """)
    connection.commit()
    connection.close()
    context = multiprocessing.get_context("spawn")
    barrier = context.Barrier(4)
    results = context.Queue()
    workers = [context.Process(target=_migrate_when_released,
                               args=(barrier, str(path), results))
               for _ in range(4)]
    for worker in workers:
        worker.start()
    outcomes = [results.get(timeout=120) for _ in workers]
    for worker in workers:
        worker.join(timeout=60)
    assert outcomes == ["ok"] * 4, "\n".join(o for o in outcomes if o != "ok")
    connection = db.connect(path)
    try:
        assert connection.execute("PRAGMA user_version").fetchone()[0] == 6
        rows = [tuple(r) for r in connection.execute(
            "SELECT name1, submitted_at, credits_declared_at, grad_session, "
            "schedule_ack, schedule_ack_at FROM applications ORDER BY id")]
        assert rows == [("Старо", "t", "t", "", 0, None),
                        ("Чернова", None, None, "", 0, None)]
        assert connection.execute(
            "SELECT answer FROM requests").fetchone()[0] == "confirm"
        assert connection.execute(
            "SELECT result FROM checks").fetchone()[0] == "passed"
    finally:
        connection.close()


# --- The nightly copy, and the documents ------------------------------------

def test_the_nightly_copy_holds_the_session_and_the_tick(client, settings,
                                                         outbox):
    as_student(client, "copy@example.org")
    save(client, 1, dict(EXAM, **TICKED), "submit")
    chosen = record_for(settings, "copy@example.org")["id"]
    earlier = insert_application(settings, "earlier@example.org",
                                 grad_type="exam", name1="Пилот", fn="F1")
    connection = connect(settings)
    try:
        rows, _ = snapshot.table(connection, lists.load(settings.lists_dir))
    finally:
        connection.close()
    column = dict((name, i) for i, name in enumerate(rows[0]))
    assert all(len(row) == len(rows[0]) for row in rows)
    by_number = dict((row[0], row) for row in rows[1:])
    for number, session, ticked in (
            (chosen, "26 януари 2027 г. (вторник)", "да"),
            (earlier, "—", "не")):
        row = by_number[number]
        assert row[column["Сесия"]] == session
        assert row[column["Запознат(а) с графика на сесиите"]] == ticked


def test_no_document_prints_the_session_or_the_tick(settings):
    loaded = lists.load(settings.lists_dir)
    record = {"id": 1, "email": "a@example.org", "grad_type": "thesis",
              "name1": "Ана", "name2": "Бойкова", "name3": "Вълчева",
              "fn": "F1", "phone": "1", "programme": "BSNADM01",
              "topic": "Тема", "average_grade": "5", "professor": "ivanov",
              "sup_title": "", "sup_name": "", "sup_email": "",
              "credits_declared": 1,
              "credits_declared_at": "2026-10-13T09:00:00+00:00",
              "submitted_at": "2026-10-13T09:00:00+00:00"}
    for field in db.PROPOSAL_FIELDS:
        record[field] = "Раздел"

    def text(make, chosen):
        data = make(dict(record, grad_session="2027-01" if chosen else "",
                         schedule_ack=int(chosen),
                         schedule_ack_at=record["submitted_at"] if chosen
                         else None), loaded)
        return [p.text for p in every_paragraph(
            docx.Document(io.BytesIO(data)))]

    for make in (documents.zaiavlenie, documents.prilozhenie2):
        for grad_type in ("thesis", "exam"):
            record["grad_type"] = grad_type
            assert text(make, True) == text(make, False)
            joined = "\n".join(text(make, True))
            assert "януари 2027" not in joined
            assert texts.ACK_SCHEDULE[:30] not in joined


# --- Codes in any characters, through the pages -----------------------------

@SLOW
@given(code=a_code())
@example(code="Сесия-Jan <&\"'>")
@example(code="ЯНУАРИ 2027")
def test_a_code_in_any_characters_is_chosen_recorded_and_shown(code):
    path = Path(tempfile.mkdtemp())
    clock = Clock()
    box = Outbox()
    db.set_clock(clock)
    from superassistant import mail
    mail.set_relay(box)
    try:
        prepare_data_dir(path / "data")
        write_sessions(path / "data" / "lists", [
            [code] + LATER_SESSION[1:]])
        settings = make_settings(path / "data")
        app = create_app(settings)
        app.config["TESTING"] = True
        student = as_student(Client(app.test_client()), "any@example.org")
        page = student.get("/application").get_data(as_text=True)
        assert "30 юни 2099 г. (вторник)" in page
        response = save(student, 1, dict(EXAM, grad_session=code,
                                         schedule_ack="1"), "submit")
        assert response.status_code == 302
        record = record_for(settings, "any@example.org")
        assert record["grad_session"] == code and record["submitted_at"]
        staff = as_staff(Client(app.test_client()),
                         make_account(settings, "staff1"))
        page = staff.get("/staff/application/{}".format(
            record["id"])).get_data(as_text=True)
        assert dd(page, "session") == "30 юни 2099 г. (вторник)"
        assert staff.post("/staff/application/{}/session".format(
            record["id"]), data={"grad_session": code}).status_code == 302
    finally:
        db.set_clock(None)
        mail.set_relay(None)
        shutil.rmtree(str(path), ignore_errors=True)
