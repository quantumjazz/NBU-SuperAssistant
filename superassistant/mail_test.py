"""`python -m superassistant mail-test <address>`: one test message, to prove
mail works before anybody relies on it.

The approach is CourseBench's (coursebench/admin.py, cmd_mail_test): say
first what will happen (the mode, the relay and the sender), then whether the
relay accepted the message, and that accepted is not delivered, because mail
accepted and then dropped is the failure that looks exactly like everything
working. The message goes the way every message goes (mail.send): printed in
mode console or unset, to the owner with <address> on top in mode owner, to
<address> in mode send. It bypasses the rate limits: only someone on the host
can run it.

Exit status: 0 when sent or printed, 1 when refused or not configured, 2 for
bad usage (no address, more than one, or one that is not an address).
"""

import sys
from email.utils import formataddr

from superassistant import mail, texts
from superassistant.settings import from_env


def _mail_settings_problem(settings):
    """Why mail cannot go as configured, as one line, or ""."""
    problems = settings.mail_problems()
    if not problems and settings.effective_mail_mode() in ("owner", "send"):
        stopper = mail.relay_problem(settings)
        if stopper:
            problems = [stopper]
    return " ".join(problems)


def _plan(settings, address):
    """What is about to happen, in the owner's words."""
    mode = settings.effective_mail_mode()
    if mode == "console":
        label = settings.mail_mode or texts.CLI_MAIL_TEST_MODE_UNSET
        return texts.CLI_MAIL_TEST_PLAN_CONSOLE.format(mode=label,
                                                       address=address)
    values = {"address": address, "owner": settings.owner_email,
              "relay": mail.relay_description(settings),
              "sender": formataddr((mail.FROM_NAME, settings.mail_from))}
    if mode == "owner":
        return texts.CLI_MAIL_TEST_PLAN_OWNER.format(**values)
    return texts.CLI_MAIL_TEST_PLAN_SEND.format(**values)


def run(settings, address, out=None, err=None):
    """Send or print the test message. Returns the exit status."""
    out = out or sys.stdout
    err = err or sys.stderr
    stopper = _mail_settings_problem(settings)
    if stopper:
        err.write(texts.CLI_MAIL_TEST_UNCONFIGURED.format(stopper) + "\n")
        return 1
    out.write(_plan(settings, address) + "\n\n")
    out.flush()
    message = mail.Message(address, texts.CLI_MAIL_TEST_SUBJECT,
                           texts.CLI_MAIL_TEST_TEXT.format(
                               address=address, base_url=settings.base_url))
    try:
        mail.send(settings, message, out=out)
    except mail.MailFailed as exc:
        err.write(texts.CLI_MAIL_TEST_REFUSED.format(exc) + "\n")
        return 1
    if settings.effective_mail_mode() == "console":
        out.write(texts.CLI_MAIL_TEST_PRINTED + "\n")
    else:
        out.write(texts.CLI_MAIL_TEST_ACCEPTED + "\n")
    return 0


def main(argv):
    argv = list(argv)
    if argv in (["-h"], ["--help"]):
        sys.stdout.write(texts.CLI_MAIL_TEST_USAGE + "\n")
        return 0
    if len(argv) != 1 or argv[0].startswith("-"):
        sys.stderr.write(texts.CLI_MAIL_TEST_USAGE + "\n")
        return 2
    address = argv[0].strip()
    if not mail.valid_address(address):
        sys.stderr.write(texts.CLI_MAIL_TEST_BAD_ADDRESS.format(argv[0])
                         + "\n")
        return 2
    return run(from_env(), address)
