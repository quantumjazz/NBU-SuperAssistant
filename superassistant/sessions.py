"""The schedule of graduation sessions (constitution 5.13).

The sessions are the owner's fifth list (lists.SESSIONS): per session a
code, its date and the three deadlines of the department's framework
schedule. Every student sees the schedule on the application and chooses
one session: "students must see the scheduled dates and choose one; they
also must acknowledge the timetable" (the owner, 13 October 2026), built
before milestone 3 as its plan's requirement 4 words it (the owner, 16
October 2026: "Yes, all of it").

Days are Sofia's (db.LOCAL_ZONE), read from the one clock (db.now_dt): a
session dated today or later is offered; one dated before today is passed,
shown in the schedule and marked, never offered to a student. Staff may
correct an application's session to any listed session, passed or not.

A session's date is written as „26 януари 2027 г. (вторник)“ and a deadline
as „до 13 ноември 2026 г.“, the words from texts.
"""

from superassistant import db, texts


def today():
    """Today's date in Sofia."""
    return db.now_dt().astimezone(db.LOCAL_ZONE).date()


def long_date(day):
    """A session's date: day, month and year, and the weekday."""
    return texts.SESSION_DATE.format(day=day.day,
                                     month=texts.MONTHS[day.month - 1],
                                     year=day.year,
                                     weekday=texts.WEEKDAYS[day.weekday()])


def deadline(day):
    """A deadline: „до“ and the date."""
    return texts.SESSION_DEADLINE.format(day=day.day,
                                         month=texts.MONTHS[day.month - 1],
                                         year=day.year)


def is_passed(session, day=None):
    return session["date"] < (day or today())


def offered(lists, day=None):
    """The codes a student may choose on that day (today by default), in
    the order of their dates."""
    day = day or today()
    return [code for code, session in lists.sessions.items()
            if not is_passed(session, day)]


def label(lists, code):
    """An application's session as every page writes it: its date, „—“ for
    none, and the code itself for one no longer listed (the start refuses
    such a list, so only a page open across a restart could show it)."""
    if not code:
        return texts.SESSION_NONE
    session = lists.sessions.get(code)
    return long_date(session["date"]) if session else code


def schedule(lists, day=None):
    """The schedule's rows, in the order of their dates: the code, the
    session's date, its three deadlines and whether it has passed."""
    day = day or today()
    return [{"code": code, "date": long_date(session["date"]),
             "deadlines": [deadline(session[key])
                           for key in ("topics", "exam", "theses")],
             "passed": is_passed(session, day)}
            for code, session in lists.sessions.items()]
