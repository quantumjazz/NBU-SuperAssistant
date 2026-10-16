"""The application, the supervisor's answer and staff's work, through the
pages (NOW.md requirements 2, 3 and 5; proofs 1, 3 and 4).

Students and staff are signed in by writing the session directly; signing in
through the emailed link is tested in tests/test_signin.py.
"""

import re

import pytest

from superassistant import applications, db, supervision, texts
from tests.conftest import connect, make_account

THESIS_TAB_1 = {
    "name1": "Мария", "name2": "Петрова", "name3": "Тодорова",
    "fn": "104999", "grad_type": "thesis", "phone": "0888 000 111",
    "programme": "BSNBUB04", "topic": "Управление на риска в малки фирми",
    "average_grade": "5,50", "professor": "ivanov", "credits_declared": "1",
    "grad_session": "2027-01", "schedule_ack": "1",
}
THESIS_TAB_2 = {
    "rationale": "Обосновка\nвтори ред", "aims": "Цели", "object_subject":
    "Обект", "methodology": "Методи", "information_base": "Данни",
    "plan": "Глава 1\nГлава 2", "schedule": "Октомври – май",
}


def as_student(client, address):
    with client.raw.session_transaction() as session:
        session["student"] = address.strip().casefold()
        session["student_email"] = address
    return client


def as_staff(client, record):
    with client.raw.session_transaction() as session:
        session["staff"] = record["id"]
        session["tag"] = record["session_tag"]
    return client


def save(client, tab, fields, action="save"):
    data = dict(fields)
    data.update({"tab": str(tab), "action": action})
    return client.post("/application", data=data)


def submit_thesis(client, overrides=None, tab2=None):
    tab1 = dict(THESIS_TAB_1)
    tab1.update(overrides or {})
    assert save(client, 1, tab1, "next").status_code == 302
    return save(client, 2, dict(THESIS_TAB_2, **(tab2 or {})), "submit")


def record_for(settings, address):
    connection = connect(settings)
    try:
        return applications.by_email_key(connection, address.casefold())
    finally:
        connection.close()


def link_from(message, choice):
    found = re.search(r"(/answer/[A-Za-z0-9_-]+/" + choice + ")", message.text)
    return found.group(1)


# --- The application -------------------------------------------------------

def test_a_state_exam_asks_names_and_fn_only_and_has_no_second_tab(
        client, settings, outbox):
    as_student(client, "exam@example.org")
    page = client.get("/application").get_data(as_text=True)
    assert "Преди да подадете заявлението" in page        # the 5.1 reminder
    save(client, 1, {"name1": "Иван", "name2": "Иванов", "name3": "Петров",
                     "fn": "12345", "grad_type": "exam"})
    page = client.get("/application?tab=2").get_data(as_text=True)
    assert 'id="tab2-link"' in page and re.search(r'id="tab2-link"[^>]*hidden',
                                                  page)
    response = save(client, 1, {"name1": "Иван", "name2": "Иванов",
                                "name3": "Петров", "fn": "12345",
                                "grad_type": "exam",
                                "credits_declared": "1",
                                "grad_session": "2027-01",
                                "schedule_ack": "1"}, "submit")
    assert response.status_code == 302
    record = record_for(settings, "exam@example.org")
    assert record["submitted_at"] and record["fn"] == "F12345"
    assert record["programme"] == ""                      # 8.3: no programme
    assert outbox.messages == []                          # no supervisor
    page = client.get("/application").get_data(as_text=True)
    assert "Подадено на" in page and "prilozhenie2" not in page


def test_a_thesis_is_submitted_once_its_request_has_gone(client, settings,
                                                         outbox):
    as_student(client, "thesis@example.org")
    response = submit_thesis(client)
    assert response.status_code == 302
    record = record_for(settings, "thesis@example.org")
    assert record["submitted_at"] is not None
    (request_mail,) = outbox.messages
    assert request_mail.intended == "p.ivanov@example.org"
    for expected in ("Мария Петрова Тодорова", "F104999",
                     "Управление на бизнеса и предприемачество",
                     "Управление на риска в малки фирми", "Обосновка",
                     "втори ред", "Глава 2", "/confirm", "/decline"):
        assert expected in request_mail.text
    assert "Потвърждавам" in request_mail.html
    assert "Не потвърждавам" in request_mail.html
    page = client.get("/application").get_data(as_text=True)
    assert "Чака отговор от научния ръководител" in page


def test_a_typed_supervisor_from_outside_gets_the_request(client, settings,
                                                          outbox):
    as_student(client, "outside@example.org")
    submit_thesis(client, {"professor": "", "sup_title": "проф. д-р",
                           "sup_name": "Анна Стефанова",
                           "sup_email": "a.stefanova@example.net"})
    (sent,) = outbox.messages
    assert sent.intended == "a.stefanova@example.net"
    assert "проф. д-р Анна Стефанова" in sent.text


def test_a_relay_refusing_the_request_leaves_the_application_unsubmitted(
        client, settings, outbox):
    as_student(client, "refused@example.org")
    outbox.refuse = True
    response = submit_thesis(client)
    assert response.status_code == 503
    assert "не можа да бъде изпратено" in response.get_data(as_text=True)
    record = record_for(settings, "refused@example.org")
    assert record["submitted_at"] is None
    connection = connect(settings)
    assert connection.execute("SELECT COUNT(*) FROM requests").fetchone()[0] \
        == 0
    connection.close()


def test_mixed_letters_are_refused_and_shown_and_nothing_is_saved(
        client, settings):
    as_student(client, "mixed@example.org")
    response = save(client, 1, dict(THESIS_TAB_1,
                                    name3="Тодорова".replace("о", "o")))
    assert response.status_code == 400
    assert "смесени латински и кирилски" in response.get_data(as_text=True)
    record = record_for(settings, "mixed@example.org")
    assert record["name1"] == ""


def test_no_field_is_asked_twice(client):
    as_student(client, "twice@example.org")
    save(client, 1, THESIS_TAB_1, "next")
    first = client.get("/application?tab=1").get_data(as_text=True)
    second = client.get("/application?tab=2").get_data(as_text=True)
    names = lambda page: set(re.findall(r'<(?:input|textarea|select)[^>]*'
                                        r'name="([a-z_0-9]+)"', page))
    asked = lambda page: names(page) - {"csrf", "tab", "action", "comment"}
    assert asked(first) and asked(second)
    assert not (asked(first) & asked(second))


def test_after_submitting_the_student_cannot_change_the_application(
        client, settings):
    as_student(client, "locked@example.org")
    submit_thesis(client)
    save(client, 1, dict(THESIS_TAB_1, topic="Друга тема"))
    assert record_for(settings, "locked@example.org")["topic"] == \
        THESIS_TAB_1["topic"]
    # Choosing again without a decline changes nothing either.
    client.post("/application/supervisor", data={"professor": "georgieva"})
    assert record_for(settings, "locked@example.org")["professor"] == "ivanov"


# --- The supervisor's answer ------------------------------------------------

def test_opening_a_link_records_nothing_and_the_button_records_once(
        client, new_client, settings, outbox):
    as_student(client, "answer@example.org")
    submit_thesis(client)
    confirm = link_from(outbox.messages[0], "confirm")
    decline = confirm[:-len("confirm")] + "decline"
    supervisor = new_client()
    for _ in range(2):
        page = supervisor.get(confirm)
        assert page.status_code == 200
        assert "Мария Петрова Тодорова" in page.get_data(as_text=True)
    record = record_for(settings, "answer@example.org")
    connection = connect(settings)
    assert applications.current_request(connection, record["id"])["answer"] \
        is None
    supervisor.post(confirm, data={"comment": "Съгласен съм."})
    current = applications.current_request(connection, record["id"])
    assert current["answer"] == "confirm"
    assert current["comment"] == "Съгласен съм." and current["answered_at"]
    # A second answer, through either link, changes nothing.
    page = supervisor.post(decline, data={"comment": "x"}).get_data(
        as_text=True)
    assert "вече е записан" in page
    again = applications.current_request(connection, record["id"])
    assert again["answer"] == "confirm" and again["comment"] == "Съгласен съм."
    connection.close()
    # The student sees the answer, not the comment.
    page = client.get("/application").get_data(as_text=True)
    assert "Научният ръководител потвърди" in page
    assert "Съгласен съм." not in page


def test_no_link_is_stored_in_the_clear(client, settings, outbox):
    as_student(client, "hashed@example.org")
    submit_thesis(client)
    token = link_from(outbox.messages[0], "confirm").split("/")[2]
    connection = connect(settings)
    for row in connection.execute("SELECT * FROM requests"):
        assert all(token not in str(value) for value in tuple(row))
    connection.close()


def test_a_decline_tells_the_student_who_may_choose_again(
        client, new_client, settings, outbox):
    as_student(client, "declined@example.org")
    submit_thesis(client)
    first = outbox.messages[0]
    new_client().post(link_from(first, "decline"), data={"comment": ""})
    notice = outbox.to("declined@example.org")
    assert len(notice) == 1
    assert "/application" in notice[0].text
    page = client.get("/application").get_data(as_text=True)
    assert "не потвърди" in page and "/application/supervisor" in page
    outbox.clear()
    response = client.post("/application/supervisor",
                           data={"professor": "georgieva"})
    assert response.status_code == 302
    (new_request,) = outbox.messages
    assert new_request.intended == "e.georgieva@example.org"
    connection = connect(settings)
    record = record_for(settings, "declined@example.org")
    rows = applications.requests_of(connection, record["id"])
    assert [r["answer"] for r in rows] == ["decline", None]
    assert rows[0]["replaced_at"] is not None and rows[1]["replaced_at"] is None
    connection.close()
    # The first request's links now only show its answer.
    page = new_client().get(link_from(first, "confirm")).get_data(
        as_text=True)
    assert "вече е записан" in page


def test_a_decline_notice_the_relay_refuses_still_records_the_answer(
        client, new_client, settings, outbox):
    as_student(client, "notice@example.org")
    submit_thesis(client)
    link = link_from(outbox.messages[0], "decline")
    outbox.refuse = True
    page = new_client().post(link, data={}).get_data(as_text=True)
    assert "писмото до студента не" in page
    record = record_for(settings, "notice@example.org")
    connection = connect(settings)
    assert applications.current_request(connection, record["id"])["answer"] \
        == "decline"
    connection.close()


def test_a_confirmation_tells_the_student(client, new_client, settings,
                                          outbox):
    as_student(client, "confirmed@example.org")
    submit_thesis(client)
    new_client().post(link_from(outbox.messages[0], "confirm"),
                      data={"comment": ""})
    notice = outbox.to("confirmed@example.org")
    assert len(notice) == 1 and len(outbox.messages) == 2
    assert notice[0].subject == texts.CONFIRM_SUBJECT
    for expected in ("Мария Петрова Тодорова", "доц. д-р Петър Иванов",
                     "„Управление на риска в малки фирми“",
                     settings.base_url + "/application"):
        assert expected in notice[0].text
    page = client.get("/application").get_data(as_text=True)
    assert texts.STATUS_CONFIRMED in page


def test_a_confirmation_notice_the_relay_refuses_still_records_the_answer(
        client, new_client, settings, outbox):
    as_student(client, "confirm-notice@example.org")
    submit_thesis(client)
    link = link_from(outbox.messages[0], "confirm")
    outbox.refuse = True
    page = new_client().post(link, data={}).get_data(as_text=True)
    assert texts.ANSWER_NOTICE_FAILED in page
    record = record_for(settings, "confirm-notice@example.org")
    connection = connect(settings)
    assert applications.current_request(connection, record["id"])["answer"] \
        == "confirm"
    connection.close()


def test_a_supervisor_link_reaches_only_its_own_request(
        client, new_client, settings, outbox):
    as_student(client, "one@example.org")
    submit_thesis(client)
    other = new_client()
    as_student(other, "two@example.org")
    submit_thesis(other, {"name1": "Георги", "name2": "Стоянов",
                          "name3": "Колев", "topic": "Друга тема"})
    first_link = link_from(outbox.messages[0], "confirm")
    page = new_client().get(first_link).get_data(as_text=True)
    assert "Мария Петрова Тодорова" in page and "Георги" not in page
    assert new_client().get("/answer/not-a-token/confirm").status_code == 404


# --- The answer page's title and heading (the task of 13 October 2026) -------
# They name the choice only while the page can record it or has just recorded
# it; otherwise both read ANSWER_TITLE_NEUTRAL and the body says what stands.

CHOICE_TITLES = (texts.ANSWER_TITLE_CONFIRM, texts.ANSWER_TITLE_DECLINE)


def title_of(page):
    return re.search(r"<title>(.*?) \| ", page).group(1)


def heading_of(page):
    found = re.search(r"<h1>(.*?)</h1>", page)
    return found.group(1) if found else None


def test_an_invalid_link_names_no_choice(new_client):
    for choice in ("confirm", "decline"):
        for send in ("get", "post"):
            response = getattr(new_client(), send)(
                "/answer/not-a-token/" + choice)
            page = response.get_data(as_text=True)
            assert response.status_code == 404
            assert title_of(page) == texts.ANSWER_TITLE_NEUTRAL
            assert texts.ANSWER_UNKNOWN in page
            assert not any(title in page for title in CHOICE_TITLES)


def test_an_open_link_names_its_choice(client, new_client, outbox):
    as_student(client, "open@example.org")
    submit_thesis(client)
    for choice, title in zip(("confirm", "decline"), CHOICE_TITLES):
        page = new_client().get(link_from(outbox.messages[0], choice)
                                ).get_data(as_text=True)
        assert title_of(page) == heading_of(page) == title
        assert texts.ANSWER_CHIP in page


def test_a_recorded_answer_names_its_choice(client, new_client, outbox):
    as_student(client, "recorded@example.org")
    submit_thesis(client)
    page = new_client().post(link_from(outbox.messages[0], "decline"),
                             data={}).get_data(as_text=True)
    assert title_of(page) == heading_of(page) == texts.ANSWER_TITLE_DECLINE
    assert texts.ANSWER_RECORDED.split("{")[0] in page


def test_an_answered_request_reads_neutrally_and_shows_the_answer(
        client, new_client, settings, outbox):
    as_student(client, "answered@example.org")
    submit_thesis(client)
    request_mail = outbox.messages[0]
    new_client().post(link_from(request_mail, "decline"), data={})
    page = new_client().get(link_from(request_mail, "confirm")).get_data(
        as_text=True)
    assert title_of(page) == heading_of(page) == texts.ANSWER_TITLE_NEUTRAL
    assert not any(title in page for title in CHOICE_TITLES)
    assert "вече е записан" in page and texts.ANSWER_WORD["decline"] in page
    record = record_for(settings, "answered@example.org")
    connection = connect(settings)
    assert applications.current_request(connection, record["id"])[
        "answer"] == "decline"
    connection.close()


def test_a_replaced_request_reads_neutrally(client, new_client, settings,
                                            outbox):
    as_student(client, "replaced@example.org")
    submit_thesis(client)
    old_confirm = link_from(outbox.messages[0], "confirm")
    record = record_for(settings, "replaced@example.org")
    viewer = as_staff(new_client(), make_account(settings, "staff1"))
    assert viewer.post("/staff/application/{}/supervisor".format(
        record["id"]), data={"professor": "dimitrov"}).status_code == 302
    page = new_client().get(old_confirm).get_data(as_text=True)
    assert title_of(page) == heading_of(page) == texts.ANSWER_TITLE_NEUTRAL
    assert not any(title in page for title in CHOICE_TITLES)
    assert texts.ANSWER_REPLACED in page


# --- Reminders --------------------------------------------------------------

def test_reminders_carry_links_that_still_record_an_answer(
        client, new_client, settings, outbox, clock):
    from superassistant import lists as list_module
    as_student(client, "remind@example.org")
    submit_thesis(client)
    first = outbox.messages[0]
    loaded = list_module.load(settings.lists_dir)
    connection = connect(settings)
    clock.advance(days=3)
    sent, failed = supervision.remind(connection, settings, loaded)
    assert len(sent) == 1 and failed == []
    reminder = outbox.messages[-1]
    assert reminder.intended == "p.ivanov@example.org"
    assert "Напомняне" in reminder.subject
    assert link_from(reminder, "confirm") == link_from(first, "confirm")
    # Again the same day: nothing more.
    assert supervision.remind(connection, settings, loaded) == ([], [])
    clock.advance(days=3)
    assert len(supervision.remind(connection, settings, loaded)[0]) == 1
    clock.advance(days=30)
    assert supervision.remind(connection, settings, loaded) == ([], [])
    new_client().post(link_from(reminder, "confirm"), data={})
    record = record_for(settings, "remind@example.org")
    assert applications.current_request(connection, record["id"])["answer"] \
        == "confirm"
    connection.close()


def test_a_refused_reminder_is_reported_and_not_recorded(
        client, settings, outbox, clock):
    from superassistant import lists as list_module, reminders
    import io
    as_student(client, "refusedreminder@example.org")
    submit_thesis(client)
    clock.advance(days=3)
    outbox.refuse = True
    out = io.StringIO()
    assert reminders.run(settings, out) == 1
    assert "p.ivanov@example.org" in out.getvalue()
    connection = connect(settings)
    assert connection.execute("SELECT reminders_sent FROM requests").fetchone()[
        0] == 0
    connection.close()


# --- Staff ------------------------------------------------------------------

@pytest.fixture
def staff(settings):
    return make_account(settings, "staff1")


def test_the_table_lists_submitted_applications_and_marks_the_waiting(
        client, new_client, settings, outbox, staff):
    as_student(client, "table@example.org")
    submit_thesis(client)
    draft = new_client()
    as_student(draft, "draft@example.org")
    save(draft, 1, {"name1": "Чернова", "grad_type": "exam"})
    viewer = as_staff(new_client(), staff)
    page = viewer.get("/staff").get_data(as_text=True)
    assert "Мария Петрова Тодорова" in page and "Чернова" not in page
    for column in ("Студент", "F№", "Програма", "Вид", "Тема",
                   "Научен ръководител", "Отговор", "Проверка"):
        assert column in page
    # In the rows: the counts above the table name the same states.
    table = page.split('id="applications"', 1)[1]
    assert 'class="waiting"' in table
    assert "чака научния ръководител" in table and "чака проверка" in table


def test_staff_see_every_field_and_the_answer_with_its_comment_and_time(
        client, new_client, settings, outbox, staff):
    as_student(client, "every@example.org")
    submit_thesis(client)
    new_client().post(link_from(outbox.messages[0], "confirm"),
                      data={"comment": "Ще ръководя."})
    record = record_for(settings, "every@example.org")
    viewer = as_staff(new_client(), staff)
    page = viewer.get("/staff/application/{}".format(record["id"])).get_data(
        as_text=True)
    for value in list(THESIS_TAB_2.values()) + ["0888 000 111", "5,50",
                                                "Ще ръководя.", "F104999"]:
        assert value in page
    connection = connect(settings)
    answered_at = applications.current_request(connection,
                                               record["id"])["answered_at"]
    connection.close()
    assert db.local_datetime(answered_at) in page


def test_checks_and_corrections_keep_what_they_replace(
        client, new_client, settings, outbox, staff):
    as_student(client, "fix@example.org")
    submit_thesis(client)
    record = record_for(settings, "fix@example.org")
    viewer = as_staff(new_client(), staff)
    base = "/staff/application/{}".format(record["id"])
    viewer.post(base + "/check", data={"result": "not_passed",
                                       "note": "Няма такъв F№"})
    viewer.post(base + "/correct", data={"field": "fn", "value": "f104998"})
    viewer.post(base + "/check", data={"result": "passed", "note": ""})
    connection = connect(settings)
    checks = applications.checks_of(connection, record["id"])
    assert [c["result"] for c in checks] == ["not_passed", "passed"]
    assert checks[0]["note"] == "Няма такъв F№"
    assert checks[0]["username"] == "staff1" and checks[0]["at"]
    assert applications.latest_check(connection, record["id"])["result"] == \
        "passed"
    (correction,) = applications.corrections_of(connection, record["id"])
    assert (correction["field"], correction["old_value"],
            correction["new_value"]) == ("fn", "F104999", "F104998")
    assert correction["username"] == "staff1" and correction["at"]
    connection.close()
    refused = viewer.post(base + "/correct",
                          data={"field": "name1", "value": "Мaрия"})
    assert refused.status_code == 400


def test_a_staff_change_of_supervisor_sends_a_new_request_keeping_the_answer(
        client, new_client, settings, outbox, staff):
    as_student(client, "change@example.org")
    submit_thesis(client)
    new_client().post(link_from(outbox.messages[0], "confirm"), data={})
    record = record_for(settings, "change@example.org")
    viewer = as_staff(new_client(), staff)
    base = "/staff/application/{}".format(record["id"])
    outbox.clear()
    outbox.refuse = True
    viewer.post(base + "/supervisor", data={"professor": "dimitrov"})
    assert record_for(settings, "change@example.org")["professor"] == "ivanov"
    outbox.refuse = False
    viewer.post(base + "/supervisor", data={"professor": "dimitrov"})
    (sent,) = outbox.messages
    assert sent.intended == "s.dimitrov@example.org"
    connection = connect(settings)
    rows = applications.requests_of(connection, record["id"])
    assert [r["answer"] for r in rows] == ["confirm", None]
    assert rows[0]["replaced_at"] is not None
    (correction,) = applications.corrections_of(connection, record["id"])
    assert correction["field"] == "professor"
    connection.close()
    page = client.get("/application").get_data(as_text=True)
    assert "Чака отговор" in page


# --- Who sees what ----------------------------------------------------------

def test_a_student_reaches_only_their_own_application(
        client, new_client, settings, outbox):
    as_student(client, "mine@example.org")
    submit_thesis(client)
    other = as_student(new_client(), "other@example.org")
    page = other.get("/application").get_data(as_text=True)
    assert "Мария" not in page and "Управление на риска" not in page
    for url in ("/staff", "/staff/application/1", "/owner", "/staff/reports",
                "/staff/reports/1/delete",
                "/staff/application/1/zaiavlenie.docx",
                "/staff/application/1/prilozhenie2.docx"):
        response = other.get(url)
        assert response.status_code in (302, 403, 404)
        assert "Мария" not in response.get_data(as_text=True)
