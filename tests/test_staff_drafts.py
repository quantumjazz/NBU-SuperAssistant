"""Applications not yet submitted, for staff (constitution 2.4 and 5.15; the
owner, 23 October 2026: "it was not right for them to stay hidden from
staff", "Same table, marked", "See it, remove to bin").

Every application not in the bin stands in the staff table, a draft marked
„неподадено“ where the answer and the check go and counted among the
applications. A draft's page shows what the student has entered so far and
nothing staff may change: no check, correction or form. Staff may remove it
to the bin; there the student can no longer save or submit it, also when the
removal comes between the student's page and the student's change. Put back,
it is the student's draft again; deleted, the student may start again.
Everyone is invented.
"""

import itertools

import pytest

from hypothesis import HealthCheck, given, settings as hsettings
from hypothesis import strategies as st

from superassistant import applications, lists, supervision, texts
from tests.conftest import connect, insert_application, make_account
from tests.test_application_flow import (THESIS_TAB_1, THESIS_TAB_2,
                                         as_staff, as_student, record_for,
                                         save)

DRAFT_TAB_1 = dict(THESIS_TAB_1, name1="Чернова", fn="104777",
                   topic="Тема на чернова")
CHANGES = ("check", "correct", "session", "supervisor", "type")
_numbers = itertools.count(1)


def staff_page(viewer, number):
    return viewer.get("/staff/application/{}".format(number))


def remove(viewer, number, reason="other", note=""):
    return viewer.post("/staff/application/{}/remove".format(number),
                       {"reason": reason, "note": note})


def rows_of(page):
    """The staff table's rows, each as its HTML."""
    table = page.split('id="applications"', 1)[1].split("</table>", 1)[0]
    return table.split("<tr ")[1:]


def test_staff_see_a_draft_read_only(client, new_client, settings, clock):
    as_student(client, "draft@example.org")
    client.get("/application")                  # begun
    clock.advance(minutes=20)                   # then saved
    save(client, 1, DRAFT_TAB_1, "next")
    save(client, 2, THESIS_TAB_2)
    record = record_for(settings, "draft@example.org")
    viewer = as_staff(new_client(), make_account(settings))

    page = staff_page(viewer, record["id"]).get_data(as_text=True)
    for entered in ("Чернова Петрова Тодорова", "Тема на чернова",
                    "Обосновка", "F104777"):
        assert entered in page
    assert 'id="not-submitted-chip"' in page
    assert texts.STAFF_NOT_SUBMITTED_NOTE in page
    assert texts.STAFF_LAST_SAVED.format("12.10.2026 12:20") in page
    assert texts.STAFF_STARTED.split("{}")[0] not in page
    assert texts.STAFF_SUBMITTED_AT.lower() not in page
    assert '<dd id="submitted-at">{}</dd>'.format(texts.STAFF_NOT_SUBMITTED) \
        in page
    # Nothing staff may change, and no forms to print; only the bin.
    for absent in ('id="staff-forms"', 'id="record-check"', 'id="checks"',
                   'id="corrections"', 'id="session-form"',
                   'id="type-form"', '/supervisor"'):
        assert absent not in page
    assert 'action="/staff/application/{}/remove"'.format(record["id"]) \
        in page


def test_staff_change_nothing_on_a_draft(client, new_client, settings):
    as_student(client, "draft@example.org")
    save(client, 1, DRAFT_TAB_1)
    before = dict(record_for(settings, "draft@example.org"))
    viewer = as_staff(new_client(), make_account(settings))
    number = before["id"]
    values = {"result": "passed", "note": "н", "field": "topic",
              "value": "Друга", "grad_session": "2027-01",
              "grad_type": "exam", "professor": "ivanov"}
    for change in CHANGES:
        assert viewer.post("/staff/application/{}/{}".format(
            number, change), values).status_code == 404
    for form in ("zaiavlenie", "prilozhenie2"):
        assert viewer.get("/staff/application/{}/{}.docx".format(
            number, form)).status_code == 404
    assert dict(record_for(settings, "draft@example.org")) == before
    connection = connect(settings)
    try:
        for table in ("checks", "corrections", "requests"):
            assert connection.execute(
                "SELECT COUNT(*) FROM " + table).fetchone()[0] == 0
    finally:
        connection.close()


def test_a_draft_removed_to_the_bin_put_back_and_deleted(
        client, new_client, settings, outbox):
    student = as_student(client, "draft@example.org")
    save(student, 1, DRAFT_TAB_1)
    number = record_for(settings, "draft@example.org")["id"]
    viewer = as_staff(new_client(), make_account(settings))
    # The student's page was read before the removal.
    assert texts.DRAFT_LEAD in student.get("/application").get_data(
        as_text=True)

    assert remove(viewer, number, "other", "тестов запис").headers[
        "Location"].endswith("/staff")
    assert "Чернова" not in viewer.get("/staff").get_data(as_text=True)
    bin_page = viewer.get("/staff/bin").get_data(as_text=True)
    assert "Чернова" in bin_page and texts.STAFF_NOT_SUBMITTED in bin_page
    in_bin = staff_page(viewer, number).get_data(as_text=True)
    assert 'id="in-bin"' in in_bin and 'id="not-submitted-chip"' in in_bin
    assert texts.STAFF_NOT_SUBMITTED_NOTE not in in_bin

    # The student sees only that it was removed, and can change nothing.
    before = dict(record_for(settings, "draft@example.org"))
    page = student.get("/application").get_data(as_text=True)
    assert 'id="removed"' in page and texts.DRAFT_LEAD not in page
    assert 'name="action"' not in page
    for action in ("save", "next", "submit"):
        for change in ({"name2": "Друго"}, {"fn": "12ab"}):  # valid, refused
            answer = save(student, 1, dict(DRAFT_TAB_1, **change), action)
            assert answer.headers["Location"].endswith("/application")
            assert dict(record_for(settings, "draft@example.org")) == before
    assert 'id="removed"' in student.get("/application").get_data(
        as_text=True)
    assert outbox.messages == []

    # Put back, it is the student's draft again.
    viewer.post("/staff/application/{}/restore".format(number))
    rows = rows_of(viewer.get("/staff").get_data(as_text=True))
    assert len(rows) == 1 and texts.STAFF_NOT_SUBMITTED in rows[0]
    assert save(student, 1, dict(DRAFT_TAB_1, name2="Ново")).status_code \
        == 302
    assert record_for(settings, "draft@example.org")["name2"] == "Ново"

    # Removed again and deleted: the student may start again.
    remove(viewer, number, "graduated")
    viewer.post("/staff/application/{}/delete".format(number))
    connection = connect(settings)
    try:
        assert applications.get(connection, number) is None
    finally:
        connection.close()
    page = as_student(new_client(), "draft@example.org").get(
        "/application").get_data(as_text=True)
    assert texts.DRAFT_LEAD in page and "Чернова" not in page
    assert record_for(settings, "draft@example.org")["id"] != number


def test_a_removed_draft_is_not_submitted(client, new_client, settings,
                                          outbox):
    """Complete, and removed between the student's page and the press."""
    student = as_student(client, "late@example.org")
    assert save(student, 1, THESIS_TAB_1, "next").status_code == 302
    assert save(student, 2, THESIS_TAB_2).status_code == 302
    number = record_for(settings, "late@example.org")["id"]
    remove(as_staff(new_client(), make_account(settings)), number)
    answer = save(student, 2, THESIS_TAB_2, "submit")
    assert answer.headers["Location"].endswith("/application")
    assert 'id="removed"' in student.get("/application").get_data(
        as_text=True)
    assert record_for(settings, "late@example.org")["submitted_at"] is None
    assert outbox.messages == []            # no request to the supervisor


def test_a_complete_draft_read_before_its_removal_is_neither_saved_nor_submitted(
        client, new_client, settings, outbox):
    """The guards inside the transactions, which the page reaches when the
    removal commits between its own read and its writes."""
    student = as_student(client, "stale@example.org")
    save(student, 1, THESIS_TAB_1, "next")
    save(student, 2, THESIS_TAB_2)
    connection = connect(settings)
    try:
        stale = applications.get(connection, record_for(
            settings, "stale@example.org")["id"])
        remove(as_staff(new_client(), make_account(settings)), stale["id"])
        before = dict(applications.get(connection, stale["id"]))
        with pytest.raises(applications.Removed):
            applications.save_draft(connection, stale, {"name2": "Друго"})
        with pytest.raises(applications.Removed):
            supervision.submit(connection, settings,
                               lists.load(settings.lists_dir), stale["id"])
        assert dict(applications.get(connection, stale["id"])) == before
    finally:
        connection.close()
    assert outbox.messages == []


def test_a_draft_with_no_name_is_named_by_its_address(
        client, new_client, settings):
    as_student(client, "noname@example.org")
    client.get("/application")              # the first visit makes it
    number = record_for(settings, "noname@example.org")["id"]
    viewer = as_staff(new_client(), make_account(settings))
    row, = rows_of(viewer.get("/staff").get_data(as_text=True))
    assert ('<a class="name" href="/staff/application/{}">noname@<wbr>'
            'example.org</a>').format(number) in row
    assert 'class="sub"' not in row             # the address once
    page = staff_page(viewer, number).get_data(as_text=True)
    assert "<title>{} | ".format(texts.STAFF_APPLICATION_TITLE.format(
        "noname@example.org")) in page
    # Opened, nothing saved: when it was begun, not "last saved".
    assert texts.STAFF_STARTED.split("{}")[0] in page
    assert texts.STAFF_LAST_SAVED.split("{}")[0] not in page
    remove(viewer, number)
    assert ('<a class="name" href="/staff/application/{}">noname@'
            'example.org</a>').format(number) in viewer.get(
                "/staff/bin").get_data(as_text=True)


def test_staff_see_a_drafts_ticks_as_the_student_left_them(
        client, new_client, settings):
    """By the rule the nightly copy reads them by (applications.ticked)."""
    as_student(client, "draft@example.org")
    save(client, 1, DRAFT_TAB_1)                    # both boxes ticked
    number = record_for(settings, "draft@example.org")["id"]
    viewer = as_staff(new_client(), make_account(settings))
    page = staff_page(viewer, number).get_data(as_text=True)
    assert '<dd id="declared">{}</dd>'.format(
        texts.STAFF_DECLARED_VALUE[True]) in page
    assert '<dd id="acknowledged">{}</dd>'.format(
        texts.ACKNOWLEDGED_VALUE[True]) in page
    row, = rows_of(viewer.get("/staff").get_data(as_text=True))
    assert '<td class="declared">{}</td>'.format(
        texts.STAFF_DECLARED_VALUE[True]) in row


def ids_of(page):
    return [int(row.split('data-id="', 1)[1].split('"', 1)[0])
            for row in rows_of(page)]


def test_the_order_submitted_as_before_then_drafts_latest_saved_first(
        new_client, settings):
    same = "2026-10-12T08:00:00+00:00"
    first = insert_application(settings, "first@example.org",
                               submitted_at=same,
                               updated_at="2026-10-20T08:00:00+00:00")
    second = insert_application(settings, "second@example.org",
                                submitted_at=same, updated_at=same)
    later = insert_application(settings, "later@example.org",
                               submitted=False, name1="Късна",
                               updated_at="2026-10-20T08:00:00+00:00")
    earlier = insert_application(settings, "earlier@example.org",
                                 submitted=False, name1="Ранна",
                                 updated_at="2026-10-01T08:00:00+00:00")
    viewer = as_staff(new_client(), make_account(settings))
    # Submitted in the same second: the later number first, as before.
    assert ids_of(viewer.get("/staff").get_data(as_text=True)) == [
        second, first, later, earlier]


# --- The rule, over any set of applications --------------------------------

APPLICATION = st.fixed_dictionaries({
    "submitted": st.booleans(),
    "binned": st.booleans(),
    "name1": st.sampled_from(["", "Ана", "Боян"]),
    "grad_type": st.sampled_from([None, "thesis", "exam"]),
})


@hsettings(max_examples=25, deadline=None,
           suppress_health_check=[HealthCheck.function_scoped_fixture])
@given(made=st.lists(APPLICATION, max_size=6))
def test_the_table_holds_every_application_not_in_the_bin(
        new_client, settings, made):
    staff = make_account(settings, "staff{}".format(next(_numbers)))
    connection = connect(settings)
    try:
        connection.execute("DELETE FROM applications")
        connection.commit()
    finally:
        connection.close()
    numbers = []
    for index, state in enumerate(made):
        fields = {"name1": state["name1"], "grad_type": state["grad_type"],
                  "fn": "F{}".format(300000 + index)}
        if state["binned"]:
            fields.update(binned_at="2026-10-23T08:00:00+00:00",
                          binned_by=staff["id"], bin_reason="other")
        numbers.append(insert_application(
            settings, "a{}@example.org".format(index),
            submitted=state["submitted"], **fields))
    viewer = as_staff(new_client(), staff)
    page = viewer.get("/staff").get_data(as_text=True)
    shown = [n for n, state in zip(numbers, made) if not state["binned"]]
    if not shown:
        assert texts.STAFF_EMPTY in page
        return
    rows = rows_of(page)
    assert sorted(int(row.split('data-id="', 1)[1].split('"', 1)[0])
                  for row in rows) == sorted(shown)
    # The submitted first, each draft marked and waiting for nothing.
    marks = [texts.STAFF_NOT_SUBMITTED in row for row in rows]
    assert marks == sorted(marks)
    for row in rows:
        number = int(row.split('data-id="', 1)[1].split('"', 1)[0])
        state = made[numbers.index(number)]
        assert (texts.STAFF_NOT_SUBMITTED in row) == (not state["submitted"])
        if not state["submitted"]:
            assert 'class=""' in row
    assert "<b>{}</b>&nbsp;{}".format(
        len(shown), texts.STAFF_COUNT_ALL[0 if len(shown) == 1 else 1]) \
        in page
    # Every application's page opens; only a submitted one outside the bin
    # can be changed.
    for number, state in zip(numbers, made):
        one = staff_page(viewer, number)
        assert one.status_code == 200
        assert ('id="record-check"' in one.get_data(as_text=True)) == (
            state["submitted"] and not state["binned"])


def test_no_one_but_staff_sees_a_draft(client, new_client, settings):
    insert_application(settings, "hidden@example.org", submitted=False,
                       name1="Скрита")
    number = record_for(settings, "hidden@example.org")["id"]
    other = as_student(new_client(), "other@example.org")
    waiting = new_client()
    make_account(settings, "waiting", approved=False)
    waiting.post("/staff/sign-in", {"login": "waiting",
                                    "password": "парола-123"})
    for outsider in (client, other, waiting):
        for url in ("/staff", "/staff/application/{}".format(number),
                    "/staff/bin"):
            answer = outsider.get(url)
            assert "Скрита" not in answer.get_data(as_text=True)
            assert answer.status_code in (302, 403)
