"""The schedule of sessions in a real browser (constitution 5.13; the
milestone-3 plan's proof 5, as far as requirement 4 goes): at phone width a
student reads the schedule, each session stacked with its deadlines, the
passed ones marked; is refused without a session and the tick; chooses the
session and ticks, submits, and then sees the session and the schedule. At
desktop width staff see the session in the table and on the application's
page, and correct it to a passed session, the correction logged.
"""

import pytest

from superassistant import texts
from tests.browser.conftest import DESKTOP, PHONE
from tests.browser.test_application_browser import sign_in_by_link
from tests.conftest import insert_application, insert_request, make_account

sync_api = pytest.importorskip("playwright.sync_api")
expect = sync_api.expect

pytestmark = pytest.mark.browser

JANUARY = "26 януари 2027\u00a0г. (вторник)"
SEPTEMBER = "26 септември 2026\u00a0г. (събота)"


def test_a_student_chooses_a_session_and_staff_correct_it(live_server,
                                                          open_page):
    page = open_page(PHONE)
    sign_in_by_link(page, live_server, "session@example.org")

    schedule = page.locator("#schedule")
    expect(schedule).to_be_visible()
    rows = schedule.locator("tbody tr")
    expect(rows).to_have_count(4)
    expect(schedule.locator("tr.passed")).to_have_count(3)
    expect(rows.nth(3)).to_contain_text(JANUARY)
    expect(rows.nth(3)).to_contain_text("до 13 ноември 2026 г.")
    expect(page.locator("#schedule-note")).to_have_text(texts.SCHEDULE_NOTE)
    # At phone width each session stacks: no column headings shown, each
    # deadline under its heading, and nothing wider than the screen.
    assert rows.nth(3).evaluate("e => getComputedStyle(e).display") == "block"
    assert schedule.locator("thead").bounding_box()["height"] <= 1
    assert page.evaluate(
        "document.documentElement.scrollWidth") <= PHONE["width"]
    expect(page.locator("input[name=grad_session]")).to_have_count(1)

    page.fill("#name1", "Румен")
    page.fill("#name2", "Колев")
    page.fill("#name3", "Данов")
    page.fill("#fn", "300456")
    page.check("input[name=grad_type][value=exam]")
    page.check("#credits_declared")
    page.locator("#submit-exam").click()
    expect(page.locator("#grad_session-error")).to_have_text(
        texts.REFUSED_SESSION)
    expect(page.locator("#schedule_ack-error")).to_have_text(
        texts.TICK_REQUIRED)

    page.locator("label.choice", has_text=JANUARY).click()
    page.locator("label[for=schedule_ack]").click()
    expect(page.locator("#schedule_ack")).to_be_checked()
    page.locator("#submit-exam").click()
    expect(page.locator("#status")).to_contain_text("Подадено на")
    expect(page.locator("#chosen-session")).to_have_text(JANUARY)
    expect(page.locator("#acknowledged")).to_have_text("да")
    expect(page.locator("#session #schedule")).to_be_visible()
    expect(page.locator("#chosen-line")).to_have_text(
        "Избрана сесия: " + JANUARY)
    assert page.evaluate(
        "document.documentElement.scrollWidth") <= PHONE["width"]

    # A thesis application as staff see many: the table must still fit a
    # desk's screen with the session in it.
    thesis = insert_application(
        live_server.settings, "desislava@example.org", grad_type="thesis",
        name1="Десислава", name2="Петкова", name3="Маринова", fn="F201234",
        phone="0888123456", programme="MSNSMQ09",
        topic="Качество на услугите в публичния сектор",
        average_grade="5,75", professor="georgieva",
        credits_declared=1, credits_declared_at="2026-10-15T09:00:00+00:00")
    insert_request(live_server.settings, thesis,
                   sup_email="e.georgieva@example.org", professor="georgieva")
    make_account(live_server.settings, "staff5", password="служител-5")
    desk = open_page(DESKTOP)
    desk.goto(live_server.url + "/staff/sign-in")
    desk.fill("#login", "staff5")
    desk.fill("#password", "служител-5")
    desk.get_by_role("button", name=texts.STAFF_SIGNIN_BUTTON).click()
    wrap = desk.locator(".table-wrap")
    assert wrap.evaluate("w => w.scrollWidth <= w.clientWidth"), \
        "the staff table scrolls sideways at 1280 px"
    row = desk.locator("#applications tbody tr", has_text="Румен")
    expect(row.locator("td.session")).to_contain_text(JANUARY)
    expect(row.locator(".acknowledged")).to_have_text("график: да")
    other = desk.locator("#applications tbody tr", has_text="Десислава")
    expect(other.locator("td.session")).to_contain_text("—")
    expect(other.locator(".acknowledged")).to_have_text("график: —")
    desk.get_by_role("link", name="Румен Колев Данов").click()
    expect(desk.locator("#session")).to_have_text(JANUARY)
    desk.select_option("#grad_session", "2026-09")
    desk.locator("#save-session").click()
    expect(desk.locator("main")).to_contain_text(texts.STAFF_CORRECTED)
    expect(desk.locator("#session")).to_have_text(SEPTEMBER)
    expect(desk.locator("#corrections")).to_contain_text(
        "Сесия: от „{}“ на „{}“".format(JANUARY, SEPTEMBER))

    page.reload()
    expect(page.locator("#chosen-session")).to_have_text(SEPTEMBER)
