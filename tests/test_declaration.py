"""The declaration that the credits are covered (the task of 13 October 2026;
constitution 5.3): "must be ticked to submit, as he signs the same sentence on
paper". A tick on the first tab for both types, saved with the draft and
recorded with when at submission; staff see it; the заявление does not
change. Everyone is invented.
"""

import io
import re

import docx

from superassistant import documents, lists, texts
from tests.conftest import connect, insert_application, make_account
from tests.test_documents import every_paragraph
from tests.test_application_flow import (THESIS_TAB_1, THESIS_TAB_2,
                                         as_staff, as_student, record_for,
                                         save)

EXAM = {"name1": "Калина", "name2": "Иванова", "name3": "Стоева",
        "fn": "500002", "grad_type": "exam"}


def unticked(fields):
    return dict((k, v) for k, v in fields.items() if k != "credits_declared")


def test_the_box_is_on_the_first_tab_with_the_forms_sentence(client):
    as_student(client, "box@example.org")
    first = client.get("/application").get_data(as_text=True)
    assert texts.DECLARE_CREDITS in first
    assert re.search(r'<input type="checkbox" id="credits_declared" '
                     r'name="credits_declared"', first)
    # Under the faculty number, above the first tab's buttons.
    assert first.index('id="fn"') < first.index('id="credits_declared"') \
        < first.index('name="action"')
    save(client, 1, THESIS_TAB_1, "next")
    second = client.get("/application?tab=2").get_data(as_text=True)
    assert "credits_declared" not in second


def test_a_state_exam_without_the_tick_is_not_submitted(client, settings,
                                                         outbox, clock):
    as_student(client, "exam-tick@example.org")
    response = save(client, 1, EXAM, "submit")
    page = response.get_data(as_text=True)
    assert response.status_code == 400
    assert re.search(r'id="credits_declared-error">' + re.escape(
        texts.TICK_REQUIRED), page)
    record = record_for(settings, "exam-tick@example.org")
    assert record["submitted_at"] is None and record["credits_declared"] == 0
    assert record["name1"] == "Калина"            # the draft is still saved
    response = save(client, 1, dict(EXAM, credits_declared="1"), "submit")
    assert response.status_code == 302
    record = record_for(settings, "exam-tick@example.org")
    assert record["credits_declared"] == 1
    assert record["credits_declared_at"] == record["submitted_at"] == \
        clock().isoformat(timespec="seconds")


def test_a_thesis_without_the_tick_goes_back_to_the_first_tab(
        client, settings, outbox, clock):
    as_student(client, "thesis-tick@example.org")
    assert save(client, 1, unticked(THESIS_TAB_1), "next").status_code == 302
    response = save(client, 2, THESIS_TAB_2, "submit")
    page = response.get_data(as_text=True)
    assert response.status_code == 400
    assert '<input type="hidden" name="tab" value="1">' in page
    assert re.search(r'id="credits_declared-error">' + re.escape(
        texts.TICK_REQUIRED), page)
    assert outbox.messages == []                  # no request to a supervisor
    assert record_for(settings, "thesis-tick@example.org")[
        "submitted_at"] is None
    assert save(client, 1, THESIS_TAB_1, "next").status_code == 302
    assert save(client, 2, THESIS_TAB_2, "submit").status_code == 302
    record = record_for(settings, "thesis-tick@example.org")
    assert record["credits_declared_at"] == record["submitted_at"] == \
        clock().isoformat(timespec="seconds")
    assert len(outbox.messages) == 1


def test_the_tick_is_saved_with_the_draft_and_shown_again(client, settings):
    as_student(client, "draft-tick@example.org")
    save(client, 1, dict(EXAM, credits_declared="1"))
    assert record_for(settings, "draft-tick@example.org")[
        "credits_declared"] == 1
    page = client.get("/application").get_data(as_text=True)
    assert re.search(r'id="credits_declared"[^>]*checked', page)
    # A refused entry keeps the tick as it was sent.
    refused = save(client, 1, dict(EXAM, name1="Kалина",
                                   credits_declared="1"))
    assert refused.status_code == 400
    assert re.search(r'id="credits_declared"[^>]*checked',
                     refused.get_data(as_text=True))
    save(client, 1, EXAM)
    assert record_for(settings, "draft-tick@example.org")[
        "credits_declared"] == 0
    page = client.get("/application").get_data(as_text=True)
    assert not re.search(r'id="credits_declared"[^>]*checked', page)
    assert record_for(settings, "draft-tick@example.org")[
        "credits_declared_at"] is None


def test_staff_see_the_declaration_and_a_pilot_application_shows_none(
        client, new_client, settings, outbox):
    as_student(client, "declared@example.org")
    save(client, 1, dict(EXAM, credits_declared="1"), "submit")
    ticked = record_for(settings, "declared@example.org")
    # Submitted before the tick existed: nothing recorded.
    pilot = insert_application(settings, "pilot@example.org",
                               grad_type="exam", name1="Пилот",
                               name2="Тестов", name3="Студент", fn="F1")
    viewer = as_staff(new_client(), make_account(settings, "staff1"))
    for number, shown in ((ticked["id"], "да"), (pilot, "—")):
        page = viewer.get("/staff/application/{}".format(number)).get_data(
            as_text=True)
        assert "<dt>{}</dt><dd id=\"declared\">{}</dd>".format(
            texts.STAFF_DECLARED, shown) in page
    table = viewer.get("/staff").get_data(as_text=True)
    assert "<th>Кредити</th>" in table
    for number, shown in ((ticked["id"], "да"), (pilot, "—")):
        row = table.split('data-id="{}"'.format(number))[1].split("</tr>")[0]
        assert '<td class="declared">{}</td>'.format(shown) in row


def test_a_student_cannot_see_anothers_declaration(client, new_client,
                                                   settings, outbox):
    as_student(client, "first@example.org")
    save(client, 1, dict(EXAM, credits_declared="1"), "submit")
    first = record_for(settings, "first@example.org")
    other = as_student(new_client(), "second@example.org")
    page = other.get("/application").get_data(as_text=True)
    assert "Калина" not in page
    assert not re.search(r'id="credits_declared"[^>]*checked', page)
    for url in ("/staff", "/staff/application/{}".format(first["id"])):
        response = other.get(url)
        assert response.status_code == 302
        assert texts.STAFF_DECLARED not in response.get_data(as_text=True)


def test_a_type_correction_neither_needs_nor_changes_the_tick(
        client, new_client, settings, outbox):
    pilot = insert_application(settings, "type-pilot@example.org",
                               grad_type="exam", name1="Ана", name2="Бойкова",
                               name3="Вълчева", fn="F600001")
    data = dict(THESIS_TAB_1)
    data.update(THESIS_TAB_2)
    for key in ("grad_type", "professor", "credits_declared", "fn"):
        data.pop(key)
    viewer = as_staff(new_client(), make_account(settings, "staff1"))
    base = "/staff/application/{}".format(pilot)
    for field, value in data.items():
        assert viewer.post(base + "/correct", data={
            "field": field, "value": value}).status_code == 302
    assert viewer.post(base + "/type", data={
        "grad_type": "thesis", "professor": "ivanov"}).status_code == 302
    connection = connect(settings)
    row = connection.execute("SELECT * FROM applications WHERE id = ?",
                             (pilot,)).fetchone()
    connection.close()
    assert row["grad_type"] == "thesis"
    assert row["credits_declared"] == 0 and row["credits_declared_at"] is None


def test_the_zaiavlenie_is_the_same_with_or_without_the_tick(settings):
    loaded = lists.load(settings.lists_dir)
    record = {"id": 1, "email": "a@example.org", "grad_type": "thesis",
              "name1": "Ана", "name2": "Бойкова", "name3": "Вълчева",
              "fn": "F1", "phone": "1", "programme": "BSNADM01",
              "topic": "Тема", "average_grade": "5", "professor": "ivanov",
              "sup_title": "", "sup_name": "", "sup_email": "",
              "submitted_at": "2026-10-13T09:00:00+00:00"}

    def text(declared):
        data = documents.zaiavlenie(dict(record, credits_declared=declared,
                                         credits_declared_at=None if not
                                         declared else record["submitted_at"]),
                                    loaded)
        return [p.text for p in every_paragraph(
            docx.Document(io.BytesIO(data)))]

    for grad_type in ("thesis", "exam"):
        record["grad_type"] = grad_type
        assert text(1) == text(0)
        # The sentence the box repeats is printed on both parts of the form.
        assert sum(line.startswith(texts.DECLARE_CREDITS[:-1])
                   for line in text(1)) == 2
