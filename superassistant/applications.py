"""A student's application: what is asked, what is refused, where it stands.

The entry rules (NOW.md requirement 2) live here, so the student's form and a
staff correction obey the same ones:

- every entry is kept as typed, without spaces at either end, F№ in capitals;
- a character a Word file cannot hold is refused: a control character, other
  than a line break in the proposal's sections (Word files are XML 1.0);
- in the student's names, the topic and a typed supervisor's name, a word
  that mixes Latin and Cyrillic letters is refused, a word being an unbroken
  run of letters, so „CRM-система“ passes (adopted from docs/domain.md).

Refusals name the characters, so the student can find and retype them.
"""

import unicodedata

from superassistant import db

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


class Refusal(object):
    """Why one entry was refused: the field, a reason code, the characters."""

    def __init__(self, field, reason, characters=""):
        self.field = field
        self.reason = reason            # 'control', 'mixed', 'required', ...
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
    """The value as it will be stored: line breaks as \\n, ends trimmed."""
    value = _line_breaks(field, value).strip()
    if field == "fn":
        value = value.upper()
    return value


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


def clean(form, fields, lists=None):
    """Normalise and check the given fields of a submitted form.

    Returns (values, refusals): the values to store, and one Refusal per field
    that breaks a rule. Choice fields must name an entry of the owner's lists.
    """
    values, refusals = {}, []
    for field in fields:
        raw = form.get(field, "")
        refusal = check_entry(field, raw)
        value = normalise(field, raw)
        if refusal is None and lists is not None and value:
            if field == "programme" and value not in lists.programmes:
                refusal = Refusal(field, "choice")
            elif field == "professor" and value not in lists.professors:
                refusal = Refusal(field, "choice")
            elif field == "sup_title" and value not in lists.titles:
                refusal = Refusal(field, "choice")
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
    """The student's one application; made on the first visit."""
    with db.transaction(connection):
        row = by_email_key(connection, key)
        if row is None:
            stamp = db.now()
            connection.execute(
                "INSERT INTO applications (email, email_key, created_at, "
                "updated_at) VALUES (?, ?, ?, ?)", (email, key, stamp, stamp))
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
    return connection.execute(
        "SELECT 1 FROM report_students WHERE application_id = ? LIMIT 1",
        (application_id,)).fetchone() is not None


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
    if result not in ("passed", "not_passed"):
        raise ValueError(result)
    with db.transaction(connection):
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
