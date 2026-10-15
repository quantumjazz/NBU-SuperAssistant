"""The bin (constitution 5.15; the owner, 15 October 2026: "Users remove the
entry (select reason - graduation, else), it goes to a 'bin' and deletion is
confirmed as a second step").

Rules over generated sequences of removals, putting back and deletions: what
the staff table, the reports, the reminders and the log hold; that a
deletion takes every row recorded with the application and nothing else,
leaves a kept report's file as it was, and that a deleted application's
number is never given again. Through the pages: the two steps, the student
who sees only that the application was removed, the supervisor whose links
record nothing, every change refused once the removal has committed, also
when it commits between the page and the change, and who may reach the bin
at all. Everyone is invented.
"""

import hashlib
import sqlite3

import pytest
from hypothesis import given, strategies as st

from superassistant import applications, db, lists, reports, supervision
from superassistant import texts
from superassistant.web import staff as staff_pages
from tests.conftest import (Client, connect, insert_application, insert_check,
                            insert_request, make_account)
from tests.test_application_flow import (THESIS_TAB_1, as_staff, as_student,
                                         link_from, record_for, submit_thesis)
from tests.test_supervision_rules import FAST, new_thesis, world


def count(connection, table, application_id):
    return connection.execute(
        "SELECT COUNT(*) FROM " + table + " WHERE application_id = ?",
        (application_id,)).fetchone()[0]


def table_ids(connection):
    """The applications the staff table lists, as its query selects them."""
    return [row["id"] for row in connection.execute(
        "SELECT id FROM applications WHERE submitted_at IS NOT NULL AND "
        "binned_at IS NULL ORDER BY submitted_at DESC, id DESC")]


# --- The rules, over generated sequences -----------------------------------

operation = st.one_of(
    st.tuples(st.just("remove"), st.integers(0, 9),
              st.sampled_from(applications.BIN_REASONS)),
    st.tuples(st.just("restore"), st.integers(0, 9), st.just(None)),
    st.tuples(st.just("delete"), st.integers(0, 9), st.just(None)),
    st.tuples(st.just("new"), st.just(0), st.just(None)),
    st.tuples(st.just("report"), st.just(0), st.just(None)),
)


@FAST
@given(operations=st.lists(operation, min_size=1, max_size=12))
def test_the_bin_over_any_sequence_of_removals_and_deletions(operations):
    with world() as (settings, connection, loaded, clock, box, staff):
        made = []                          # every number ever given
        model = {}                         # number: None or reason in bin
        log = []                           # (number, event, reason)

        def new():
            number = new_thesis(connection, settings, loaded, len(made) + 1)
            assert all(number > earlier for earlier in made)   # never again
            made.append(number)
            model[number] = None
            request = applications.current_request(connection, number)
            connection.execute("UPDATE requests SET answer = 'confirm' "
                               "WHERE id = ?", (request["id"],))
            applications.record_check(connection, number, "passed",
                                      "проверка", staff["id"])
            with db.transaction(connection):
                applications.correct(connection, applications.get(
                    connection, number), {"topic": "Нова тема"}, staff["id"])

        new()
        new()
        for kind, index, reason in operations:
            clock.advance(minutes=1)
            alive = sorted(model)
            target = alive[index % len(alive)] if alive else None
            if kind == "new":
                new()
            elif kind == "report":
                try:
                    reports.generate(connection, settings, loaded,
                                     "BSNADM01", staff["id"])
                except reports.NothingToReport:
                    pass
            elif kind == "remove" and target is not None:
                done = applications.remove(connection, target, reason,
                                           "бележка", staff["id"])
                assert done == (model[target] is None)
                if done:
                    model[target] = reason
                    log.append((target, "removed", reason))
            elif kind == "restore" and target is not None:
                done = applications.restore(connection, target, staff["id"])
                assert done == (model[target] is not None)
                if done:
                    log.append((target, "restored", model[target]))
                    model[target] = None
            elif kind == "delete" and target is not None:
                was = applications.get(connection, target)
                done = applications.delete(connection, target, staff["id"])
                assert done == (model[target] is not None)
                if done:
                    log.append((target, "deleted", model.pop(target)))
                    for table in applications.RECORDED_WITH:
                        assert count(connection, table, target) == 0
                    assert connection.execute(
                        "SELECT COUNT(*) FROM signins WHERE email_key = ?",
                        (was["email_key"],)).fetchone()[0] == 0
                    assert applications.get(connection, target) is None

        binned = sorted(n for n, reason in model.items() if reason)
        active = sorted(n for n, reason in model.items() if not reason)
        assert sorted(table_ids(connection)) == active
        assert sorted(r["id"] for r in applications.binned(connection)) \
            == binned
        assert [r["bin_reason"] for r in sorted(
            applications.binned(connection), key=lambda r: r["id"])] == [
                model[n] for n in binned]
        qualifying = [r["id"] for r in reports.qualifying(connection,
                                                          "BSNADM01")]
        assert sorted(qualifying) == active
        # Every application not in the bin keeps its own rows.
        for number in active + binned:
            for table in ("corrections", "checks", "requests"):
                assert count(connection, table, number) >= 1
        # The log: every event in order, by number only.
        assert [(r["application_id"], r["event"], r["reason"])
                for r in connection.execute(
                    "SELECT * FROM bin_events ORDER BY id")] == log
        assert [(r["application_id"], r["reason"])
                for r in applications.deletions(connection)] == [
            (n, reason) for n, event, reason in reversed(log)
            if event == "deleted"]
        columns = [r[1] for r in connection.execute(
            "PRAGMA table_info(bin_events)")]
        assert columns == ["id", "application_id", "event", "reason",
                           "by_account", "at"]
        # Nothing points at an application that is gone.
        assert connection.execute("PRAGMA foreign_key_check").fetchall() \
            == []


def test_a_deleted_last_applications_number_is_never_given_again(settings,
                                                                 app):
    staff = make_account(settings)
    connection = connect(settings)
    first = applications.get_or_create(connection, "a@example.org",
                                       "a@example.org")
    last = applications.get_or_create(connection, "b@example.org",
                                      "b@example.org")
    connection.execute("UPDATE applications SET submitted_at = ? WHERE id = "
                       "?", (db.now(), last["id"]))
    assert applications.remove(connection, last["id"], "other", "",
                               staff["id"])
    assert applications.delete(connection, last["id"], staff["id"])
    again = applications.get_or_create(connection, "b@example.org",
                                       "b@example.org")
    assert again["id"] == last["id"] + 1 > first["id"]
    assert again["submitted_at"] is None and again["name1"] == ""
    connection.close()


def test_removing_needs_a_reason_and_a_submitted_application(settings, app):
    staff = make_account(settings)
    connection = connect(settings)
    draft = insert_application(settings, "d@example.org", submitted=False)
    done = insert_application(settings, "s@example.org")
    with pytest.raises(ValueError):
        applications.remove(connection, done, "graduation", "", staff["id"])
    assert not applications.remove(connection, draft, "other", "",
                                   staff["id"])
    assert not applications.remove(connection, 999, "other", "", staff["id"])
    assert not applications.restore(connection, done, staff["id"])
    assert not applications.delete(connection, done, staff["id"])
    assert applications.get(connection, done) is not None
    assert connection.execute("SELECT COUNT(*) FROM bin_events").fetchone()[
        0] == 0
    connection.close()


def test_schema_3_with_rows_upgrades_keeping_them(tmp_path):
    path = tmp_path / "superassistant.sqlite3"
    connection = sqlite3.connect(str(path))
    connection.executescript(";".join(db.MIGRATIONS[:3])
                             + ";PRAGMA user_version = 3;")
    connection.execute(
        "INSERT INTO applications (email, email_key, created_at, updated_at, "
        "submitted_at, name1, credits_declared) VALUES ('a@example.org', "
        "'a@example.org', 't', 't', 't', 'Ана', 1)")
    connection.commit()
    connection.close()
    db.migrate(path)
    connection = db.connect(path)
    row = connection.execute("SELECT * FROM applications").fetchone()
    assert (row["name1"], row["credits_declared"], row["binned_at"],
            row["binned_by"], row["bin_reason"], row["bin_note"]) == (
        "Ана", 1, None, None, None, "")
    assert connection.execute("PRAGMA user_version").fetchone()[0] == 4
    assert connection.execute("SELECT COUNT(*) FROM bin_events").fetchone()[
        0] == 0
    connection.close()


# --- Through the pages -------------------------------------------------------

def reported_thesis(settings, staff, address="a@example.org"):
    """A confirmed, checked thesis application, corrected once, listed in a
    kept topic report."""
    number = insert_application(settings, address, grad_type="thesis",
                                programme="BSNADM01", name1="Ана",
                                name2="Бойкова", name3="Вълчева",
                                fn="F300001", topic="Тема",
                                professor="ivanov")
    insert_request(settings, number, answer="confirm")
    insert_check(settings, number, "passed", staff["id"])
    connection = connect(settings)
    with db.transaction(connection):
        applications.correct(connection, applications.get(connection, number),
                             {"topic": "Тема на тезата"}, staff["id"])
    report_id = reports.generate(connection, settings,
                                 lists.load(settings.lists_dir), "BSNADM01",
                                 staff["id"])
    connection.close()
    return number, report_id


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_staff_remove_put_back_and_delete_in_two_steps(settings, app, clock):
    staff = make_account(settings)
    client = as_staff(Client(app.test_client()), staff)
    number, report_id = reported_thesis(settings, staff)
    connection = connect(settings)
    report = reports.get(connection, report_id)
    file = reports.path(settings, report)
    before = sha(file)
    url = "/staff/application/{}".format(number)

    page = client.get(url).get_data(as_text=True)
    assert 'action="{}/remove"'.format(url) in page
    assert texts.BIN_REASON_GRADUATED in page and texts.BIN_REASON_OTHER in page

    # No reason: refused, nothing changed.
    reply = client.post(url + "/remove", {"note": "x"})
    assert reply.status_code == 400
    assert texts.BIN_CHOOSE_REASON in reply.get_data(as_text=True)
    assert not applications.is_binned(applications.get(connection, number))

    # The first step: out of the table, into the bin, out of the reports.
    clock.advance(minutes=5)
    reply = client.post(url + "/remove", {"reason": "graduated",
                                          "note": "сесия 26.09"})
    assert reply.status_code == 302 and reply.headers["Location"].endswith(
        "/staff")
    table = client.get("/staff").get_data(as_text=True)
    assert "Вълчева" not in table
    assert texts.BIN_REMOVED in table
    bin_page = client.get("/staff/bin").get_data(as_text=True)
    for shown in ("Ана Бойкова Вълчева", "F300001", "дипломиран(а)",
                  "сесия 26.09", staff["username"],
                  db.local_datetime(db.now())):
        assert shown in bin_page, shown
    page = client.get(url).get_data(as_text=True)
    assert 'id="in-bin"' in page and 'id="restore"' in page
    assert 'href="{}/delete"'.format(url) in page
    for form in ("/check", "/correct", "/type", "/supervisor", "/remove"):
        assert 'action="{}{}"'.format(url, form) not in page, form
    assert reports.qualifying(connection, "BSNADM01") == []

    # Nothing changes it while it is in the bin.
    for path, data in (("/check", {"result": "passed"}),
                       ("/correct", {"field": "topic", "value": "Друга"}),
                       ("/supervisor", {"professor": "georgieva"}),
                       ("/type", {"grad_type": "exam"}),
                       ("/remove", {"reason": "other"})):
        assert client.post(url + path, data).status_code == 404, path
    assert count(connection, "checks", number) == 1
    assert count(connection, "corrections", number) == 1
    assert count(connection, "requests", number) == 1

    # Put back: as it was.
    reply = client.post(url + "/restore", follow_redirects=True)
    assert texts.BIN_RESTORED in reply.get_data(as_text=True)
    assert "Вълчева" in client.get("/staff").get_data(as_text=True)
    assert texts.BIN_EMPTY in client.get("/staff/bin").get_data(as_text=True)
    record = applications.get(connection, number)
    assert (record["binned_at"], record["bin_reason"], record["bin_note"]) \
        == (None, None, "")
    assert client.post(url + "/restore").status_code == 404

    # The second step exists only for an application in the bin.
    assert client.get(url + "/delete").status_code == 404
    assert client.post(url + "/delete").status_code == 404
    assert applications.get(connection, number) is not None

    client.post(url + "/remove", {"reason": "other", "note": ""})
    page = client.get(url + "/delete").get_data(as_text=True)
    for shown in ("Ана Бойкова Вълчева", "F300001", "друго",
                  texts.BIN_DELETE_LEAD, 'id="delete-application"'):
        assert shown in page, shown
    assert applications.get(connection, number) is not None   # not yet

    clock.advance(hours=1)
    reply = client.post(url + "/delete", follow_redirects=True)
    page = reply.get_data(as_text=True)
    assert texts.BIN_DELETED in page
    assert applications.get(connection, number) is None
    for table in applications.RECORDED_WITH:
        assert count(connection, table, number) == 0
    # The kept report stays, without the student; its file as generated.
    assert reports.get(connection, report_id) is not None
    assert reports.students(connection, report_id) == []
    assert sha(file) == before
    log = page.split('id="deletions"')[1]
    for shown in ("№ {}".format(number), "друго",
                  "{}, {}".format(staff["username"],
                                  db.local_datetime(db.now()))):
        assert shown in log, shown
    assert "Вълчева" not in page and "F300001" not in page
    for reply in (client.get(url), client.get(url + "/delete"),
                  client.post(url + "/delete"), client.post(url + "/restore")):
        assert reply.status_code == 404
    connection.close()


def test_a_student_whose_application_is_in_the_bin_sees_only_that(
        client, new_client, settings, outbox):
    student = as_student(client, "maria@example.org")
    assert submit_thesis(student).status_code == 302
    record = record_for(settings, "maria@example.org")
    staff = make_account(settings)
    office = as_staff(new_client(), staff)
    office.post("/staff/application/{}/remove".format(record["id"]),
                {"reason": "other"})

    page = student.get("/application").get_data(as_text=True)
    assert texts.STATUS_REMOVED in page
    assert THESIS_TAB_1["topic"] not in page
    assert 'id="forms"' not in page and "<form method=\"post\" action=" \
        "\"/application\"" not in page
    assert student.get("/application/forms/zaiavlenie.docx").status_code \
        == 404
    assert student.get("/application/forms/prilozhenie2.docx").status_code \
        == 404
    before = dict(record_for(settings, "maria@example.org"))
    reply = student.post("/application", {"tab": "1", "action": "save",
                                          "name1": "Друго"})
    assert reply.status_code == 302
    reply = student.post("/application/supervisor",
                         {"professor": "georgieva"})
    assert reply.status_code == 302
    assert dict(record_for(settings, "maria@example.org")) == before

    # Put back: the student's page as before.
    office.post("/staff/application/{}/restore".format(record["id"]))
    page = student.get("/application").get_data(as_text=True)
    assert texts.STATUS_REMOVED not in page and THESIS_TAB_1["topic"] in page

    # Deleted: the student, still signed in, starts afresh under a new number.
    office.post("/staff/application/{}/remove".format(record["id"]),
                {"reason": "graduated"})
    office.post("/staff/application/{}/delete".format(record["id"]))
    page = student.get("/application").get_data(as_text=True)
    assert texts.DRAFT_LEAD in page and THESIS_TAB_1["topic"] not in page
    fresh = record_for(settings, "maria@example.org")
    assert fresh["id"] > record["id"] and fresh["submitted_at"] is None


def test_a_supervisors_link_records_nothing_while_in_the_bin(
        client, new_client, settings, outbox):
    student = as_student(client, "petar@example.org")
    submit_thesis(student)
    record = record_for(settings, "petar@example.org")
    link = link_from(outbox.to("p.ivanov@example.org")[-1], "confirm")
    staff = make_account(settings)
    office = as_staff(new_client(), staff)
    office.post("/staff/application/{}/remove".format(record["id"]),
                {"reason": "other"})
    supervisor = new_client()
    page = supervisor.get(link).get_data(as_text=True)
    assert texts.ANSWER_REPLACED in page and 'id="record-answer"' not in page
    outbox.clear()
    page = supervisor.post(link, {"comment": "да"}).get_data(as_text=True)
    assert texts.ANSWER_REPLACED in page
    connection = connect(settings)
    assert applications.current_request(connection, record["id"])[
        "answer"] is None
    assert outbox.messages == []

    office.post("/staff/application/{}/restore".format(record["id"]))
    assert 'id="record-answer"' in supervisor.get(link).get_data(
        as_text=True)

    office.post("/staff/application/{}/remove".format(record["id"]),
                {"reason": "other"})
    office.post("/staff/application/{}/delete".format(record["id"]))
    assert supervisor.get(link).status_code == 404
    assert supervisor.post(link, {"comment": ""}).status_code == 404
    connection.close()


def test_no_reminder_goes_for_an_application_in_the_bin(monkeypatch):
    with world() as (settings, connection, loaded, clock, box, staff):
        number = new_thesis(connection, settings, loaded, 1)
        clock.advance(days=3)
        stale = supervision.due(connection, settings)
        assert [r["application_id"] for r in stale] == [number]
        applications.remove(connection, number, "other", "", staff["id"])
        assert supervision.due(connection, settings) == []
        box.clear()
        assert supervision.remind(connection, settings, loaded) == ([], [])
        # Removed after the run chose it: its own transaction finds it gone.
        monkeypatch.setattr(supervision, "due", lambda c, s: stale)
        assert supervision.remind(connection, settings, loaded) == ([], [])
        assert box.messages == []
        assert applications.current_request(connection, number)[
            "reminders_sent"] == 0
        monkeypatch.undo()
        applications.restore(connection, number, staff["id"])
        sent, failed = supervision.remind(connection, settings, loaded)
        assert len(sent) == 1 and failed == []


def test_every_change_finds_a_removal_committed_before_it():
    """A removal committed between reading an application and changing it:
    each change reads it again under its own write lock and changes
    nothing."""
    with world() as (settings, connection, loaded, clock, box, staff):
        number = new_thesis(connection, settings, loaded, 1)
        token = supervision.token_for(settings, applications.current_request(
            connection, number))
        applications.remove(connection, number, "other", "", staff["id"])
        before = [dict(r) for r in connection.execute(
            "SELECT * FROM requests ORDER BY id")]
        box.clear()
        with pytest.raises(applications.Removed):
            applications.record_check(connection, number, "passed", "",
                                      staff["id"])
        with pytest.raises(applications.Removed):
            supervision.staff_change(connection, settings, loaded, number,
                                     {"professor": "georgieva"}, staff["id"])
        with pytest.raises(applications.Removed):
            supervision.staff_change_type(connection, settings, loaded,
                                          number, "exam", {}, staff["id"])
        with pytest.raises(applications.Removed):
            supervision.choose_again(connection, settings, loaded, number,
                                     {"professor": "georgieva"})
        assert supervision.answer(connection, token, "confirm", "")[0] \
            == "replaced"
        assert count(connection, "checks", number) == 0
        assert count(connection, "corrections", number) == 0
        assert [dict(r) for r in connection.execute(
            "SELECT * FROM requests ORDER BY id")] == before
        assert box.messages == []
        assert not connection.in_transaction


@pytest.mark.parametrize("path, data", [
    ("/check", {"result": "passed"}),
    ("/correct", {"field": "topic", "value": "Друга тема"}),
    ("/supervisor", {"professor": "georgieva"}),
    ("/type", {"grad_type": "exam"}),
])
def test_a_page_read_before_the_removal_changes_nothing(
        settings, app, outbox, monkeypatch, path, data):
    staff = make_account(settings)
    client = as_staff(Client(app.test_client()), staff)
    number, _ = reported_thesis(settings, staff)
    connection = connect(settings)
    stale = applications.get(connection, number)
    applications.remove(connection, number, "other", "", staff["id"])
    # The page's own look at the application happened before the removal.
    monkeypatch.setattr(staff_pages, "_active", lambda application_id: stale)
    rows = {table: count(connection, table, number)
            for table in ("checks", "corrections", "requests")}
    outbox.clear()
    assert client.post("/staff/application/{}{}".format(number, path),
                       data).status_code == 404
    assert {table: count(connection, table, number) for table in rows} \
        == rows
    assert applications.get(connection, number)["topic"] == "Тема на тезата"
    assert outbox.messages == []
    connection.close()


def test_only_approved_staff_reach_the_bin(settings, app):
    staff = make_account(settings)
    number, _ = reported_thesis(settings, staff)
    connection = connect(settings)
    other = insert_application(settings, "b@example.org", name1="Борис")
    applications.remove(connection, other, "graduated", "", staff["id"])
    waiting = make_account(settings, username="waiting", approved=False)
    student = as_student(Client(app.test_client()), "a@example.org")
    base = "/staff/application/{}".format
    for client in (Client(app.test_client()), student,
                   as_staff(Client(app.test_client()), waiting)):
        for reply in (client.get("/staff/bin"),
                      client.post(base(number) + "/remove",
                                  {"reason": "other"}),
                      client.post(base(other) + "/restore"),
                      client.get(base(other) + "/delete"),
                      client.post(base(other) + "/delete")):
            assert reply.status_code == 302
            assert reply.headers["Location"].endswith("/staff/sign-in")
            text = reply.get_data(as_text=True)
            assert "Ана" not in text and "Борис" not in text
    assert not applications.is_binned(applications.get(connection, number))
    assert applications.is_binned(applications.get(connection, other))
    assert [r["event"] for r in connection.execute(
        "SELECT event FROM bin_events")] == ["removed"]
    connection.close()


def test_the_bin_is_in_the_staff_navigation(settings, app):
    staff = make_account(settings)
    client = as_staff(Client(app.test_client()), staff)
    page = client.get("/staff").get_data(as_text=True)
    assert 'href="/staff/bin"' in page and texts.NAV_BIN in page
    page = client.get("/staff/bin").get_data(as_text=True)
    assert texts.BIN_EMPTY in page and 'aria-current="page">{}'.format(
        texts.NAV_BIN) in page
    # An application in the bin belongs to the bin: its pages say so, and
    # show no empty history.
    number = insert_application(settings, "c@example.org", name1="Цвета")
    connection = connect(settings)
    applications.remove(connection, number, "other", "", staff["id"])
    connection.close()
    for path in ("", "/delete"):
        page = client.get("/staff/application/{}{}".format(number, path)
                          ).get_data(as_text=True)
        assert 'aria-current="page">{}'.format(texts.NAV_BIN) in page
        assert 'aria-current="page">{}'.format(texts.NAV_STAFF) not in page
    page = client.get("/staff/application/{}".format(number)).get_data(
        as_text=True)
    assert 'id="checks"' not in page and 'id="corrections"' not in page
