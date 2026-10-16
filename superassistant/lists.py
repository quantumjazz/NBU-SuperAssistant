"""The owner's lists: academic titles, faculties, programmes, professors and
the schedule of sessions.

Five CSV files in the data directory's `lists` folder, UTF-8, one entry per
line, with a header row in Bulgarian. The owner edits them in any text editor
or spreadsheet. They start from the values docs/domain.md records (NOW.md,
requirement 6); the professors list starts empty, for the owner to fill.

The sessions list holds per graduation session a code, its date and the
three deadlines of the department's framework schedule, dates written
YYYY-MM-DD (constitution 5.13). It starts from the four sessions of the
2026/2027 schedule and is written once, at the first start that knows it
(web.prepare), so the pilot's first start after the update of 16 October
2026 writes it beside the four lists it already has.

A list that cannot be read, or that no longer holds an entry an application
uses, stops the service from starting, naming the file and the line: a wrong
list must never reach an email or a document.

A programme is listed once per form of study, by name, with one code, which
only staff see (constitution 2.6 and 5.3). The codes of the first starting
list were replaced on 13 October 2026; rename_programmes moves the records
that still hold one to its new code, once (web.prepare).
"""

import csv
import io
import os
import re
from datetime import date

TITLES = "titles.csv"
FACULTIES = "faculties.csv"
PROGRAMMES = "programmes.csv"
PROFESSORS = "professors.csv"
SESSIONS = "sessions.csv"

HEADERS = {
    TITLES: ["звание"],
    FACULTIES: ["код", "факултет", "звание на декана", "декан"],
    PROGRAMMES: ["код", "степен", "програма", "форма", "факултет"],
    PROFESSORS: ["код", "звание", "име", "email"],
    SESSIONS: ["код", "дата на сесията",
               "заявления за одобряване на теми до",
               "заявления за държавен изпит до",
               "предаване на одобрени тези до"],
}

# A session's dates, in the order of its row after the code.
SESSION_DATES = ("date", "topics", "exam", "theses")
_ISO_DATE = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}")

DEGREES = ("БП", "МП")
FORMS = ("РО", "ДО")

# Starting values, from docs/domain.md (October 2026). The faculty of each
# programme follows the mapping the owner confirmed on 9 October 2026:
# ДО to ФДЕНО, РО bachelor's to БФ, РО master's to МФ. ФДЕНО's name is the
# abbreviation, as every report writes it: „ДЕКАН НА ФДЕНО“ (the owner, 12
# October 2026); БФ and МФ are written in full. The programmes are the
# owner's of 13 October 2026, one row per programme and form, each with its
# code in Locus: "Remove “Курсист - Бизнес администрация” and “Управление на
# здравеопазването” completely, each other program stays in the list only
# once with each form or study". Where Locus has two codes for one programme
# and form, the row takes the first (MSNHRB05, MSNSMQ11, MSNSMQ09).
STARTER = {
    TITLES: [["проф. д-р"], ["доц. д-р"], ["гл. ас. д-р"], ["ас. д-р"]],
    FACULTIES: [
        ["БФ", "Бакалавърски факултет", "доц. д-р", "Илия Кожухаров"],
        ["МФ", "Магистърски факултет", "проф. д-р", "Борис Сергинов"],
        ["ФДЕНО", "ФДЕНО", "доц. д-р", "Венцислав Джамбазов"],
    ],
    PROGRAMMES: [
        ["BSNADM01", "БП", "Администрация и управление", "РО", "БФ"],
        ["BSNADM04", "БП", "Публичен мениджмънт и регионално развитие",
         "РО", "БФ"],
        ["BSNBUB04", "БП", "Управление на бизнеса и предприемачество", "РО",
         "БФ"],
        ["BSNDIU01", "БП", "Управление на бизнеса и предприемачество", "ДО",
         "ФДЕНО"],
        ["BSNTUR01", "БП", "Туризъм", "РО", "БФ"],
        ["BSNDIT01", "БП", "Туризъм", "ДО", "ФДЕНО"],
        ["BSNDIT04", "БП", "Управление на туризма", "ДО", "ФДЕНО"],
        ["MSNADM21", "МП",
         "Артмениджмънт. Управление на културни институции и творчески "
         "индустрии", "РО", "МФ"],
        ["MSNALH03", "МП", "Управление на луксозното хотелиерство", "РО",
         "МФ"],
        ["MSNHRB05", "МП",
         "Управление и развитие на човешките ресурси (на български и "
         "английски език)", "РО", "МФ"],
        ["MSNHRE08", "МП",
         "Управление и развитие на човешките ресурси (на английски език)",
         "ДО", "ФДЕНО"],
        ["MSNMBA01", "МП", "Бизнес администрация", "РО", "МФ"],
        ["MSNMBA12", "МП", "Бизнес администрация", "ДО", "ФДЕНО"],
        ["MSNMBA81", "МП", "Мениджмънт на туристическия бизнес", "РО", "МФ"],
        ["MSNMBA80", "МП", "Мениджмънт на туристическия бизнес", "ДО",
         "ФДЕНО"],
        ["MSNSMQ11", "МП", "Мениджмънт за организационно съвършенство", "РО",
         "МФ"],
        ["MSNSMQ09", "МП", "Мениджмънт за организационно съвършенство", "ДО",
         "ФДЕНО"],
    ],
    PROFESSORS: [],
    # The department's „График на сесиите … 2026/2027“: each session's date,
    # then the deadlines for the applications to approve topics, for the
    # applications for the state exam, and for handing in approved theses.
    SESSIONS: [
        ["2026-04", "2026-04-21", "2025-11-14", "2026-02-06", "2026-02-06"],
        ["2026-07", "2026-07-07", "2026-02-06", "2026-04-30", "2026-04-30"],
        ["2026-09", "2026-09-26", "2026-04-30", "2026-07-17", "2026-07-17"],
        ["2027-01", "2027-01-26", "2026-09-11", "2026-11-13", "2026-11-13"],
    ],
}


# The codes of the first starting list, used by the pilot until 13 October
# 2026, and the code of the same programme and form in the owner's list.
RENAMED_PROGRAMMES = {
    "АУ-РО": "BSNADM01", "УБП-РО": "BSNBUB04", "УБП-ДО": "BSNDIU01",
    "АМ-РО": "MSNADM21", "МОС-РО": "MSNSMQ11", "МОС-ДО": "MSNSMQ09",
    "УРЧР-РО": "MSNHRB05", "БА-РО": "MSNMBA01",
}


class ListError(Exception):
    """A list the service cannot start with. Says which file and line."""

    def __init__(self, filename, line, message):
        self.filename = filename
        self.line = line
        where = ("{} line {}".format(filename, line) if line
                 else filename)
        Exception.__init__(self, where + ": " + message)


class Lists(object):
    """What the five files hold, read once and checked."""

    def __init__(self, titles, faculties, programmes, professors,
                 sessions=None):
        self.titles = titles            # [title]
        self.faculties = faculties      # {code: {name, dean_title, dean}}
        self.programmes = programmes    # {code: {degree, name, form, faculty}}
        self.professors = professors    # {code: {title, name, email}}
        # {code: {date, topics, exam, theses}}, each a date, by session date
        self.sessions = sessions if sessions is not None else {}

    def programme_faculty(self, code):
        """The faculty a programme's report goes to, or None."""
        programme = self.programmes.get(code)
        if programme is None:
            return None
        return self.faculties.get(programme["faculty"])

    def professor_label(self, code):
        """A listed professor as written in documents: title and name."""
        professor = self.professors[code]
        return professor["title"] + " " + professor["name"]


def write_starter(lists_dir, filenames=None):
    """Write any list that is missing, from the starting values: every list,
    or only those named."""
    lists_dir.mkdir(parents=True, exist_ok=True)
    for filename, rows in STARTER.items():
        if filenames is not None and filename not in filenames:
            continue
        path = lists_dir / filename
        if path.exists():
            continue
        buffer = io.StringIO()
        writer = csv.writer(buffer, lineterminator="\n")
        writer.writerow(HEADERS[filename])
        for row in rows:
            writer.writerow(row)
        # Whole or not at all: a start that fails half-way must not leave a
        # truncated list that every later start then refuses.
        partial = path.with_name(filename + ".tmp")
        partial.write_text(buffer.getvalue(), encoding="utf-8")
        os.replace(str(partial), str(path))


def _rows(lists_dir, filename):
    """(physical line number, cells) for each non-empty row after the header.

    The line is the file's own line where the row starts, so a quoted cell
    spanning lines does not shift the lines reported after it.
    """
    from superassistant.applications import forbidden_characters
    path = lists_dir / filename
    try:
        text = path.read_text(encoding="utf-8-sig")
    except FileNotFoundError:
        raise ListError(filename, 0, "the file is missing")
    except (OSError, UnicodeDecodeError) as exc:
        raise ListError(filename, 0, "the file cannot be read: " + str(exc))
    # A character no Word document can hold would silently vanish from every
    # document that prints the entry: refuse it, by line and code.
    for number, line in enumerate(text.split("\n"), start=1):
        bad = forbidden_characters(line[:-1] if line.endswith("\r") else line)
        if bad:
            raise ListError(filename, number, "the character " + ", ".join(
                "U+{:04X}".format(ord(ch)) for ch in bad)
                + " cannot be printed in a document")
    reader = csv.reader(io.StringIO(text))
    rows, previous = [], 0
    try:
        for row in reader:
            rows.append((previous + 1, row))
            previous = reader.line_num
    except csv.Error as exc:
        raise ListError(filename, previous + 1,
                        "the file cannot be read: " + str(exc))
    if not rows:
        raise ListError(filename, 1, "the header row is missing")
    header = [cell.strip() for cell in rows[0][1]]
    if header != HEADERS[filename]:
        raise ListError(filename, rows[0][0], "the header must be: "
                        + ",".join(HEADERS[filename]))
    out = []
    for number, row in rows[1:]:
        cells = [cell.strip() for cell in row]
        if not any(cells):
            continue
        if any("\n" in cell or "\r" in cell for cell in cells):
            raise ListError(filename, number, "a cell holds a line break")
        if len(cells) != len(HEADERS[filename]):
            raise ListError(filename, number, "expected {} columns, found {}"
                            .format(len(HEADERS[filename]), len(cells)))
        if not all(cells):
            raise ListError(filename, number, "a column is empty")
        out.append((number, cells))
    return out


def _unique(filename, number, code, seen):
    if code in seen:
        raise ListError(filename, number, "the code " + repr(code)
                        + " is used twice")
    seen.add(code)


def _iso_date(filename, number, value):
    """A date written YYYY-MM-DD, as a date; else ListError."""
    if _ISO_DATE.fullmatch(value):
        try:
            return date.fromisoformat(value)
        except ValueError:
            pass
    raise ListError(filename, number, "the date " + repr(value)
                    + " is not a date written YYYY-MM-DD")


def load(lists_dir):
    """Read and check the five lists. Raises ListError."""
    titles = []
    for number, (title,) in _rows(lists_dir, TITLES):
        if title in titles:
            raise ListError(TITLES, number, "the title " + repr(title)
                            + " is listed twice")
        titles.append(title)

    faculties = {}
    for number, (code, name, dean_title, dean) in _rows(lists_dir, FACULTIES):
        _unique(FACULTIES, number, code, set(faculties))
        if dean_title not in titles:
            raise ListError(FACULTIES, number, "the title " + repr(dean_title)
                            + " is not in " + TITLES)
        faculties[code] = {"name": name, "dean_title": dean_title,
                           "dean": dean}

    programmes = {}
    for number, (code, degree, name, form, faculty) in _rows(lists_dir,
                                                              PROGRAMMES):
        _unique(PROGRAMMES, number, code, set(programmes))
        if degree not in DEGREES:
            raise ListError(PROGRAMMES, number, "the degree must be БП or МП")
        if form not in FORMS:
            raise ListError(PROGRAMMES, number, "the form must be РО or ДО")
        if faculty not in faculties:
            raise ListError(PROGRAMMES, number, "the faculty " + repr(faculty)
                            + " is not in " + FACULTIES)
        programmes[code] = {"degree": degree, "name": name, "form": form,
                            "faculty": faculty}

    professors = {}
    for number, (code, title, name, email) in _rows(lists_dir, PROFESSORS):
        _unique(PROFESSORS, number, code, set(professors))
        if title not in titles:
            raise ListError(PROFESSORS, number, "the title " + repr(title)
                            + " is not in " + TITLES)
        if "@" not in email:
            raise ListError(PROFESSORS, number, "the email address "
                            + repr(email) + " is not an address")
        professors[code] = {"title": title, "name": name, "email": email}

    sessions, dates = [], set()
    for number, row in _rows(lists_dir, SESSIONS):
        code = row[0]
        _unique(SESSIONS, number, code, set(c for c, _ in sessions))
        entry = dict(zip(SESSION_DATES, (_iso_date(SESSIONS, number, value)
                                         for value in row[1:])))
        if entry["date"] in dates:
            raise ListError(SESSIONS, number, "the date " + row[1]
                            + " is listed twice")
        dates.add(entry["date"])
        if any(entry[key] > entry["date"] for key in SESSION_DATES[1:]):
            raise ListError(SESSIONS, number, "a deadline is after the "
                            "session's date " + row[1])
        sessions.append((code, entry))
    sessions.sort(key=lambda item: item[1]["date"])

    return Lists(titles, faculties, programmes, professors,
                 dict(sessions))


def check_used(lists, connection):
    """Raise ListError if an application uses an entry the lists lack."""
    queries = [
        (PROGRAMMES, "programme", lists.programmes,
         "SELECT id, programme AS value FROM applications "
         "WHERE programme != ''"),
        (PROFESSORS, "professor", lists.professors,
         "SELECT id, professor AS value FROM applications "
         "WHERE professor != ''"),
        (TITLES, "title", set(lists.titles),
         "SELECT id, sup_title AS value FROM applications "
         "WHERE sup_title != ''"),
        (SESSIONS, "session", lists.sessions,
         "SELECT id, grad_session AS value FROM applications "
         "WHERE grad_session != ''"),
    ]
    for filename, what, entries, sql in queries:
        missing = {}
        for row in connection.execute(sql):
            if row["value"] not in entries:
                missing.setdefault(row["value"], []).append(row["id"])
        if missing:
            value = sorted(missing)[0]
            raise ListError(filename, 0, "the {} {!r} is used by applications "
                            "{} but is no longer listed".format(
                                what, value, ", ".join(
                                    str(i) for i in missing[value])))


def rename_programmes(connection, account_id):
    """Move every application holding an old starter code to its new code.

    Drafts included, since check_used reads every application. Each move is a
    correction under account_id (the owner's), keeping the old code; every
    report's programme, kept or in the bin, is moved too, since nothing else
    records it. Runs
    inside the caller's transaction. Returns how many applications moved.
    """
    from superassistant import applications
    moved = 0
    for old, new in sorted(RENAMED_PROGRAMMES.items()):
        for record in connection.execute(
                "SELECT * FROM applications WHERE programme = ? ORDER BY id",
                (old,)).fetchall():
            moved += len(applications.correct(connection, record,
                                              {"programme": new}, account_id))
        connection.execute("UPDATE reports SET programme = ? WHERE "
                           "programme = ?", (new, old))
    return moved
