"""The topic-approval report (NOW.md requirement 7): which applications it
lists, and the reports kept.

An application belongs in a programme's report when it is a submitted thesis
application of that programme, the answer to its current request (the latest
one not replaced) is a confirmation, and its latest check (the highest id)
passed. Students are listed in alphabetical order of their names as printed,
then by F№.

Each report is kept until staff delete it: its .docx in the data directory's
reports folder, and a row in `reports` with one row per student in
`report_students`, so a report can be read again with the students it listed
when it was made. A later report never removes or overwrites an earlier one.
DEFERRED (NOW.md): leaving students already reported out of a later report;
until then a later report lists them again.

Staff may delete a report: "the report disappears", with its file and its
rows (the owner, 13 October 2026; constitution 5.14). The students it listed
then wait for a report again, and the next report of their programme lists
them. A row in `report_deletions` keeps who deleted which report and when.
A deleted report's number is never given to a later report, so the log's
number names one report only. A deletion happens whole or not at all: until
it has committed its file is only set aside, and goes back if it fails.
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
            # SQLite would give the number of a deleted last report again.
            report_id = 1 + connection.execute(
                "SELECT MAX(COALESCE((SELECT MAX(id) FROM reports), 0), "
                "COALESCE((SELECT MAX(report_id) FROM report_deletions), 0))"
            ).fetchone()[0]
            connection.execute(
                "INSERT INTO reports (id, programme, faculty, generated_at, "
                "generated_by, filename) VALUES (?,?,?,?,?,?)",
                (report_id, programme, faculty, generated_at, account_id,
                 filename))
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


def download_name(report_id, generated_at):
    """The report's name as staff download it, and as the pages name it."""
    return "doklad-temi-{}-{}.docx".format(report_id, generated_at[:10])


# A report's file while its deletion is not yet committed: set aside under
# this second name, so it can go back if the deletion fails (tidy).
ASIDE = ".deleting"


def _aside(file):
    return file.with_name(file.name + ASIDE)


def _put_back(file):
    """The file set aside, back under its own name, if it is aside."""
    try:
        _aside(file).replace(file)
    except FileNotFoundError:
        pass


def delete(connection, settings, report_id, account_id):
    """Delete a kept report: its rows and its file, logging who and when.

    All or nothing. One transaction writes the log row and removes the rows
    of `report_students` and then `reports`; before its COMMIT the file is
    set aside under a second name (ASIDE), which needs the same rights in
    the reports folder as removing it. If anything fails before the COMMIT
    has succeeded (the file cannot be moved, Codex T13-C2; a write fails;
    another connection still reading holds the COMMIT off past the busy
    timeout, T13-C1), the file is put back and then the transaction rolled
    back, so the report, its rows and its file stay, nothing is logged, and
    the deletion can be tried again. The file goes back while this
    connection still holds the write lock, so tidy, waiting for that lock,
    never finds it aside for a kept report. After the COMMIT the file set
    aside is removed; should that fail, or the process stop first, the next
    start removes it (tidy). A file already missing does not stop the
    deletion. Returns False when no such report is kept.

    The transaction is written out here rather than through db.transaction,
    because the file must go back before the ROLLBACK, a failed COMMIT
    included.
    """
    file = None
    connection.execute("BEGIN IMMEDIATE")
    try:
        report = get(connection, report_id)
        if report is None:
            connection.execute("ROLLBACK")
            return False
        count = connection.execute(
            "SELECT COUNT(*) FROM report_students WHERE report_id = ?",
            (report_id,)).fetchone()[0]
        connection.execute(
            "INSERT INTO report_deletions (report_id, programme, "
            "generated_at, students, filename, deleted_by, deleted_at) "
            "VALUES (?,?,?,?,?,?,?)",
            (report_id, report["programme"], report["generated_at"], count,
             report["filename"], account_id, db.now()))
        connection.execute("DELETE FROM report_students WHERE report_id = ?",
                           (report_id,))
        connection.execute("DELETE FROM reports WHERE id = ?", (report_id,))
        file = path(settings, report)
        try:
            file.replace(_aside(file))
        except FileNotFoundError:
            pass
        connection.execute("COMMIT")
    except BaseException:
        try:
            if file is not None:
                _put_back(file)
        finally:
            if connection.in_transaction:
                connection.execute("ROLLBACK")
        raise
    try:
        _aside(file).unlink()
    except OSError:
        pass            # the deletion stands; the next start removes it
    return True


def tidy(connection, settings):
    """Finish what a stopped process left half-done in the reports folder.

    A file set aside for a deletion that never committed goes back under its
    name, its report being still kept; one whose report is gone is removed.
    It holds the write lock while it looks, so a deletion running in another
    process is waited for and found finished either way. It writes no row,
    so it ends with ROLLBACK, which no other connection can hold off.
    Raises OSError when a file cannot be moved or removed.
    """
    if not settings.reports_dir.is_dir():
        return
    connection.execute("BEGIN IMMEDIATE")
    try:
        kept = set(row["filename"] for row in connection.execute(
            "SELECT filename FROM reports"))
        for aside in sorted(settings.reports_dir.glob("*" + ASIDE)):
            name = aside.name[:-len(ASIDE)]
            try:
                if name in kept:
                    aside.replace(aside.with_name(name))
                else:
                    aside.unlink()
            except FileNotFoundError:
                pass
    finally:
        connection.execute("ROLLBACK")


def deletions(connection):
    """Every deletion, newest first, with the username of who deleted."""
    return connection.execute(
        "SELECT d.*, a.username FROM report_deletions d JOIN accounts a ON "
        "a.id = d.deleted_by ORDER BY d.id DESC").fetchall()
