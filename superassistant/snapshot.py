"""`python -m superassistant snapshot`: the nightly copy of the applications.

On the host a systemd timer runs it every night at 00:00, Sofia time; it can
also be run by hand. It writes every submitted application, those in the bin
included and marked, as one CSV file in the records folder's `snapshots`,
emails that file to the owner's account address, and removes the copies 30
days old or older (constitution 6.7; the owner, 15 October 2026: "every day,
say 00.00 hours the app outputs a csv with all students entries data",
"Email it to you", "30 days"). A second run on the same day writes that
day's file again and sends it again.

The file is made for Excel on the owner's Mac, whose numbers use a decimal
comma. Excel there separates cells by semicolons, so the file does too, and
it reads Cyrillic only from a file that starts with the UTF-8 byte order
mark, so the file does. Excel also changes what it reads: it runs a cell
beginning with "=" as a formula, and turns what looks like a number, a date
or a time into one, so „0888123456“ loses its first zero, „5,50“ becomes 5,5
and „1e5“ 100000, however long the cell: 256 ones become 1,11E+255, and
8,200 zeros and „1e5“ 100000 (Codex T15-C3). Its text import, File > Open,
also splits a cell with line breaks into rows.

So every cell is written as an Excel formula that only joins text: ="…",
or ="…"&CHAR(10)&"…" for a line break, pieces of at most 255 UTF-16 units
(a quote, written twice, counting twice), as Excel's text values hold. Excel
shows it exactly as typed and never runs, converts or splits it, opened or
imported (checked in Excel on the owner's Mac, 15 October 2026). A cell too
long for Excel's formula of 8,192 units is written with an apostrophe before
it, which keeps it text, the apostrophe shown; its line breaks, if any, are
then written as they are, which opening the file keeps but the text import
splits.

What the file holds is what staff see of each application: its entries,
its session and whether the student ticked knowing the schedule, the
current supervisor's answer and comment, the latest check, whether a kept
report lists it, and whether it is in the bin and why. It is read in one
transaction, so it is the records of one moment. Never a sign-in code, an
answer link or a password.

The message goes through mail.send like every other, so in mode owner it
goes to SUPERASSISTANT_OWNER_EMAIL and in mode console it is printed. Like
mail-test it bypasses the rate limits: only someone on the host can run it.
The file is written before the message is sent and stays if the relay
refuses; the run then ends with status 1, so systemctl shows the unit as
failed until the next run.
"""

import csv
import fcntl
import io
import os
import re
import sys

from superassistant import (accounts, applications, db, mail, sessions,
                            supervision)
from superassistant import texts
from superassistant.settings import from_env
from superassistant.web import StartupError, prepare

KEEP_DAYS = 30
NAME = "zaiavlenia-{}.csv"
_NAME = re.compile(r"zaiavlenia-(\d{4})-(\d{2})-(\d{2})\.csv(\.tmp)?")
DELIMITER = ";"

# The longest text one of Excel's text values holds, and the longest
# formula, in UTF-16 units.
_EXCEL_TEXT_MAX = 255
_EXCEL_FORMULA_MAX = 8192
# A line break as a term of the formula.
_LINE_BREAKS = {"\n": "CHAR(10)", "\r": "CHAR(13)"}
LOCK = ".lock"


def _excel_length(value):
    return len(value.encode("utf-16-le")) // 2


def _literals(text):
    """text as Excel text values, "…", each holding at most _EXCEL_TEXT_MAX
    units as written, a quote counting twice; a character is never split."""
    pieces, current, size = [], [], 0
    for ch in text:
        width = _excel_length(ch) * (2 if ch == '"' else 1)
        if current and size + width > _EXCEL_TEXT_MAX:
            pieces.append("".join(current))
            current, size = [], 0
        current.append(ch)
        size += width
    pieces.append("".join(current))
    return ['"' + piece.replace('"', '""') + '"' for piece in pieces]


def _terms(value):
    """The formula's terms: text values and line breaks, in order."""
    terms, run = [], []
    for ch in value:
        if ch in _LINE_BREAKS:
            if run:
                terms.extend(_literals("".join(run)))
                run = []
            terms.append(_LINE_BREAKS[ch])
        else:
            run.append(ch)
    if run:
        terms.extend(_literals("".join(run)))
    return terms


def cell(value):
    """One value as the file writes it, so Excel shows it as typed."""
    value = "" if value is None else str(value)
    if not value:
        return value
    formula = "=" + "&".join(_terms(value))
    if _excel_length(formula) <= _EXCEL_FORMULA_MAX:
        return formula
    return "'" + value


def _supervisor_email(record, lists):
    if record["professor"]:
        professor = lists.professors.get(record["professor"])
        return professor["email"] if professor else ""
    return record["sup_email"]


def _row(connection, record, lists):
    standing = applications.standing(connection, record)
    request = applications.current_request(connection, record["id"])
    answered = standing.answer in supervision.CHOICES
    check = applications.latest_check(connection, record["id"])
    binned = applications.is_binned(record)
    return [
        record["id"],
        db.local_datetime(record["submitted_at"]),
        record["email"],
        texts.STAFF_TYPE.get(record["grad_type"], ""),
        record["name1"], record["name2"], record["name3"], record["fn"],
        texts.SNAPSHOT_YES_NO[record["credits_declared_at"] is not None],
        texts.SNAPSHOT_YES_NO[record["schedule_ack_at"] is not None],
        sessions.label(lists, record["grad_session"]),
        record["phone"],
        supervision.programme_label(record, lists),
        record["programme"],
        record["topic"],
        record["average_grade"],
        applications.supervisor_label(record, lists),
        _supervisor_email(record, lists),
    ] + [record[field] for field in db.PROPOSAL_FIELDS] + [
        texts.STAFF_ANSWER[standing.answer],
        db.local_datetime(request["answered_at"]) if answered else "",
        request["comment"] if answered else "",
        texts.STAFF_CHECK[standing.check],
        db.local_datetime(check["at"]) if check is not None else "",
        check["note"] if check is not None else "",
        texts.SNAPSHOT_YES_NO[standing.reported],
        texts.BIN_REASON.get(record["bin_reason"], record["bin_reason"])
        if binned else texts.SNAPSHOT_NOT_BINNED,
        db.local_datetime(record["binned_at"]),
        record["bin_note"],
    ]


def table(connection, lists):
    """The header and one row per submitted application, by number, all
    read in one transaction; and how many of them are in the bin."""
    connection.execute("BEGIN")
    try:
        records = connection.execute(
            "SELECT * FROM applications WHERE submitted_at IS NOT NULL "
            "ORDER BY id").fetchall()
        rows = [_row(connection, record, lists) for record in records]
    finally:
        connection.execute("ROLLBACK")
    binned = sum(1 for record in records if applications.is_binned(record))
    return [list(texts.SNAPSHOT_COLUMNS)] + rows, binned


def to_bytes(rows):
    """The rows as the file's bytes: UTF-8 with its mark, semicolons."""
    buffer = io.StringIO()
    writer = csv.writer(buffer, delimiter=DELIMITER)
    for row in rows:
        writer.writerow([cell(value) for value in row])
    return buffer.getvalue().encode("utf-8-sig")


def write(settings, data, day):
    """Write that day's file, readable by the host's user only. Returns its
    path. It appears under its name only once whole."""
    folder = settings.snapshots_dir
    folder.mkdir(mode=0o700, parents=True, exist_ok=True)
    path = folder / NAME.format(day.isoformat())
    partial = path.with_name(path.name + ".tmp")
    descriptor = os.open(str(partial), os.O_WRONLY | os.O_CREAT | os.O_TRUNC,
                         0o600)
    with os.fdopen(descriptor, "wb") as handle:
        handle.write(data)
    os.replace(str(partial), str(path))
    return path


def prune(settings, today):
    """Remove the copies KEEP_DAYS days old or older, and any file a
    stopped run left half-written. Returns the names removed. Nothing else
    in the folder is touched."""
    from datetime import date
    folder = settings.snapshots_dir
    if not folder.is_dir():
        return []
    removed = []
    for path in sorted(folder.iterdir()):
        match = _NAME.fullmatch(path.name)
        if match is None or not path.is_file():
            continue
        try:
            day = date(int(match.group(1)), int(match.group(2)),
                       int(match.group(3)))
        except ValueError:
            continue
        if match.group(4) or (today - day).days >= KEEP_DAYS:
            path.unlink()
            removed.append(path.name)
    return removed


def owner_address(connection, settings):
    """The owner's account address, or None without an owner."""
    if not settings.owner_username:
        return None
    account = accounts.by_username(connection, settings.owner_username)
    return account["email"] if account is not None else None


def run(settings, out=None, err=None):
    """Write, prune and send. Returns the exit status: 0, or 1 when the
    copy could not be sent."""
    out = out or sys.stdout
    err = err or sys.stderr
    loaded = prepare(settings)
    connection = db.connect(settings.db_path)
    try:
        rows, binned = table(connection, loaded)
        address = owner_address(connection, settings)
    finally:
        connection.close()
    moment = db.now()
    today = db.local_day(moment)
    data = to_bytes(rows)
    settings.snapshots_dir.mkdir(mode=0o700, parents=True, exist_ok=True)
    descriptor = os.open(str(settings.snapshots_dir / LOCK),
                         os.O_RDWR | os.O_CREAT, 0o600)
    try:
        fcntl.flock(descriptor, fcntl.LOCK_EX)
        path = write(settings, data, today)
        removed = prune(settings, today)
    finally:
        os.close(descriptor)        # closing releases the lock
    count = len(rows) - 1
    out.write(texts.CLI_SNAPSHOT_WRITTEN.format(
        path=path, count=count, size=len(data),
        word=texts.CLI_SNAPSHOT_WORD[0 if count == 1 else 1]) + "\n")
    if removed:
        out.write(texts.CLI_SNAPSHOT_PRUNED.format(", ".join(removed))
                  + "\n")
    if address is None:
        err.write(texts.CLI_SNAPSHOT_NO_OWNER + "\n")
        return 1
    message = mail.Message(
        address,
        texts.SNAPSHOT_SUBJECT.format(date=db.local_date(moment)),
        texts.SNAPSHOT_TEXT.format(name=path.name,
                                   moment=db.local_datetime(moment),
                                   count=len(rows) - 1, binned=binned,
                                   days=KEEP_DAYS),
        attachments=[mail.Attachment(path.name, data, "text", "csv")])
    try:
        mail.send(settings, message, out=out)
    except mail.MailFailed as exc:
        err.write(texts.CLI_SNAPSHOT_NOT_SENT.format(exc) + "\n")
        return 1
    if settings.effective_mail_mode() == "console":
        out.write(texts.CLI_SNAPSHOT_PRINTED + "\n")
    else:
        out.write(texts.CLI_SNAPSHOT_SENT.format(
            settings.owner_email if settings.effective_mail_mode() == "owner"
            else address) + "\n")
    return 0


def main(argv):
    try:
        return run(from_env())
    except StartupError as exc:
        sys.stderr.write("NBU-SuperAssistant cannot start: " + str(exc) + "\n")
        return 1
