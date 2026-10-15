"""The bin in a real browser (constitution 5.15): a student submits a thesis
application at phone width; staff at desktop width remove it with a reason,
find it in the bin and out of the table, the student then sees only that it
was removed; staff put it back, remove it again and delete it on the second
page, after which the bin lists the deletion by number and the student,
still signed in, starts afresh.
"""

import pytest

from superassistant import texts
from tests.browser.conftest import DESKTOP, PHONE
from tests.browser.test_application_browser import STUDENT, submit_thesis
from tests.conftest import make_account

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
