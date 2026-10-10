"""`python -m superassistant remind`: remind supervisors who have not answered.

On the host a systemd timer runs it every day at 09:00, Sofia time; it can
also be run by hand. The rule is in supervision.due: three calendar days in
Sofia after the request and three after that reminder, at most twice, as the
settings SUPERASSISTANT_REMINDER_DAYS and SUPERASSISTANT_REMINDER_COUNT say,
so a request mailed on Monday afternoon is reminded on Thursday and Sunday
mornings. Running it again on the same day sends nothing more.
"""

import sys

from superassistant import db, supervision, texts
from superassistant.settings import from_env
from superassistant.web import StartupError, prepare


def run(settings, out=None):
    """Send the reminders due. Returns the exit status: 0, or 1 on a failure."""
    out = out or sys.stdout
    loaded = prepare(settings)
    connection = db.connect(settings.db_path)
    try:
        sent, failed = supervision.remind(connection, settings, loaded)
    finally:
        connection.close()
    out.write(texts.CLI_REMINDERS_SENT.format(len(sent)) + "\n")
    for request, reason in failed:
        out.write(texts.CLI_REMINDER_FAILED.format(
            request["sup_email"], request["application_id"], reason) + "\n")
    return 1 if failed else 0


def main(argv):
    try:
        return run(from_env())
    except StartupError as exc:
        sys.stderr.write("NBU-SuperAssistant cannot start: " + str(exc) + "\n")
        return 1
