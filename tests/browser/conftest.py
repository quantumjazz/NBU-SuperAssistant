"""The shared browser harness (NOW.md proof 5).

The real application, made by create_app over a fresh data directory with
invented people, serves on a free localhost port from a background thread;
mail goes in mode "owner" to the fake relay from tests/conftest.py, so no
message leaves the machine. Chromium pages come at phone width (390 x 844)
for students and supervisors and at desktop width (1280 x 800) for staff.

The owner's account exists before the start, as the start-up check requires,
and the setting names it, as on the host: OWNER_USERNAME and OWNER_PASSWORD.

Every browser test is marked @pytest.mark.browser; pytest.ini deselects them
unless `-m browser` is given. If Chromium cannot launch, they are skipped
with the reason.
"""

import re
import threading
from contextlib import contextmanager

import pytest
from werkzeug.serving import make_server

from superassistant.web import create_app
from tests.conftest import make_account, make_settings, prepare_data_dir

OWNER_USERNAME = "owner"
OWNER_EMAIL_ACCOUNT = "owner-account@example.org"
OWNER_PASSWORD = "собственик-парола-1"
PHONE = {"width": 390, "height": 844}
DESKTOP = {"width": 1280, "height": 800}


class LiveServer(object):
    """A running application: its URL, its settings and the fake relay."""

    def __init__(self, url, settings, outbox):
        self.url = url
        self.settings = settings
        self.outbox = outbox

    def latest(self, intended):
        """The latest message the relay received for this recipient."""
        return latest_message(self.outbox, intended)


def latest_message(outbox, intended):
    """The latest message the fake relay received for an intended
    recipient, or None. Its .text, .html and .subject are as sent."""
    found = outbox.to(intended)
    return found[-1] if found else None


def links_in(message):
    """Every http(s) link in a message's text, in order."""
    return re.findall(r"https?://\S+", message.text)


@contextmanager
def serve(settings):
    """Serve create_app(settings) on a free localhost port; yields the URL.

    Links in mail must lead back here, so base_url is set to the port the
    server was given.
    """
    app = create_app(settings)
    server = make_server("127.0.0.1", 0, app, threaded=True)
    url = "http://127.0.0.1:{}".format(server.server_port)
    settings.base_url = url
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield url
    finally:
        server.shutdown()
        thread.join(10)


@pytest.fixture
def live_settings(tmp_path):
    """A prepared data directory, mail mode "owner", the owner's account."""
    data_dir = tmp_path / "data"
    prepare_data_dir(data_dir)
    settings = make_settings(data_dir, mail_mode="owner",
                             owner_username=OWNER_USERNAME)
    make_account(settings, OWNER_USERNAME, OWNER_EMAIL_ACCOUNT,
                 OWNER_PASSWORD, approved=False)
    return settings


@pytest.fixture
def live_server(live_settings, outbox, clock):
    """The running application, with the fake relay installed and the test
    clock (tests/conftest.py Clock), so the sessions it offers do not depend
    on the day the tests run."""
    with serve(live_settings) as url:
        yield LiveServer(url, live_settings, outbox)


@pytest.fixture(scope="session")
def chromium():
    sync_api = pytest.importorskip("playwright.sync_api")
    manager = sync_api.sync_playwright().start()
    try:
        browser = manager.chromium.launch()
    except Exception as exc:          # any launch failure is a skip reason
        manager.stop()
        pytest.skip("Chromium cannot launch: {}".format(exc))
    yield browser
    browser.close()
    manager.stop()


@pytest.fixture
def open_page(chromium):
    """open_page(size) -> a page in a new browser context (its own cookies).

    size is PHONE or DESKTOP. Every context opened is closed afterwards.
    """
    contexts = []

    def opener(size=DESKTOP):
        options = {"viewport": size, "locale": "bg-BG"}
        if size == PHONE:
            options.update(is_mobile=True, has_touch=True)
        context = chromium.new_context(**options)
        context.set_default_timeout(10000)
        contexts.append(context)
        return context.new_page()

    yield opener
    for context in contexts:
        context.close()


@pytest.fixture
def phone_page(open_page):
    return open_page(PHONE)


@pytest.fixture
def desktop_page(open_page):
    return open_page(DESKTOP)
