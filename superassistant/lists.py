"""The owner's lists: academic titles, faculties, programmes and professors.

Four CSV files in the data directory's `lists` folder, UTF-8, one entry per
line, with a header row in Bulgarian. The owner edits them in any text editor
or spreadsheet. They start from the values docs/domain.md records (NOW.md,
requirement 6); the professors list starts empty, for the owner to fill.

A list that cannot be read, or that no longer holds an entry an application
uses, stops the service from starting, naming the file and the line: a wrong
list must never reach an email or a document.
"""

import csv
import io
import os

TITLES = "titles.csv"
FACULTIES = "faculties.csv"
PROGRAMMES = "programmes.csv"
PROFESSORS = "professors.csv"

HEADERS = {
    TITLES: ["звание"],
    FACULTIES: ["код", "факултет", "звание на декана", "декан"],
    PROGRAMMES: ["код", "степен", "програма", "форма", "факултет"],
    PROFESSORS: ["код", "звание", "име", "email"],
}

DEGREES = ("БП", "МП")
FORMS = ("РО", "ДО")

# Starting values, from docs/domain.md (October 2026). The faculty of each
# programme follows the mapping the owner confirmed on 9 October 2026:
# ДО to ФДЕНО, РО bachelor's to БФ, РО master's to МФ.
STARTER = {
    TITLES: [["проф. д-р"], ["доц. д-р"], ["гл. ас. д-р"], ["ас. д-р"]],
    FACULTIES: [
        ["БФ", "Бакалавърски факултет", "доц. д-р", "Илия Кожухаров"],
        ["МФ", "Магистърски факултет", "проф. д-р", "Борис Сергинов"],
        ["ФДЕНО",
         "Факултет за дистанционно, електронно и непрекъснато обучение",
         "доц. д-р", "Венцислав Джамбазов"],
    ],
    PROGRAMMES: [
        ["АУ-РО", "БП", "Администрация и управление", "РО", "БФ"],
        ["УБП-РО", "БП", "Управление на бизнеса и предприемачество", "РО",
         "БФ"],
        ["УБП-ДО", "БП", "Управление на бизнеса и предприемачество", "ДО",
         "ФДЕНО"],
        ["АМ-РО", "МП",
         "Артмениджмънт. Управление на културни институции и творчески "
         "индустрии", "РО", "МФ"],
        ["МОС-РО", "МП", "Мениджмънт за организационно съвършенство", "РО",
         "МФ"],
        ["МОС-ДО", "МП", "Мениджмънт за организационно съвършенство", "ДО",
         "ФДЕНО"],
        ["УРЧР-РО", "МП", "Управление и развитие на човешките ресурси", "РО",
         "МФ"],
        ["БА-РО", "МП", "Бизнес администрация", "РО", "МФ"],
    ],
    PROFESSORS: [],
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
    """What the four files hold, read once and checked."""

    def __init__(self, titles, faculties, programmes, professors):
        self.titles = titles            # [title]
        self.faculties = faculties      # {code: {name, dean_title, dean}}
        self.programmes = programmes    # {code: {degree, name, form, faculty}}
        self.professors = professors    # {code: {title, name, email}}

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


def write_starter(lists_dir):
    """Write any list that is missing, from the starting values."""
    lists_dir.mkdir(parents=True, exist_ok=True)
    for filename, rows in STARTER.items():
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


def load(lists_dir):
    """Read and check the four lists. Raises ListError."""
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

    return Lists(titles, faculties, programmes, professors)


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
