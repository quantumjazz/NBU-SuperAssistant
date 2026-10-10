"""Regressions for Codex's review of milestone 1 at aa278fc (M1-C3 to M1-C9;
M1-C1 and M1-C2 are browser regressions in tests/browser).

Invented people, temporary data and the fake relay only.
"""

import io
import re

import pytest
from docx import Document
from hypothesis import HealthCheck, given, settings as hsettings
from hypothesis import strategies as st

from superassistant import applications, db, limits, lists, reports
from superassistant.web import StartupError, create_app
from tests.conftest import (Client, connect, make_account, make_settings,
                            prepare_data_dir)
from tests.test_application_flow import (THESIS_TAB_1, THESIS_TAB_2,
                                         as_staff, as_student, link_from,
                                         record_for, save, submit_thesis)


# --- M1-C4: staff correct the graduation type -------------------------------

def submit_exam(client, address, extra=None):
    as_student(client, address)
    fields = {"name1": "Калина", "name2": "Иванова", "name3": "Стоева",
              "fn": "F500001", "grad_type": "exam"}
    fields.update(extra or {})
    assert save(client, 1, fields, "submit").status_code == 302


def thesis_data():
    data = dict(THESIS_TAB_1)
    data.update(THESIS_TAB_2)
    data.pop("grad_type")
    data.pop("professor")
    return data


@pytest.fixture
def staff(settings):
    return make_account(settings, "staff1")


def test_exam_to_thesis_needs_the_thesis_data_first(client, new_client,
                                                    settings, outbox, staff):
    submit_exam(client, "type1@example.org")
    record = record_for(settings, "type1@example.org")
    viewer = as_staff(new_client(), staff)
    base = "/staff/application/{}".format(record["id"])
    response = viewer.post(base + "/type", data={"grad_type": "thesis",
                                                 "professor": "ivanov"})
    assert response.status_code == 400
    assert "За теза липсват" in response.get_data(as_text=True)
    assert record_for(settings, "type1@example.org")["grad_type"] == "exam"
    connection = connect(settings)
    assert applications.corrections_of(connection, record["id"]) == []
    connection.close()
    assert outbox.messages == []


def test_exam_to_thesis_and_back_keeps_history_and_answers(
        client, new_client, settings, outbox, staff):
    submit_exam(client, "type2@example.org")
    record = record_for(settings, "type2@example.org")
    viewer = as_staff(new_client(), staff)
    base = "/staff/application/{}".format(record["id"])
    for field, value in thesis_data().items():
        assert viewer.post(base + "/correct", data={
            "field": field, "value": value}).status_code == 302
    outbox.clear()
    # The relay refuses: nothing changes.
    outbox.refuse = True
    assert viewer.post(base + "/type", data={
        "grad_type": "thesis", "professor": "ivanov"}).status_code == 503
    assert record_for(settings, "type2@example.org")["grad_type"] == "exam"
    outbox.refuse = False
    assert viewer.post(base + "/type", data={
        "grad_type": "thesis", "professor": "ivanov"}).status_code == 302
    assert record_for(settings, "type2@example.org")["grad_type"] == "thesis"
    (request_mail,) = outbox.messages
    assert request_mail.intended == "p.ivanov@example.org"
    connection = connect(settings)
    type_rows = [c for c in applications.corrections_of(connection,
                                                        record["id"])
                 if c["field"] == "grad_type"]
    assert [(c["old_value"], c["new_value"], c["username"])
            for c in type_rows] == [("exam", "thesis", "staff1")]
    connection.close()
    # The student's page and forms follow the corrected type.
    page = client.get("/application").get_data(as_text=True)
    assert "Чака отговор" in page and "prilozhenie2" in page
    assert client.get("/application/forms/prilozhenie2.docx").status_code \
        == 200
    # Eligible for the report only once confirmed and checked.
    connection = connect(settings)
    loaded = lists.load(settings.lists_dir)
    qualifying = lambda: [r["id"] for r in reports.qualifying(connection,
                                                              "УБП-РО")]
    assert record["id"] not in qualifying()
    new_client().post(link_from(request_mail, "confirm"), data={})
    applications.record_check(connection, record["id"], "passed", "",
                              staff["id"])
    assert record["id"] in qualifying()
    # Back to a state exam: the request standing is retired, its answer kept.
    assert viewer.post(base + "/type",
                       data={"grad_type": "exam"}).status_code == 302
    rows = applications.requests_of(connection, record["id"])
    assert [r["answer"] for r in rows] == ["confirm"]
    assert rows[0]["replaced_at"] is not None
    assert record["id"] not in qualifying()
    connection.close()
    assert client.get("/application/forms/prilozhenie2.docx").status_code \
        == 404
    page = client.get("/application").get_data(as_text=True)
    assert "prilozhenie2" not in page and "Чака отговор" not in page
    staff_page = viewer.get(base).get_data(as_text=True)
    assert "държавен изпит" in staff_page and "теза" in staff_page
    assert loaded is not None


# --- M1-C5: a maintained list is never recreated -----------------------------

def test_a_list_removed_after_installation_stops_the_start(tmp_path):
    data_dir = tmp_path / "data"
    settings = make_settings(data_dir)
    create_app(settings)                          # first installation
    path = settings.lists_dir / lists.PROGRAMMES
    text = path.read_text(encoding="utf-8").replace(
        "Администрация и управление", "Публична администрация")
    path.write_text(text, encoding="utf-8")
    from tests.conftest import insert_application
    insert_application(settings, "c5@example.org", programme="АУ-РО")
    path.unlink()
    with pytest.raises(StartupError) as raised:
        create_app(settings)
    assert lists.PROGRAMMES in str(raised.value)
    assert "missing" in str(raised.value)
    assert not path.exists()                      # not quietly recreated


# --- M1-C6: list text a document cannot hold --------------------------------

def professors_text(rows):
    return "код,звание,име,email\n" + "".join(row + "\n" for row in rows)


@hsettings(max_examples=60, deadline=None,
           suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(before=st.integers(min_value=0, max_value=4),
       multiline=st.booleans(),
       bad=st.characters(whitelist_categories=("Cc",)).filter(
           lambda ch: ch not in "\n\r"),
       position=st.integers(min_value=0, max_value=5))
def test_an_unprintable_character_is_reported_by_its_true_line(
        tmp_path_factory, before, multiline, bad, position):
    rows = ['p{0},доц. д-р,Име Фамилия{0},p{0}@example.org'.format(i)
            for i in range(before)]
    if multiline:
        rows.insert(0, 'm,доц. д-р,"Две\nреда",m@example.org')
    name = "Петър Иванов"
    position = min(position, len(name))
    rows.append('x,доц. д-р,{},x@example.org'.format(
        name[:position] + bad + name[position:]))
    text = professors_text(rows)
    expected_line = text.split("\n").index(next(
        line for line in text.split("\n") if bad in line)) + 1
    folder = tmp_path_factory.mktemp("lists")
    lists.write_starter(folder)
    (folder / lists.PROFESSORS).write_text(text, encoding="utf-8")
    with pytest.raises(lists.ListError) as raised:
        lists.load(folder)
    assert raised.value.line == expected_line
    assert "U+{:04X}".format(ord(bad)) in str(raised.value)


def test_a_line_break_inside_a_cell_is_refused_and_later_lines_stay_true(
        tmp_path):
    lists.write_starter(tmp_path)
    (tmp_path / lists.PROFESSORS).write_text(professors_text([
        'a,доц. д-р,"Едно\nдве",a@example.org']), encoding="utf-8")
    with pytest.raises(lists.ListError) as raised:
        lists.load(tmp_path)
    assert raised.value.line == 2 and "line break" in str(raised.value)
    (tmp_path / lists.PROFESSORS).write_text(professors_text([
        'a,доц. д-р,Едно Две,a@example.org',
        'b,акад.,Три Четири,b@example.org']), encoding="utf-8")
    with pytest.raises(lists.ListError) as raised:
        lists.load(tmp_path)
    assert raised.value.line == 3


def test_a_nul_in_a_professor_stops_the_start(tmp_path):
    data_dir = tmp_path / "data"
    prepare_data_dir(data_dir)
    (data_dir / "lists" / lists.PROFESSORS).write_text(professors_text([
        "ivanov,доц. д-р,Пе\x00тър Иванов,p.ivanov@example.org"]),
        encoding="utf-8")
    with pytest.raises(StartupError) as raised:
        create_app(make_settings(data_dir))
    assert "professors.csv line 2" in str(raised.value)
    assert "U+0000" in str(raised.value)


# --- M1-C7: a forwarded header does not reset the source limit ---------------

def test_a_spoofed_forwarding_header_does_not_bypass_the_source_limit(
        app, outbox):
    statuses = []
    for number in range(limits.MAIL_PER_SOURCE + 1):
        client = Client(app.test_client())
        response = client.post("/sign-in", data={
            "email": "spoof{}@example.org".format(number)},
            headers={"CF-Connecting-IP": "10.0.0.{}".format(number)},
            environ_base={"REMOTE_ADDR": "192.0.2.7"})
        statuses.append(response.status_code)
    assert statuses[-1] == 429
    assert len(outbox.messages) == limits.MAIL_PER_SOURCE


# --- M1-C8: every path that sends mail has a finite bound --------------------

@pytest.fixture
def small_limits(monkeypatch):
    monkeypatch.setattr(limits, "SUPERVISOR_PER_ADDRESS", 2)
    monkeypatch.setattr(limits, "NOTICE_PER_ADDRESS", 1)


def test_requests_to_one_supervisor_are_bounded_and_roll_back(
        app, new_client, settings, outbox, small_limits):
    sent = []
    for number in range(3):
        student = new_client()
        as_student(student, "many{}@example.org".format(number))
        sent.append(submit_thesis(student, {
            "name1": "Име", "name2": "Бащино",
            "name3": "Фамилия" + "абв"[number]}).status_code)
    assert sent == [302, 302, 503]
    assert len(outbox.to("p.ivanov@example.org")) == 2
    third = record_for(settings, "many2@example.org")
    assert third["submitted_at"] is None
    connection = connect(settings)
    assert connection.execute("SELECT COUNT(*) FROM requests").fetchone()[0] \
        == 2
    assert connection.execute("SELECT COUNT(*) FROM attempts WHERE bucket = ?",
                              (limits.bucket("supervisor",
                                             "p.ivanov@example.org"),)
                              ).fetchone()[0] == 2
    connection.close()


def test_four_submissions_to_one_supervisor_leave_four_limit_records(
        app, new_client, settings, outbox):
    for number in range(4):
        student = new_client()
        as_student(student, "four{}@example.org".format(number))
        submit_thesis(student, {"name3": "Фамилия" + "абвг"[number]})
    connection = connect(settings)
    assert connection.execute("SELECT COUNT(*) FROM attempts WHERE bucket = ?",
                              (limits.bucket("supervisor",
                                             "p.ivanov@example.org"),)
                              ).fetchone()[0] == 4
    connection.close()


def test_a_bounded_replacement_rolls_back(app, client, new_client, settings,
                                          outbox, small_limits, staff):
    as_student(client, "replace@example.org")
    submit_thesis(client)
    record = record_for(settings, "replace@example.org")
    viewer = as_staff(new_client(), staff)
    base = "/staff/application/{}".format(record["id"])
    assert viewer.post(base + "/supervisor",
                       data={"professor": "dimitrov"}).status_code == 302
    assert viewer.post(base + "/supervisor",
                       data={"professor": "ivanov"}).status_code == 302
    # Two requests to ivanov were sent in this hour already.
    assert viewer.post(base + "/supervisor",
                       data={"professor": "dimitrov"}).status_code == 302
    response = viewer.post(base + "/supervisor",
                           data={"professor": "ivanov"})
    assert response.status_code == 503
    assert record_for(settings, "replace@example.org")["professor"] == \
        "dimitrov"


def test_a_bounded_decline_notice_keeps_the_answer_and_says_so(
        app, new_client, settings, outbox, small_limits):
    student = new_client()
    as_student(student, "notice2@example.org")
    submit_thesis(student)
    page = new_client().post(link_from(outbox.messages[0], "decline"),
                             data={}).get_data(as_text=True)
    assert "писмото до студента не" not in page
    student.post("/application/supervisor", data={"professor": "georgieva"})
    request = [m for m in outbox.messages
               if m.intended == "e.georgieva@example.org"][-1]
    page = new_client().post(link_from(request, "decline"),
                             data={}).get_data(as_text=True)
    assert "писмото до студента не" in page          # over the notice bound
    record = record_for(settings, "notice2@example.org")
    connection = connect(settings)
    assert applications.current_request(connection, record["id"])["answer"] \
        == "decline"
    connection.close()
    assert len(outbox.to("notice2@example.org")) == 1


def test_a_bounded_reminder_stays_due(app, client, settings, outbox, clock,
                                      monkeypatch):
    from superassistant import supervision
    as_student(client, "due@example.org")
    submit_thesis(client)
    monkeypatch.setattr(limits, "SUPERVISOR_PER_ADDRESS", 1)
    clock.advance(days=3, minutes=-30)                # the request's hour
    clock.advance(minutes=31)
    loaded = lists.load(settings.lists_dir)
    connection = connect(settings)
    monkeypatch.setattr(limits, "WINDOW", 4 * 86400)  # still counts it
    sent, failed = supervision.remind(connection, settings, loaded)
    assert sent == [] and len(failed) == 1
    assert connection.execute("SELECT reminders_sent FROM requests"
                              ).fetchone()[0] == 0
    monkeypatch.setattr(limits, "WINDOW", 3600)
    sent, failed = supervision.remind(connection, settings, loaded)
    assert len(sent) == 1 and failed == []
    connection.close()


def test_all_mail_together_is_bounded(app, new_client, settings, outbox,
                                      monkeypatch):
    monkeypatch.setattr(limits, "ALL_MAIL", 2)
    codes = []
    for number in range(3):
        client = Client(app.test_client())
        codes.append(client.post("/sign-in", data={
            "email": "all{}@example.org".format(number)},
            environ_base={"REMOTE_ADDR": "192.0.2.{}".format(number)}
        ).status_code)
    assert codes[:2] == [302, 302] and codes[2] == 429
    assert len(outbox.messages) == 2


# --- M1-C9: the report's header in the adopted size --------------------------

def test_the_report_header_is_times_new_roman_12_pt():
    from pathlib import Path
    template = Path(__file__).resolve().parent.parent / "templates" \
        / "doklad_temi.docx"
    header = Document(str(template)).tables[0].rows[0]
    runs = [r for c in header.cells for p in c.paragraphs for r in p.runs]
    assert runs and all(r.font.size is not None and r.font.size.pt == 12
                        for r in runs)
    assert all(r.font.name == "Times New Roman" for r in runs)
