"""Rules of the supervisor's request, answer and reminders, and of checks,
over generated sequences of events (NOW.md proof 1):

- what each answer, a staff change of the supervisor and the staff check do to
  an application, and what its page then shows the student;
- which supervisors a reminder run selects for given days and count, runs
  repeated on one day included; since milestone 2 the days are calendar days
  in Sofia, not periods of 24 hours (the owner's decision "Daily at 09:00,
  calendar days"), checked over request and run times across Sofia's
  daylight-saving changes and in the owner's own example;
- a supervisor's link: opening records nothing, its button records once, the
  links of the request and its reminders work until then or until the request
  is replaced, and afterwards only show the answer, if one was recorded.
"""

import contextlib
import shutil
import tempfile
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import pytest
from hypothesis import HealthCheck, example, given, settings as hsettings
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
        programme="BSNADM01", topic="Тема {}".format(number),
        average_grade="5", professor=professor, rationale="а", aims="б",
        object_subject="в", methodology="г", information_base="д", plan="е",
        schedule="ж", credits_declared=1))
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
    # Requests and runs all fall at the clock's hour (09:00 UTC, 11:00 or
    # 12:00 in Sofia), so whole days here are also calendar days in Sofia;
    # request and run times of any hour are the next test's.
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


# --- Reminders count calendar days in Sofia (milestone 2) -------------------

SOFIA = ZoneInfo("Europe/Sofia")


def sofia_day(moment):
    """The calendar date in Sofia of a moment."""
    return moment.astimezone(SOFIA).date()


def at_sofia(day, hour, minute=0):
    """The moment, in UTC, of a Sofia wall-clock time on a Sofia date."""
    return datetime.combine(day, time(hour, minute),
                            tzinfo=SOFIA).astimezone(timezone.utc)


def utc_instants(start, end):
    return st.datetimes(min_value=start, max_value=end,
                        timezones=st.just(timezone.utc)).map(
        lambda moment: moment.replace(microsecond=0))


def near_sofia_midnight(first_day, last_day):
    """Moments from 20:00 to 23:59 UTC. Sofia's midnight is 21:00 UTC in
    summer time and 22:00 UTC in winter time, so which Sofia date such a
    moment is on depends on the season."""
    return st.tuples(st.dates(first_day, last_day),
                     st.integers(min_value=20 * 3600,
                                 max_value=24 * 3600 - 1)).map(
        lambda t: datetime.combine(t[0], time(0), tzinfo=timezone.utc)
        + timedelta(seconds=t[1]))


# When a request is mailed, in UTC: near Sofia's midnight in the weeks around
# its changes of clock, on 25 October 2026 (04:00 summer time back to 03:00,
# at 01:00 UTC) and on 28 March 2027 (03:00 forward to 04:00, at 01:00 UTC);
# at any moment of the days of those changes; or at any moment of the
# pilot's year.
request_instant = st.one_of(
    near_sofia_midnight(date(2026, 10, 18), date(2026, 11, 1)),
    near_sofia_midnight(date(2027, 3, 21), date(2027, 4, 4)),
    utc_instants(datetime(2026, 10, 24), datetime(2026, 10, 26)),
    utc_instants(datetime(2027, 3, 27), datetime(2027, 3, 29)),
    utc_instants(datetime(2026, 9, 1), datetime(2027, 9, 1)),
)

# The runs: each some Sofia days after the one before (0: the same day
# again; most often 1, as the timer runs daily) at a Sofia wall-clock time,
# most often 09:00 or an hour next to midnight or a change of clock; so daily
# runs at any hour, days without a run and repeated runs on one day all
# occur.
run_plan = st.lists(st.tuples(
    st.one_of(st.just(1), st.integers(min_value=0, max_value=4)),
    st.one_of(st.sampled_from([9, 0, 23, 3, 4]),
              st.integers(min_value=0, max_value=23)),
    st.one_of(st.just(0), st.integers(min_value=0, max_value=59))),
    min_size=1, max_size=12)

DAILY_AT_NINE = [(1, 9, 0)] * 9


@hsettings(max_examples=80, deadline=None,
           suppress_health_check=[HealthCheck.too_slow])
# Requests near Sofia's midnight, then the daily run at 09:00, each on a
# Sofia date other than its UTC date or the date one offset kept all year
# would give: Sunday 25 October 2026 at 23:30, winter time, hours after the
# clocks went back (summer time's offset would say Monday); Sunday 25 October
# at 00:30, summer time, hours before (UTC still says Saturday); and Sunday
# 28 March 2027 at 00:30, winter time, before the clocks go forward (UTC
# still says Saturday).
@example(first=datetime(2026, 10, 25, 21, 30, tzinfo=timezone.utc), later=[],
         days=3, count=2, runs=DAILY_AT_NINE)
@example(first=datetime(2026, 10, 24, 21, 30, tzinfo=timezone.utc), later=[],
         days=3, count=2, runs=DAILY_AT_NINE)
@example(first=datetime(2027, 3, 27, 22, 30, tzinfo=timezone.utc), later=[],
         days=3, count=2, runs=DAILY_AT_NINE)
@given(first=request_instant,
       later=st.lists(st.integers(min_value=0, max_value=3 * 24 * 60),
                      max_size=2),
       days=st.integers(min_value=1, max_value=4),
       count=st.integers(min_value=0, max_value=3),
       runs=run_plan)
def test_a_reminder_goes_on_the_first_run_the_set_sofia_days_later(
        first, later, days, count, runs):
    """A reminder goes out exactly on the first run whose Sofia date is at
    least the set days after the Sofia date of the request or its latest
    reminder, whatever the hours of the request and the runs; at most the set
    count; never twice on one Sofia day."""
    with world(reminder_days=days, reminder_count=count) as (
            settings, connection, loaded, clock, box, staff):
        # The model: for each request, the Sofia dates it was mailed on, the
        # request's own first, then each reminder's.
        mailed, address = {}, {}
        for number, minutes in enumerate([0] + sorted(later)):
            clock.moment = first + timedelta(minutes=minutes)
            app_id = new_thesis(connection, settings, loaded, number,
                                PROFESSORS[number % len(PROFESSORS)])
            request = applications.current_request(connection, app_id)
            mailed[request["id"]] = [sofia_day(clock.moment)]
            address[request["id"]] = request["sup_email"]
        previous = clock.moment
        for gap, hour, minute in runs:
            run_at = max(previous, at_sofia(
                sofia_day(previous) + timedelta(days=gap), hour, minute))
            previous = clock.moment = run_at
            today = sofia_day(run_at)
            expected = sorted(
                rid for rid, dates in mailed.items()
                if len(dates) - 1 < count and (today - dates[-1]).days >= days)
            box.clear()
            sent, failed = supervision.remind(connection, settings, loaded)
            assert sorted(sent) == expected and failed == []
            assert sorted(m.intended for m in box.messages) == sorted(
                address[rid] for rid in expected)
            for rid in expected:
                mailed[rid].append(today)
            # Run again at once, on the same Sofia day: nothing more.
            assert supervision.remind(connection, settings, loaded) == ([], [])
        for rid, dates in mailed.items():
            row = connection.execute(
                "SELECT reminders_sent, last_mailed_at FROM requests WHERE "
                "id = ?", (rid,)).fetchone()
            assert row["reminders_sent"] == len(dates) - 1 <= count
            assert sofia_day(db.parse(row["last_mailed_at"])) == dates[-1]
            # Each mail the set days or more after the one before it, so
            # never two on one Sofia day, the request's day included.
            assert all((later_day - earlier_day).days >= days
                       for earlier_day, later_day in zip(dates, dates[1:]))


@pytest.mark.parametrize("monday", [
    date(2026, 10, 12),     # the owner's example
    date(2026, 10, 19),     # its Sunday, 25 October, the clocks go back
    date(2027, 3, 22),      # its Sunday, 28 March, the clocks go forward
])
def test_the_owners_example_monday_request_thursday_and_sunday_reminders(
        monday):
    """The owner's example: a request mailed on Monday at 14:00 and the
    daily run at 09:00, Sofia time, with the settings' defaults (3 days, 2
    reminders): the first reminder on Thursday, the second on Sunday, none on
    Saturday or the Monday after, and none later. Thursday at 09:00 is only
    67 hours after Monday at 14:00: counted in hours, as in milestone 1, it
    would have waited until Friday."""
    with world() as (settings, connection, loaded, clock, box, staff):
        assert (settings.reminder_days, settings.reminder_count) == (3, 2)
        clock.moment = at_sofia(monday, 14)
        new_thesis(connection, settings, loaded, 1)
        reminded = []
        for offset in range(1, 15):     # every day for the next two weeks
            day = monday + timedelta(days=offset)
            clock.moment = at_sofia(day, 9)
            sent, failed = supervision.remind(connection, settings, loaded)
            assert failed == [] and len(sent) <= 1
            if sent:
                reminded.append(day)
        thursday, sunday = monday + timedelta(days=3), monday + timedelta(
            days=6)
        assert reminded == [thursday, sunday]
        assert [day.weekday() for day in reminded] == [3, 6]
        saturday, next_monday = monday + timedelta(days=5), monday + timedelta(
            days=7)
        assert saturday not in reminded and next_monday not in reminded
        assert [("Напомняне" in m.subject) for m in box.messages] == [
            False, True, True]


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
