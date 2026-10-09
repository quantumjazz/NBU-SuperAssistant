"""Rules of the supervisor's request, answer and reminders, and of checks,
over generated sequences of events (NOW.md proof 1):

- what each answer, a staff change of the supervisor and the staff check do to
  an application, and what its page then shows the student;
- which supervisors a reminder run selects for given days and count, runs
  repeated on one day included;
- a supervisor's link: opening records nothing, its button records once, the
  links of the request and its reminders work until then or until the request
  is replaced, and afterwards only show the answer, if one was recorded.
"""

import contextlib
import shutil
import tempfile
from pathlib import Path

from hypothesis import HealthCheck, given, settings as hsettings
from hypothesis import strategies as st

from superassistant import applications, db, lists, mail, supervision
from tests.conftest import (Clock, Outbox, make_account, make_settings,
                            prepare_data_dir)

FAST = hsettings(max_examples=40, deadline=None,
                 suppress_health_check=[HealthCheck.too_slow])

PROFESSORS = ["ivanov", "georgieva", "dimitrov"]


@contextlib.contextmanager
def world(**setting_overrides):
    """A fresh data directory, clock and fake relay for one example."""
    path = Path(tempfile.mkdtemp())
    clock = Clock()
    box = Outbox()
    db.set_clock(clock)
    mail.set_relay(box)
    try:
        prepare_data_dir(path / "data")
        settings = make_settings(path / "data", **setting_overrides)
        connection = db.connect(settings.db_path)
        loaded = lists.load(settings.lists_dir)
        staff = make_account(settings, "staff1")
        yield settings, connection, loaded, clock, box, staff
        connection.close()
    finally:
        db.set_clock(None)
        mail.set_relay(None)
        shutil.rmtree(str(path), ignore_errors=True)


def new_thesis(connection, settings, loaded, number, professor="ivanov"):
    key = "s{}@example.org".format(number)
    record = applications.get_or_create(connection, key, key)
    applications.save_draft(connection, record, dict(
        name1="Име", name2="Бащино", name3="Фамилия{}".format(number),
        fn="F{}".format(1000 + number), grad_type="thesis", phone="1",
        programme="АУ-РО", topic="Тема {}".format(number), average_grade="5",
        professor=professor, rationale="а", aims="б", object_subject="в",
        methodology="г", information_base="д", plan="е", schedule="ж"))
    assert supervision.submit(connection, settings, loaded, record["id"]) == []
    return record["id"]


def token_of(settings, connection, application_id):
    request = applications.current_request(connection, application_id)
    return supervision.token_for(settings, request)


event = st.one_of(
    st.tuples(st.just("answer"), st.sampled_from(supervision.CHOICES)),
    st.tuples(st.just("check"), st.sampled_from(["passed", "not_passed"])),
    st.tuples(st.just("change"), st.sampled_from(PROFESSORS)),
    st.tuples(st.just("again"), st.sampled_from(PROFESSORS)),
)


@FAST
@given(events=st.lists(event, max_size=8))
def test_what_answers_changes_and_checks_do_to_an_application(events):
    with world() as (settings, connection, loaded, clock, box, staff):
        app_id = new_thesis(connection, settings, loaded, 1)
        # A model of what should be true, kept beside the records.
        answer, check, requests = None, None, 1
        for kind, value in events:
            clock.advance(minutes=1)
            if kind == "answer":
                state, _ = supervision.answer(
                    connection, token_of(settings, connection, app_id), value,
                    "")
                if answer is None:
                    assert state == "recorded"
                    answer = value
                else:
                    assert state == "answered"
            elif kind == "check":
                applications.record_check(connection, app_id, value, "",
                                          staff["id"])
                check = value
            elif kind == "change":
                current = applications.get(connection, app_id)["professor"]
                supervision.staff_change(connection, settings, loaded, app_id,
                                         {"professor": value}, staff["id"])
                if value != current:
                    answer, requests = None, requests + 1
            elif kind == "again":
                try:
                    supervision.choose_again(connection, settings, loaded,
                                             app_id, {"professor": value})
                except PermissionError:
                    assert answer != "decline"
                else:
                    assert answer == "decline"
                    answer, requests = None, requests + 1
            record = applications.get(connection, app_id)
            standing = applications.standing(connection, record)
            assert standing.answer == (answer or "awaited")
            assert standing.check == check
            assert standing.waiting_for_supervisor == (answer is None)
            assert standing.waiting_for_check == (check is None)
            assert standing.waiting_for_report == (answer == "confirm"
                                                   and check == "passed")
        rows = applications.requests_of(connection, app_id)
        assert len(rows) == requests
        assert sum(1 for r in rows if r["replaced_at"] is None) == 1
        # Every request made was mailed to the supervisor it names.
        assert [m.intended for m in box.messages] == [
            r["sup_email"] for r in rows]


@FAST
@given(events=st.lists(event, max_size=6),
       comment=st.text(max_size=40))
def test_a_link_records_once_while_standing_and_then_only_shows(events,
                                                                comment):
    with world() as (settings, connection, loaded, clock, box, staff):
        app_id = new_thesis(connection, settings, loaded, 1)
        first = applications.current_request(connection, app_id)
        token = supervision.token_for(settings, first)
        for kind, value in events:
            if kind == "change":
                supervision.staff_change(connection, settings, loaded, app_id,
                                         {"professor": value}, staff["id"])
            elif kind == "check":
                applications.record_check(connection, app_id, value, "",
                                          staff["id"])
        before = supervision.find(connection, token)
        state, row = supervision.answer(connection, token, "confirm", comment)
        after = supervision.find(connection, token)
        if before["replaced_at"] is not None:
            assert state == "replaced" and after["answer"] is None
        else:
            assert state == "recorded"
            assert after["answer"] == "confirm"
            assert after["comment"] == comment.strip()
            assert after["answered_at"] is not None
        state, _ = supervision.answer(connection, token, "decline", "x")
        assert state in ("answered", "replaced")
        assert supervision.find(connection, token)["answer"] == after["answer"]


request_plan = st.lists(st.tuples(
    st.integers(min_value=0, max_value=12),          # days before the run
    st.sampled_from([None, "confirm", "decline"]),   # its answer
    st.booleans(),                                   # replaced
), min_size=1, max_size=5)


@FAST
@given(plan=request_plan, days=st.integers(min_value=1, max_value=4),
       count=st.integers(min_value=0, max_value=3),
       runs=st.lists(st.integers(min_value=0, max_value=5), min_size=1,
                     max_size=5))
def test_which_supervisors_a_reminder_run_selects(plan, days, count, runs):
    with world(reminder_days=days, reminder_count=count) as (
            settings, connection, loaded, clock, box, staff):
        start = clock.moment
        made = []
        for number, (age, answer, replaced) in enumerate(plan):
            clock.moment = start
            app_id = new_thesis(connection, settings, loaded, number)
            request = applications.current_request(connection, app_id)
            stamp = (start - __import__("datetime").timedelta(days=age)
                     ).isoformat(timespec="seconds")
            connection.execute(
                "UPDATE requests SET created_at = ?, sent_at = ?, "
                "last_mailed_at = ?, answer = ?, replaced_at = ? WHERE id = ?",
                (stamp, stamp, stamp, answer,
                 stamp if replaced else None, request["id"]))
            made.append((request["id"], age, answer, replaced))
        clock.moment = start
        model = dict((rid, {"last": -age, "sent": 0})
                     for rid, age, answer, replaced in made
                     if answer is None and not replaced)
        today = 0
        for gap in runs:
            today += gap
            clock.moment = start + __import__("datetime").timedelta(days=today)
            box.clear()
            sent, failed = supervision.remind(connection, settings, loaded)
            expected = sorted(
                rid for rid, state in model.items()
                if state["sent"] < count and today - state["last"] >= days)
            assert sorted(sent) == expected and failed == []
            assert len(box.messages) == len(expected)
            for rid in expected:
                model[rid]["sent"] += 1
                model[rid]["last"] = today
            # A second run on the same day sends nothing more.
            assert supervision.remind(connection, settings, loaded) == ([], [])


@FAST
@given(steps=st.lists(st.tuples(
    st.sampled_from(["check", "correct"]),
    st.sampled_from(["passed", "not_passed"]),
    st.sampled_from(["name1", "name3", "fn", "topic", "plan"]),
    st.text(alphabet="абвгдеABCDE 0123456789", min_size=1, max_size=12)),
    max_size=8))
def test_checks_and_corrections_each_keep_what_they_replace(steps):
    with world() as (settings, connection, loaded, clock, box, staff):
        app_id = new_thesis(connection, settings, loaded, 1)
        expected_checks, expected_corrections = [], []
        for kind, result, field, text in steps:
            clock.advance(minutes=1)
            if kind == "check":
                applications.record_check(connection, app_id, result,
                                          "бележка", staff["id"])
                expected_checks.append((result, db.now()))
            else:
                record = applications.get(connection, app_id)
                value = applications.normalise(field, text)
                if not value:
                    continue
                with db.transaction(connection):
                    changed = applications.correct(connection, record,
                                                   {field: value},
                                                   staff["id"])
                if record[field] != value:
                    assert changed == [field]
                    expected_corrections.append((field, record[field], value,
                                                 db.now()))
                else:
                    assert changed == []
        checks = applications.checks_of(connection, app_id)
        assert [(c["result"], c["at"]) for c in checks] == expected_checks
        assert all(c["username"] == "staff1" and c["note"] == "бележка"
                   for c in checks)
        corrections = applications.corrections_of(connection, app_id)
        assert [(c["field"], c["old_value"], c["new_value"], c["at"])
                for c in corrections] == expected_corrections
        latest = applications.latest_check(connection, app_id)
        assert (latest["result"] if latest else None) == (
            expected_checks[-1][0] if expected_checks else None)
