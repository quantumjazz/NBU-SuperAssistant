"""The topic-approval report (NOW.md requirement 7): which applications it
lists, and the reports kept.

An application belongs in a programme's report when it is a submitted thesis
application of that programme, the answer to its current request (the latest
one not replaced) is a confirmation, and its latest check (the highest id)
passed. Students are listed in alphabetical order of their names as printed,
then by F№.

Each report is kept: its .docx in the data directory's reports folder, and a
row in `reports` with one row per student in `report_students`, so a report
can be read again with the students it listed when it was made. A later
report never removes or overwrites an earlier one. DEFERRED (NOW.md): leaving
students already reported out of a later report; until then a later report
lists them again.
"""

import secrets

from superassistant import db, documents

QUALIFYING = """
    SELECT a.* FROM applications a
    WHERE a.grad_type = 'thesis'
      AND a.submitted_at IS NOT NULL
      AND (SELECT r.answer FROM requests r
           WHERE r.application_id = a.id AND r.replaced_at IS NULL
           ORDER BY r.id DESC LIMIT 1) = 'confirm'
      AND (SELECT c.result FROM checks c
           WHERE c.application_id = a.id
           ORDER BY c.id DESC LIMIT 1) = 'passed'
"""


class NothingToReport(Exception):
    """No application of the programme belongs in a report: none is made."""


def _order(application):
    return (documents.student_name(application).casefold(),
            application["fn"].casefold(), application["id"])


def qualifying(connection, programme):
    """The applications a report for this programme lists, in its order."""
    rows = connection.execute(QUALIFYING + " AND a.programme = ?",
                              (programme,)).fetchall()
    return sorted(rows, key=_order)


def counts(connection):
    """{programme code: how many applications a report would list}."""
    return {row["programme"]: row["n"] for row in connection.execute(
        "SELECT q.programme, COUNT(*) AS n FROM (" + QUALIFYING + ") q "
        "GROUP BY q.programme")}


def generate(connection, settings, lists, programme, account_id):
    """Make, keep and return the id of a report for one programme.

    The .docx and the rows that record it are made in one transaction; if
    anything fails, neither is kept. Raises NothingToReport when no
    application qualifies, and KeyError for a programme the lists lack.
    """
    if programme not in lists.programmes:
        raise KeyError(programme)
    faculty = lists.programmes[programme]["faculty"]
    settings.reports_dir.mkdir(parents=True, exist_ok=True)
    written = None
    try:
        with db.transaction(connection):
            applications = qualifying(connection, programme)
            if not applications:
                raise NothingToReport(programme)
            generated_at = db.now()
            rows = [documents.report_row(position, application, lists)
                    for position, application in enumerate(applications,
                                                           start=1)]
            data = documents.doklad_temi(programme, rows, generated_at,
                                         lists)
            filename = "doklad-temi-{}-{}.docx".format(
                db.now_dt().strftime("%Y%m%d-%H%M%S"),
                secrets.token_hex(4))
            cursor = connection.execute(
                "INSERT INTO reports (programme, faculty, generated_at, "
                "generated_by, filename) VALUES (?,?,?,?,?)",
                (programme, faculty, generated_at, account_id, filename))
            report_id = cursor.lastrowid
            connection.executemany(
                "INSERT INTO report_students (report_id, position, "
                "application_id, fn, name, topic, supervisor) "
                "VALUES (?,?,?,?,?,?,?)",
                [(report_id, row["position"], row["application_id"],
                  row["fn"], row["name"], row["topic"], row["supervisor"])
                 for row in rows])
            # "xb": a file of that name is never overwritten.
            path = settings.reports_dir / filename
            with open(str(path), "xb") as handle:
                written = path
                handle.write(data)
    except BaseException:
        if written is not None:
            try:
                written.unlink()
            except OSError:
                pass
        raise
    return report_id


def kept(connection):
    """Every kept report, newest first, with how many students it lists."""
    return connection.execute(
        "SELECT r.*, COUNT(s.position) AS students FROM reports r "
        "LEFT JOIN report_students s ON s.report_id = r.id "
        "GROUP BY r.id ORDER BY r.id DESC").fetchall()


def get(connection, report_id):
    return connection.execute("SELECT * FROM reports WHERE id = ?",
                              (report_id,)).fetchone()


def students(connection, report_id):
    """The students a kept report lists, in its order."""
    return connection.execute(
        "SELECT * FROM report_students WHERE report_id = ? "
        "ORDER BY position", (report_id,)).fetchall()


def path(settings, report):
    return settings.reports_dir / report["filename"]
