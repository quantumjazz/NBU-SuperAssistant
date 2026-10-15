"""The bin in a real browser (constitution 5.15): a student submits a thesis
application at phone width; staff at desktop width remove it with a reason,
find it in the bin and out of the table, the student then sees only that it
was removed; staff put it back, remove it again and delete it on the second
page, after which the bin lists the deletion by number and the student,
still signed in, starts afresh.

The bin for reports (constitution 5.14): staff generate a topic report,
remove it with one press, find it in the bin, its student waiting for a
report again, put it back, remove it again and delete it on the second page,
after which the bin lists the deletion.
"""

import pytest

from superassistant import texts
from tests.browser.conftest import DESKTOP, PHONE
from tests.browser.test_application_browser import STUDENT, submit_thesis
from tests.conftest import (insert_application, insert_check,
                            insert_request, make_account)

sync_api = pytest.importorskip("playwright.sync_api")
expect = sync_api.expect

pytestmark = pytest.mark.browser

NAME = " ".join(STUDENT[:3])


def test_remove_put_back_and_delete_in_the_browser(live_server, open_page):
    student = open_page(PHONE)
    submit_thesis(student, live_server, "bin@example.org", STUDENT)

    make_account(live_server.settings, "staff4", password="служител-4")
    desk = open_page(DESKTOP)
    desk.goto(live_server.url + "/staff/sign-in")
    desk.fill("#login", "staff4")
    desk.fill("#password", "служител-4")
    desk.get_by_role("button", name=texts.STAFF_SIGNIN_BUTTON).click()
    desk.get_by_role("link", name=NAME).click()

    # The first step: a reason, then „Премахни“.
    desk.locator("#remove-application").click()
    expect(desk.locator("#remove-error")).to_have_text(texts.BIN_CHOOSE_REASON)
    desk.check("input[name=reason][value=other]")
    desk.fill("#bin_note", "тестов запис")
    desk.locator("#remove-application").click()
    expect(desk).to_have_url(live_server.url + "/staff")
    expect(desk.locator("main")).to_contain_text(texts.BIN_REMOVED)
    expect(desk.locator("main")).not_to_contain_text(NAME)

    desk.get_by_role("link", name=texts.NAV_BIN).click()
    row = desk.locator("#bin tbody tr").first
    for shown in (NAME, "друго", "тестов запис", "staff4"):
        expect(row).to_contain_text(shown)

    # The student sees only that it was removed.
    student.goto(live_server.url + "/application")
    expect(student.locator("#removed")).to_have_text(texts.STATUS_REMOVED)
    expect(student.locator("main")).not_to_contain_text(STUDENT[4])

    # Put back: in the table again.
    row.get_by_role("button", name=texts.BIN_RESTORE).click()
    expect(desk.locator("main")).to_contain_text(texts.BIN_RESTORED)
    desk.goto(live_server.url + "/staff")
    expect(desk.locator("#applications")).to_contain_text(NAME)

    # Removed again, then deleted on the second page.
    desk.get_by_role("link", name=NAME).click()
    desk.check("input[name=reason][value=graduated]")
    desk.locator("#remove-application").click()
    desk.goto(live_server.url + "/staff/bin")
    desk.locator("#bin tbody tr").first.get_by_role(
        "link", name=texts.BIN_DELETE).click()
    expect(desk.locator("h1")).to_have_text(texts.BIN_DELETE_TITLE)
    expect(desk.locator("#application")).to_contain_text(NAME)
    desk.locator("#delete-application").click()
    expect(desk).to_have_url(live_server.url + "/staff/bin")
    expect(desk.locator("main")).to_contain_text(texts.BIN_DELETED)
    expect(desk.locator("main")).to_contain_text(texts.BIN_EMPTY)
    deletions = desk.locator("#deletions")
    expect(deletions).to_contain_text("№ 1")
    expect(deletions).to_contain_text("дипломиран(а)")
    expect(deletions).not_to_contain_text(NAME)

    # The student, still signed in, starts afresh.
    student.goto(live_server.url + "/application")
    expect(student.locator("#application-form")).to_be_visible()
    expect(student.locator("#name1")).to_have_value("")


def test_remove_put_back_and_delete_a_report_in_the_browser(live_server,
                                                           open_page):
    settings = live_server.settings
    staff = make_account(settings, "staff5", password="служител-5")
    number = insert_application(settings, "report@example.org",
                                grad_type="thesis", programme="BSNADM01",
                                name1="Ана", name2="Бойкова",
                                name3="Вълчева", fn="F300001",
                                topic="Тема", professor="ivanov")
    insert_request(settings, number, answer="confirm")
    insert_check(settings, number, "passed", staff["id"])
    desk = open_page(DESKTOP)
    desk.goto(live_server.url + "/staff/sign-in")
    desk.fill("#login", "staff5")
    desk.fill("#password", "служител-5")
    desk.get_by_role("button", name=texts.STAFF_SIGNIN_BUTTON).click()
    desk.get_by_role("link", name=texts.NAV_REPORTS).click()
    desk.select_option("#programme", "BSNADM01")
    desk.locator("main form button[type=submit]").first.click()
    expect(desk.locator("main")).to_contain_text(texts.REPORTS_MADE)
    expect(desk.locator("#remove-hint")).to_have_text(
        texts.REPORTS_REMOVE_HINT)

    # The first step: one press.
    desk.get_by_role("button", name=texts.REPORTS_REMOVE).click()
    expect(desk.locator("main")).to_contain_text(texts.REPORTS_REMOVED)
    expect(desk.locator("main")).to_contain_text(texts.REPORTS_NONE_KEPT)
    desk.get_by_role("link", name=texts.NAV_STAFF).click()
    expect(desk.locator(".waiting-mark").first).to_have_text(
        texts.STAFF_WAITING_REPORT)

    desk.get_by_role("link", name=texts.NAV_BIN).click()
    row = desk.locator("#bin-reports tbody tr").first
    for shown in ("doklad-temi-1-", "Администрация и управление", "staff5"):
        expect(row).to_contain_text(shown)
    with desk.expect_download() as download:
        row.get_by_role("link", name="doklad-temi-1-").click()
    assert download.value.suggested_filename.startswith("doklad-temi-1-")

    # Put back: kept again, nobody waits.
    row.get_by_role("button", name=texts.BIN_RESTORE).click()
    expect(desk.locator("main")).to_contain_text(texts.REPORTS_RESTORED)
    expect(desk.locator('a[href="/staff/reports/1.docx"]')).to_be_visible()
    desk.get_by_role("link", name=texts.NAV_STAFF).click()
    expect(desk.locator(".waiting-mark")).to_have_count(0)
    desk.get_by_role("link", name=texts.NAV_REPORTS).click()

    # Removed again, then deleted on the second page.
    desk.get_by_role("button", name=texts.REPORTS_REMOVE).click()
    desk.get_by_role("link", name=texts.NAV_BIN).click()
    desk.locator("#bin-reports tbody tr").first.get_by_role(
        "link", name=texts.BIN_DELETE).click()
    expect(desk.locator("h1")).to_have_text(texts.REPORTS_DELETE_TITLE)
    expect(desk.locator("#report")).to_contain_text("doklad-temi-1-")
    desk.locator("#delete-report").click()
    expect(desk).to_have_url(live_server.url + "/staff/bin")
    expect(desk.locator("main")).to_contain_text(texts.REPORTS_DELETED)
    expect(desk.locator("main")).to_contain_text(texts.BIN_EMPTY)
    deletions = desk.locator("#report-deletions")
    expect(deletions).to_contain_text("doklad-temi-1-")
    expect(deletions).to_contain_text("staff5")
    expect(deletions).not_to_contain_text("Вълчева")
