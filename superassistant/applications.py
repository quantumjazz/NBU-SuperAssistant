"""A student's application: what is asked, what is refused, where it stands.

The entry rules (NOW.md requirement 2) live here, so the student's form and a
staff correction obey the same ones:

- every entry is kept as typed, without spaces at either end;
- F№ is typed as digits after a fixed „F“ and stored as „F“ and the digits,
  so every document prints it as before; staff may also type the letter, „F“
  or „f“ (the owner, 13 October 2026: "hardcode “F” so students enter only
  the numbers"). Anything else is refused. A value stored before the rule is
  kept as it is, for staff to correct;
- a character a Word file cannot hold is refused: a control character, other
  than a line break in the proposal's sections (Word files are XML 1.0);
- in the student's names, the topic and a typed supervisor's name, a word
  that mixes Latin and Cyrillic letters is refused, a word being an unbroken
  run of letters, so „CRM-система“ passes (adopted from docs/domain.md).

Refusals name the characters, so the student can find and retype them.

The student's declaration that the credits are covered is a tick, not an
entry: supervision.submit refuses a submission without it. So is the tick
that the student knows the schedule of sessions; the session itself is a
choice among those the schedule offers that day (sessions.offered), checked
when the draft is saved and again at submission.

Staff may remove a submitted application to the bin, saying why, and from
there put it back or delete it (constitution 5.15): "Users remove the entry
(select reason - graduation, else), it goes to a 'bin' and deletion is
confirmed as a second step" (the owner, 15 October 2026). While it is in the
bin nothing changes it: every write that would (a check, a correction, a
supervisor's answer, a reminder, the student's own changes) finds it gone
inside its own transaction (require_active). Deleting it removes its row and
every row recorded with it; a row in `bin_events` keeps who did what, when
and why, by the application's number only. That number is never given to a
later application, so the log's number names one application only.
"""

import unicodedata

from superassistant import db, sessions

ONE_LINE_FIELDS = ("name1", "name2", "name3", "fn", "phone", "topic",
                   "average_grade", "sup_name", "sup_email")
MULTI_LINE_FIELDS = db.PROPOSAL_FIELDS
SCRIPT_CHECKED_FIELDS = ("name1", "name2", "name3", "topic", "sup_name")
CHOICE_FIELDS = ("programme", "professor", "sup_title")
GRAD_TYPES = ("thesis", "exam")

# What every student gives, and what a thesis adds (NOW.md requirement 2).
REQUIRED_ALL = ("name1", "name2", "name3", "fn")
REQUIRED_THESIS = ("phone", "programme", "topic", "average_grade") \
    + MULTI_LINE_FIELDS


# F№: the letter every stored F№ begins with, and the digits after it.
FN_LETTER = "F"
FN_DIGITS = "0123456789"


class Refusal(object):
    """Why one entry was refused: the field, a reason code, the characters."""

    def __init__(self, field, reason, characters=""):
        self.field = field
        self.reason = reason            # 'control', 'mixed', 'fn', 'tick', ...
        self.characters = characters

    def __repr__(self):
        return "Refusal({!r}, {!r}, {!r})".format(self.field, self.reason,
                                                  self.characters)


# --- The entry rules -------------------------------------------------------

def _not_holdable(ch, multi_line):
    """Whether a Word file cannot hold this character, or the rule refuses it."""
    if ch == "\n" and multi_line:
        return False
    category = unicodedata.category(ch)
    if category in ("Cc", "Cs"):
        return True
    return ch in ("￾", "￿")


def _script(ch):
    name = unicodedata.name(ch, "")
    if name.startswith("LATIN"):
        return "latin"
    if name.startswith("CYRILLIC"):
        return "cyrillic"
    return None


def words(text):
    """The unbroken runs of letters in text (combining marks stay inside)."""
    runs, current = [], []
    for ch in text:
        category = unicodedata.category(ch)
        if category.startswith("L") or (current and category.startswith("M")):
            current.append(ch)
        elif current:
            runs.append("".join(current))
            current = []
    if current:
        runs.append("".join(current))
    return runs


def mixed_letters(text):
    """The letters that make a word mixed, in order of appearance, or "".

    In each word holding both Latin and Cyrillic letters, the letters of the
    script the word has fewer of are the ones shown; Latin on a tie.
    """
    found = []
    for word in words(text):
        latin = [ch for ch in word if _script(ch) == "latin"]
        cyrillic = [ch for ch in word if _script(ch) == "cyrillic"]
        if latin and cyrillic:
            odd = cyrillic if len(cyrillic) < len(latin) else latin
            for ch in odd:
                if ch not in found:
                    found.append(ch)
    return "".join(found)


def _line_breaks(field, value):
    value = value if isinstance(value, str) else ""
    if field in MULTI_LINE_FIELDS:
        value = value.replace("\r\n", "\n").replace("\r", "\n")
    return value


def normalise(field, value):
    """The value as it will be stored: line breaks as \\n, ends trimmed.
    F№ follows its own rule (faculty_number)."""
    return _line_breaks(field, value).strip()


def faculty_number(typed, letter=False):
    """F№ as stored, from what was typed: „F“ and the digits; "" for an empty
    entry; None when refused.

    The student types the digits only; staff (letter=True) may type „F“ or
    „f“ before them. Only the digits 0 to 9 count as digits. Spaces at either
    end are trimmed, as in every entry, but a control character is looked
    for before trimming, so trimming never makes one pass (check_entry).
    """
    typed = typed if isinstance(typed, str) else ""
    if forbidden_characters(typed):
        return None
    value = typed.strip()
    if not value:
        return ""
    if letter and value[0] in (FN_LETTER, FN_LETTER.lower()):
        value = value[1:]
    if value and all(ch in FN_DIGITS for ch in value):
        return FN_LETTER + value
    return None


def fn_digits(stored):
    """What the student's F№ field shows of a stored F№: the digits after
    „F“, or a value stored before the rule as it is, to be retyped."""
    stored = stored or ""
    rest = stored[len(FN_LETTER):]
    if stored.startswith(FN_LETTER) and rest and all(ch in FN_DIGITS
                                                     for ch in rest):
        return rest
    return stored


def forbidden_characters(text, multi_line=False):
    """The characters a Word file cannot hold, in order, each once."""
    bad = []
    for ch in text:
        if _not_holdable(ch, multi_line) and ch not in bad:
            bad.append(ch)
    return "".join(bad)


def check_entry(field, value):
    """The refusal for one entry, or None.

    Control characters are looked for in the value as typed, before the ends
    are trimmed: trimming must never be what makes a refused character pass.
    """
    value = _line_breaks(field, value)
    bad = forbidden_characters(value, field in MULTI_LINE_FIELDS)
    if bad:
        return Refusal(field, "control", bad)
    if field in SCRIPT_CHECKED_FIELDS:
        mixed = mixed_letters(normalise(field, value))
        if mixed:
            return Refusal(field, "mixed", mixed)
    return None


def clean(form, fields, lists=None, fn_letter=False):
    """Normalise and check the given fields of a submitted form.

    Returns (values, refusals): the values to store, and one Refusal per field
    that breaks a rule. Choice fields must name an entry of the owner's lists,
    and a session one the schedule offers today. F№ follows faculty_number;
    fn_letter=True is staff's correction.
    """
    values, refusals = {}, []
    for field in fields:
        raw = form.get(field, "")
        if field == "fn":
            value = faculty_number(raw, fn_letter)
            if value is None:
                refusals.append(Refusal(field, "fn"))
            else:
                values[field] = value
            continue
        refusal = check_entry(field, raw)
        value = normalise(field, raw)
        if refusal is None and lists is not None and value:
            if field == "programme" and value not in lists.programmes:
                refusal = Refusal(field, "choice")
            elif field == "professor" and value not in lists.professors:
                refusal = Refusal(field, "choice")
            elif field == "sup_title" and value not in lists.titles:
                refusal = Refusal(field, "choice")
            elif (field == "grad_session"
                  and value not in sessions.offered(lists)):
                refusal = Refusal(field, "session")
        if refusal is not None:
            refusals.append(refusal)
        else:
            values[field] = value
    return values, refusals


def missing_for_submission(record):
    """The fields a submission still lacks, as Refusals ('required')."""
    missing = [f for f in REQUIRED_ALL if not record[f]]
    if record["grad_type"] not in GRAD_TYPES:
        missing.append("grad_type")
    refusals = [Refusal(field, "required") for field in missing]
    if record["grad_type"] == "thesis":
        refusals.extend(Refusal(f, "required") for f in REQUIRED_THESIS
                        if not record[f])
        refusals.extend(supervisor_refusals(record))
    return refusals


def supervisor_refusals(record):
    """supervisor_missing as Refusals: an empty field is 'required'; an
    address typed but not an address is 'address', wrong rather than missing."""
    return [Refusal(field, "address" if field == "sup_email"
                    and record["sup_email"] else "required")
            for field in supervisor_missing(record)]


def supervisor_missing(record):
    """What the chosen supervisor lacks: a listed professor, or a typed one
    with a name, a title from the list and a valid email address."""
    from superassistant import mail
    if record["professor"]:
        return []
    out = []
    if not record["sup_name"]:
        out.append("sup_name")
    if not record["sup_title"]:
        out.append("sup_title")
    if not mail.valid_address(record["sup_email"]):
        out.append("sup_email")
    if out == ["sup_name", "sup_title", "sup_email"]:
        return ["professor"]
    return out


# --- Reading ---------------------------------------------------------------

def by_email_key(connection, key):
    return connection.execute("SELECT * FROM applications WHERE email_key = ?",
                              (key,)).fetchone()


def get(connection, application_id):
    return connection.execute("SELECT * FROM applications WHERE id = ?",
                              (application_id,)).fetchone()


def get_or_create(connection, key, email):
    """The student's one application; made on the first visit.

    A deleted application's number is never given again: SQLite would give
    the number of a deleted last row to the next one."""
    with db.transaction(connection):
        row = by_email_key(connection, key)
        if row is None:
            stamp = db.now()
            number = 1 + connection.execute(
                "SELECT MAX(COALESCE((SELECT MAX(id) FROM applications), 0), "
                "COALESCE((SELECT MAX(application_id) FROM bin_events), 0))"
            ).fetchone()[0]
            connection.execute(
                "INSERT INTO applications (id, email, email_key, created_at, "
                "updated_at) VALUES (?, ?, ?, ?, ?)",
                (number, email, key, stamp, stamp))
    return by_email_key(connection, key)


def current_request(connection, application_id):
    """The request still standing: the latest one not replaced, or None."""
    return connection.execute(
        "SELECT * FROM requests WHERE application_id = ? AND replaced_at IS "
        "NULL ORDER BY id DESC LIMIT 1", (application_id,)).fetchone()


def requests_of(connection, application_id):
    return connection.execute(
        "SELECT * FROM requests WHERE application_id = ? ORDER BY id",
        (application_id,)).fetchall()


def latest_check(connection, application_id):
    return connection.execute(
        "SELECT * FROM checks WHERE application_id = ? ORDER BY id DESC "
        "LIMIT 1", (application_id,)).fetchone()


def checks_of(connection, application_id):
    return connection.execute(
        "SELECT checks.*, accounts.username FROM checks JOIN accounts ON "
        "accounts.id = checks.by_account WHERE application_id = ? "
        "ORDER BY checks.id", (application_id,)).fetchall()


def corrections_of(connection, application_id):
    return connection.execute(
        "SELECT corrections.*, accounts.username FROM corrections JOIN "
        "accounts ON accounts.id = corrections.by_account WHERE "
        "application_id = ? ORDER BY corrections.id",
        (application_id,)).fetchall()


def in_a_report(connection, application_id):
    """Whether a kept report lists the application. A report in the bin
    does not count: its students wait for a report again at once (the
    owner, 15 October 2026: "Yes, right away"; constitution 5.14)."""
    return connection.execute(
        "SELECT 1 FROM report_students s JOIN reports r ON r.id = "
        "s.report_id WHERE s.application_id = ? AND r.binned_at IS NULL "
        "LIMIT 1", (application_id,)).fetchone() is not None


class Standing(object):
    """Where an application stands, as the student and staff see it.

    The supervisor's answer and the staff check are independent: either may
    come first (NOW.md requirement 2, "the latest check counts").
    """

    def __init__(self, record, request, check, reported):
        self.submitted = record["submitted_at"] is not None
        self.thesis = record["grad_type"] == "thesis"
        if not self.thesis or not self.submitted or request is None:
            self.answer = None
        else:
            self.answer = request["answer"] or "awaited"
        self.check = check["result"] if check is not None else None
        self.reported = reported

    @property
    def waiting_for_supervisor(self):
        return self.answer == "awaited"

    @property
    def waiting_for_check(self):
        return self.submitted and self.check is None

    @property
    def waiting_for_report(self):
        return (self.thesis and self.answer == "confirm"
                and self.check == "passed" and not self.reported)

    @property
    def waiting(self):
        return (self.waiting_for_supervisor or self.waiting_for_check
                or self.waiting_for_report)


def standing(connection, record):
    return Standing(record, current_request(connection, record["id"]),
                    latest_check(connection, record["id"]),
                    in_a_report(connection, record["id"]))


def full_name(record):
    return " ".join(part for part in (record["name1"], record["name2"],
                                      record["name3"]) if part)


def supervisor_label(record, lists):
    """The supervisor as written everywhere: title and name."""
    if record["professor"]:
        if record["professor"] in lists.professors:
            return lists.professor_label(record["professor"])
        return record["professor"]
    return " ".join(part for part in (record["sup_title"], record["sup_name"])
                    if part)


def supervisor_email(record, lists):
    if record["professor"]:
        return lists.professors[record["professor"]]["email"]
    return record["sup_email"]


# --- Writing ---------------------------------------------------------------

def save_draft(connection, record, values):
    """Store the student's entries before submission."""
    if record["submitted_at"] is not None:
        raise ValueError("submitted")
    if not values:
        return
    columns = ", ".join(name + " = ?" for name in values)
    with db.transaction(connection):
        connection.execute(
            "UPDATE applications SET " + columns + ", updated_at = ? "
            "WHERE id = ? AND submitted_at IS NULL",
            list(values.values()) + [db.now(), record["id"]])


def record_check(connection, application_id, result, note, account_id):
    """Raises Removed when the application is in the bin or deleted."""
    if result not in ("passed", "not_passed"):
        raise ValueError(result)
    with db.transaction(connection):
        require_active(connection, application_id)
        connection.execute(
            "INSERT INTO checks (application_id, result, note, by_account, "
            "at) VALUES (?, ?, ?, ?, ?)",
            (application_id, result, note, account_id, db.now()))


def correct(connection, record, values, account_id):
    """A staff correction: each changed field keeps the value it replaces.

    Returns the fields that changed. Runs inside the caller's transaction.
    """
    changed = []
    for field, value in values.items():
        old = record[field] or ""
        if value == old:
            continue
        connection.execute(
            "INSERT INTO corrections (application_id, field, old_value, "
            "new_value, by_account, at) VALUES (?, ?, ?, ?, ?, ?)",
            (record["id"], field, old, value, account_id, db.now()))
        connection.execute(
            "UPDATE applications SET " + field + " = ?, updated_at = ? "
            "WHERE id = ?", (value, db.now(), record["id"]))
        changed.append(field)
    return changed


# --- The bin (constitution 5.15) -------------------------------------------

BIN_REASONS = ("graduated", "other")


class Removed(PermissionError):
    """The application is in the bin or deleted: nothing may change it."""


def is_binned(record):
    return record is not None and record["binned_at"] is not None


def require_active(connection, application_id):
    """The application, read inside the caller's transaction, or Removed
    when it is in the bin or no longer exists. Every write that changes an
    application calls it under its own write lock, so a removal or a
    deletion committed a moment earlier is always seen."""
    record = get(connection, application_id)
    if record is None or is_binned(record):
        raise Removed(application_id)
    return record


def _bin_event(connection, application_id, event, reason, account_id,
               note=""):
    connection.execute(
        "INSERT INTO bin_events (application_id, event, reason, note, "
        "by_account, at) VALUES (?, ?, ?, ?, ?, ?)",
        (application_id, event, reason, note, account_id, db.now()))


def remove(connection, application_id, reason, note, account_id):
    """Move a submitted application to the bin, saying why. The note is
    kept with the removal's log row as well, so putting the application back
    keeps it.

    Returns False, changing nothing, when there is no such submitted
    application or it is already in the bin; raises ValueError for a reason
    that is not one of BIN_REASONS."""
    if reason not in BIN_REASONS:
        raise ValueError(reason)
    with db.transaction(connection):
        record = get(connection, application_id)
        if (record is None or record["submitted_at"] is None
                or is_binned(record)):
            return False
        note = (note or "").strip()
        connection.execute(
            "UPDATE applications SET binned_at = ?, binned_by = ?, "
            "bin_reason = ?, bin_note = ? WHERE id = ?",
            (db.now(), account_id, reason, note, application_id))
        _bin_event(connection, application_id, "removed", reason, account_id,
                   note)
    return True


def restore(connection, application_id, account_id):
    """Put an application back from the bin, as it was. Returns False when
    it is not in the bin."""
    with db.transaction(connection):
        record = get(connection, application_id)
        if not is_binned(record):
            return False
        _bin_event(connection, application_id, "restored",
                   record["bin_reason"], account_id)
        connection.execute(
            "UPDATE applications SET binned_at = NULL, binned_by = NULL, "
            "bin_reason = NULL, bin_note = '' WHERE id = ?",
            (application_id,))
    return True


# Every table holding rows recorded with an application, deleted before it.
RECORDED_WITH = ("corrections", "checks", "requests", "report_students")


def delete(connection, application_id, account_id):
    """Delete an application in the bin, with every row recorded with it.

    One transaction: the log row, then the supervisors' answers (requests),
    the checks, the corrections and its rows in every report, kept or in
    the bin, and the application itself; the notes of its removals in the
    log are blanked.
    The student's sign-in records for that address lose the address and
    are spent, rather than deleted, so their numbers are never given again:
    a browser still holding one, unfinished, cannot reach another student's
    sign-in. A report's Word file is not touched. Returns False when
    the application is not in the bin, so only the second step deletes."""
    with db.transaction(connection):
        record = get(connection, application_id)
        if not is_binned(record):
            return False
        _bin_event(connection, application_id, "deleted",
                   record["bin_reason"], account_id)
        for table in RECORDED_WITH:
            connection.execute("DELETE FROM " + table
                               + " WHERE application_id = ?",
                               (application_id,))
        connection.execute(
            "UPDATE signins SET email = '', email_key = '', used_at = "
            "COALESCE(used_at, ?), code_hash = NULL, link_hash = NULL WHERE "
            "email_key = ?", (db.now(), record["email_key"]))
        connection.execute("UPDATE bin_events SET note = '' WHERE "
                           "application_id = ?", (application_id,))
        connection.execute("DELETE FROM applications WHERE id = ?",
                           (application_id,))
    return True


def binned(connection):
    """Every application in the bin, the latest removed first, with the
    username of who removed it."""
    return connection.execute(
        "SELECT applications.*, accounts.username FROM applications JOIN "
        "accounts ON accounts.id = applications.binned_by WHERE "
        "applications.binned_at IS NOT NULL ORDER BY applications.binned_at "
        "DESC, applications.id DESC").fetchall()


def deletions(connection):
    """Every deletion, newest first: the application's number, the reason,
    who removed it and when, who deleted it and when. No student data."""
    return connection.execute(
        "SELECT d.application_id, d.reason, d.at AS deleted_at, "
        "da.username AS deleted_by, r.at AS removed_at, "
        "ra.username AS removed_by FROM bin_events d "
        "JOIN accounts da ON da.id = d.by_account "
        "LEFT JOIN bin_events r ON r.id = (SELECT MAX(id) FROM bin_events "
        "WHERE application_id = d.application_id AND event = 'removed' "
        "AND id < d.id) "
        "LEFT JOIN accounts ra ON ra.id = r.by_account "
        "WHERE d.event = 'deleted' ORDER BY d.id DESC").fetchall()
