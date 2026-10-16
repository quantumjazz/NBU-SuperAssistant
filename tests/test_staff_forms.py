"""Staff download and print each applicant's forms, and the student is told
there is nothing to print or hand in (constitution 5.5; the owner, 16
October 2026: „Попълнени документи“, the line "visible in each case",
staff downloads "Yes, build it now", an application in the bin "Yes, like
reports").

Read back from the .docx (CLAUDE.md "Check a generated document twice", by
content; the forms' layout in Word is checked in test_documents.py and by
eye). Every role that must not reach the files is tried. Everything is
invented.
"""

import re

from hypothesis import given, strategies as st

from superassistant import applications, documents, texts
from superassistant.web import documents as document_pages
from tests.conftest import Client, connect, insert_application, make_account
from tests.test_application_flow import as_staff, as_student, submit_thesis
from tests.test_documents import every_paragraph, read

THESIS = dict(grad_type="thesis", name1="Ина", name2="Йорданова",
              name3="Кирова", fn="F200001", phone="0888 123 456",
              programme="BSNADM01", professor="ivanov",
              topic="Тема на тезата", average_grade="5.25",
              rationale="ред 1\nред 2")
EXAM = dict(grad_type="exam", name1="Лора", name2="Методиева",
            name3="Ненова", fn="F200002")


def staff_url(application_id, form):
    return "/staff/application/{}/{}.docx".format(application_id, form)


def text_of(data):
    return "\n".join(p.text for p in every_paragraph(read(data)))


def disposition(reply):
    return reply.headers["Content-Disposition"]


def test_staff_download_each_applicants_forms(settings, app):
    thesis = insert_application(settings, "ina@example.org", **THESIS)
    exam = insert_application(settings, "lora@example.org", **EXAM)
    draft = insert_application(settings, "olga@example.org", submitted=False,
                               grad_type="thesis", name1="Олга",
                               fn="F200003")
    office = as_staff(Client(app.test_client()), make_account(settings))

    reply = office.get(staff_url(thesis, "zaiavlenie"))
    assert reply.status_code == 200
    assert reply.mimetype == documents.MIMETYPE
    assert "attachment" in disposition(reply) and disposition(reply).isascii()
    assert "zaiavlenie-deklaracia-{}-F200001.docx".format(thesis) \
        in disposition(reply)
    text = text_of(reply.data)
    assert "Ина Йорданова Кирова" in text and "Тема на тезата" in text
    assert "Лора" not in text
    reply = office.get(staff_url(thesis, "prilozhenie2"))
    assert reply.status_code == 200
    assert "prilozhenie-2-{}-F200001.docx".format(thesis) in disposition(reply)
    assert "ред 1\nред 2" in [p.text for p in read(reply.data).paragraphs]

    reply = office.get(staff_url(exam, "zaiavlenie"))
    assert reply.status_code == 200
    assert "zaiavlenie-deklaracia-{}-F200002.docx".format(exam) \
        in disposition(reply)
    text = text_of(reply.data)
    assert "Лора Методиева Ненова" in text and "Ина" not in text
    assert "чрез държавен изпит" in text
    assert office.get(staff_url(exam, "prilozhenie2")).status_code == 404

    # Drafts are not staff's to see, and a number no application has is
    # not found.
    for number in (draft, 999):
        for form in ("zaiavlenie", "prilozhenie2"):
            assert office.get(staff_url(number, form)).status_code == 404


def test_staff_print_the_same_forms_the_student_downloads(settings, app):
    """The staff file is the student's own document, word for word."""
    number = insert_application(settings, "ina@example.org", **THESIS)
    office = as_staff(Client(app.test_client()), make_account(settings))
    student = as_student(Client(app.test_client()), "ina@example.org")
    for form in ("zaiavlenie", "prilozhenie2"):
        mine = student.get("/application/forms/{}.docx".format(form))
        theirs = office.get(staff_url(number, form))
        assert mine.status_code == theirs.status_code == 200
        assert text_of(mine.data) == text_of(theirs.data)


def test_staff_forms_follow_corrections_and_the_type(settings, app):
    """Each download is built from the record as it stands: a correction
    shows at once, and after a change to a state exam Приложение 2 is gone
    and the заявление prints none of the thesis entries kept."""
    number = insert_application(settings, "ina@example.org", **THESIS)
    office = as_staff(Client(app.test_client()), make_account(settings))
    base = "/staff/application/{}".format(number)
    assert office.post(base + "/correct", data={
        "field": "topic", "value": "Поправена тема"}).status_code == 302
    text = text_of(office.get(staff_url(number, "zaiavlenie")).data)
    assert "Поправена тема" in text and "Тема на тезата" not in text
    for printed in ("0888 123 456", "5.25", "Иванов"):
        assert printed in text, printed

    assert office.post(base + "/type",
                       data={"grad_type": "exam"}).status_code == 302
    assert office.get(staff_url(number, "prilozhenie2")).status_code == 404
    text = text_of(office.get(staff_url(number, "zaiavlenie")).data)
    assert "чрез държавен изпит" in text
    for kept in ("Поправена тема", "0888 123 456", "5.25", "Иванов"):
        assert kept not in text, kept
    page = office.get(base).get_data(as_text=True)
    assert texts.STAFF_RETAINED_THESIS in page
    assert staff_url(number, "zaiavlenie") in page
    assert staff_url(number, "prilozhenie2") not in page


def test_staff_download_forms_in_the_bin_until_deleted(settings, app):
    staff = make_account(settings)
    number = insert_application(settings, "ina@example.org", **THESIS)
    connection = connect(settings)
    assert applications.remove(connection, number, "other", "", staff["id"])
    office = as_staff(Client(app.test_client()), staff)
    student = as_student(Client(app.test_client()), "ina@example.org")
    for form in ("zaiavlenie", "prilozhenie2"):
        assert office.get(staff_url(number, form)).status_code == 200
        assert student.get("/application/forms/{}.docx".format(
            form)).status_code == 404
    page = office.get("/staff/application/{}".format(number)).get_data(
        as_text=True)
    assert 'id="staff-forms"' in page and 'id="in-bin"' in page
    assert staff_url(number, "zaiavlenie") in page
    assert staff_url(number, "prilozhenie2") in page

    assert applications.delete(connection, number, staff["id"])
    connection.close()
    for form in ("zaiavlenie", "prilozhenie2"):
        assert office.get(staff_url(number, form)).status_code == 404


def test_only_approved_staff_download_forms(settings, app):
    number = insert_application(settings, "ina@example.org", **THESIS)
    binned = insert_application(settings, "bora@example.org",
                                **dict(THESIS, name1="Бора", fn="F200009"))
    staff = make_account(settings)
    connection = connect(settings)
    applications.remove(connection, binned, "graduated", "", staff["id"])
    connection.close()
    waiting = make_account(settings, username="waiting", approved=False)
    for visitor in (Client(app.test_client()),
                    as_student(Client(app.test_client()), "ina@example.org"),
                    as_student(Client(app.test_client()), "bora@example.org"),
                    as_staff(Client(app.test_client()), waiting)):
        for application_id in (number, binned):
            for form in ("zaiavlenie", "prilozhenie2"):
                reply = visitor.get(staff_url(application_id, form))
                assert reply.status_code == 302
                assert reply.headers["Location"].endswith("/staff/sign-in")
                assert reply.mimetype != documents.MIMETYPE
                body = reply.get_data(as_text=True)
                assert "Ина" not in body and "Бора" not in body


def test_the_staff_page_offers_the_forms_of_its_application(settings, app):
    thesis = insert_application(settings, "ina@example.org", **THESIS)
    exam = insert_application(settings, "lora@example.org", **EXAM)
    # A state exam still holding thesis entries offers only the заявление.
    kept = insert_application(settings, "mila@example.org",
                              **dict(EXAM, name1="Мила", fn="F200004",
                                     topic="Стара тема", professor="ivanov"))
    office = as_staff(Client(app.test_client()), make_account(settings))
    for number, thesis_forms in ((thesis, True), (exam, False),
                                 (kept, False)):
        page = office.get("/staff/application/{}".format(number)).get_data(
            as_text=True)
        assert texts.STAFF_FORMS_TITLE in page
        assert 'id="staff-zaiavlenie"' in page
        assert staff_url(number, "zaiavlenie") in page
        assert (staff_url(number, "prilozhenie2") in page) is thesis_forms
        assert ('id="staff-prilozhenie2"' in page) is thesis_forms
        # Only this application's files.
        for other in {thesis, exam, kept} - {number}:
            assert "/staff/application/{}/".format(other) not in page


@given(st.integers(1, 10 ** 9), st.one_of(
    st.none(), st.text(max_size=12),
    st.text(alphabet="0123456789", min_size=1, max_size=12).map(
        lambda digits: "F" + digits)))
def test_a_staff_file_name_is_ascii_and_names_the_application(number, fn):
    """The name carries the application's number always, and the F№ exactly
    when it is „F“ and the digits 0 to 9; an F№ stored before that rule is
    left out, so the name stays ASCII whatever was stored."""
    record = {"id": number, "fn": fn}
    for form in ("zaiavlenie-deklaracia", "prilozhenie-2"):
        name = document_pages._staff_name(form, record)
        assert name.isascii()
        rule = bool(fn) and re.fullmatch(r"F[0-9]+", fn) is not None
        expected = "{}-{}{}.docx".format(form, number,
                                         "-" + fn if rule else "")
        assert name == expected


def test_a_file_for_an_fn_stored_before_the_rule_is_still_ascii(settings,
                                                                app):
    number = insert_application(settings, "ina@example.org",
                                **dict(THESIS, fn="Ф 12/б"))
    office = as_staff(Client(app.test_client()), make_account(settings))
    reply = office.get(staff_url(number, "zaiavlenie"))
    assert reply.status_code == 200
    assert disposition(reply).isascii()
    assert "zaiavlenie-deklaracia-{}.docx".format(number) \
        in disposition(reply)
    assert "Ф 12/б" in text_of(reply.data)


# --- The student's card -------------------------------------------------------

def forms_card(page):
    found = re.search(r'<section id="forms".*?</section>', page, re.S)
    assert found, "no forms card"
    return found.group(0)


def test_every_student_is_told_there_is_nothing_to_print(client, new_client,
                                                         settings):
    """The owner's heading and line, for a thesis and for a state exam,
    above the download buttons; the old heading is gone."""
    as_student(client, "maria@example.org")
    submit_thesis(client)
    insert_application(settings, "lora@example.org", **EXAM)
    exam = as_student(new_client(), "lora@example.org")
    for student, thesis_forms in ((client, True), (exam, False)):
        page = student.get("/application").get_data(as_text=True)
        assert "Документи за печат и подпис" not in page
        card = forms_card(page)
        assert "<h2>Попълнени документи</h2>" in card
        lead = ("Не е нужно да отпечатвате и представяте документите: "
                "администрацията на департамента вече разполага с тях. "
                "Можете да ги изтеглите за справка.")
        assert '<p id="forms-lead">' + lead + "</p>" in card
        assert card.index(lead) < card.index("/application/forms/")
        assert texts.FORMS_ZAIAVLENIE in card
        assert (texts.FORMS_PRILOZHENIE2 in card) is thesis_forms


def test_a_draft_has_no_forms_card(client, settings):
    insert_application(settings, "olga@example.org", submitted=False,
                       grad_type="thesis", name1="Олга")
    page = as_student(client, "olga@example.org").get(
        "/application").get_data(as_text=True)
    assert 'id="forms"' not in page and texts.FORMS_LEAD not in page
