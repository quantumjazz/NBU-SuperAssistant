"""The Word files: the student's заявление-декларация and Приложение 2, and
the topic-approval report, filled from the records with docxtpl.

The templates in templates/ are the owner's samples with each dotted line the
records fill replaced by one {{ }} tag, and the report's student rows by one
templated row (tools/build_templates.py builds them). Everything a tag prints
is worked out here, from the records and the owner's lists, so the templates
hold no logic (CLAUDE.md "Documents"; NOW.md requirements 4, 6 and 7).

A field the records do not hold keeps a dotted line like the sample's, to be
filled by hand; a date left blank is dots in full, never a year.
"""

import io
import re
from pathlib import Path
from xml.sax.saxutils import escape

from docxtpl import DocxTemplate

from superassistant import db, texts

TEMPLATES = Path(__file__).resolve().parent.parent / "templates"
ZAIAVLENIE = "zaiavlenie.docx"
PRILOZHENIE2 = "prilozhenie2.docx"
DOKLAD_TEMI = "doklad_temi.docx"

MIMETYPE = ("application/vnd.openxmlformats-officedocument."
            "wordprocessingml.document")

# The samples' dotted lines, as long as theirs, for what is left to be
# filled by hand.
DOTS = {
    "names": "…" * 49, "fn": "F" + "…" * 7, "phone": "…" * 17,
    "email": "…" * 25, "programme": "…" * 51, "grad_type": "…" * 27,
    "date": "…" * 10 + "..", "topic": "…" * 58, "supervisor": "…" * 35,
    "average_grade": "…" * 11 + "..", "student": "…" * 26,
    "proposal_topic": "…" * 79, "section": "…" * 96,
}

# Characters an XML 1.0 file, and so a Word file, cannot hold: control
# characters other than tab and line break, lone surrogates, U+FFFE and
# U+FFFF. The application refuses them at entry (NOW.md requirement 2); they
# are dropped here as well, because the owner's list files are not checked
# for them, and a document must always open.
_NOT_IN_WORD = re.compile("[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f"
                          "\ud800-\udfff￾￿]")

try:
    from zoneinfo import ZoneInfo
    _LOCAL = ZoneInfo("Europe/Sofia")
except Exception:  # no time-zone data on this host: the host's own zone
    _LOCAL = None


class _Text(object):
    """A value as it goes into the document's XML.

    Escaped once here, so docxtpl's autoescaping leaves it alone; a line
    break becomes a line break in Word (docxtpl turns "\\n" inside a run into
    <w:br/>), and "_" is written as a character reference, because docxtpl
    rewrites "{_{" and similar pairs in its output after rendering.
    """

    def __init__(self, value):
        value = (value or "").replace("\r\n", "\n").replace("\r", "\n")
        value = _NOT_IN_WORD.sub("", value)
        self.xml = escape(value).replace("_", "&#95;")

    def __html__(self):
        return self.xml

    def __str__(self):
        return self.xml


def word_text(value):
    """What a value reads as once it is in a Word file: line breaks as "\\n",
    and characters Word cannot hold dropped."""
    value = (value or "").replace("\r\n", "\n").replace("\r", "\n")
    return _NOT_IN_WORD.sub("", value)


def _or_dots(value, dots):
    return _Text(value if value else dots)


# --- Labels from the records and the lists ----------------------------------

def local_date(stamp):
    """A stored moment (UTC) as the date in Sofia, DD.MM.YYYY."""
    moment = db.parse(stamp)
    moment = moment.astimezone(_LOCAL) if _LOCAL else moment.astimezone()
    return moment.strftime("%d.%m.%Y")


def student_name(application):
    """The three names as one line, one space between them."""
    return " ".join(part for part in (application["name1"],
                                      application["name2"],
                                      application["name3"]) if part)


def supervisor_label(application, lists):
    """A listed professor as the list writes them; else the typed title and
    name of a professor from outside the department."""
    if application["professor"]:
        return lists.professor_label(application["professor"])
    return " ".join(part for part in (application["sup_title"],
                                      application["sup_name"]) if part)


def programme_label(code, lists):
    programme = lists.programmes.get(code or "")
    if programme is None:
        return ""
    return texts.DOC_PROGRAMME.format(degree=programme["degree"],
                                      name=programme["name"],
                                      form=programme["form"])


def _degree(application, lists):
    programme = lists.programmes.get(application["programme"] or "")
    return programme["degree"] if programme else ""


def grad_type_label(application, lists):
    """бакалавърска теза, магистърска теза or държавен изпит."""
    if application["grad_type"] == "exam":
        return texts.DOC_GRAD_EXAM
    adjective = texts.DOC_THESIS_ADJECTIVE.get(_degree(application, lists))
    if application["grad_type"] == "thesis" and adjective:
        return texts.DOC_GRAD_THESIS.format(adjective)
    return ""


# --- Rendering ---------------------------------------------------------------

def _render(name, context):
    template = DocxTemplate(str(TEMPLATES / name))
    template.render(context, autoescape=True)
    out = io.BytesIO()
    template.save(out)
    return out.getvalue()


def zaiavlenie(application, lists):
    """The заявление-декларация of a submitted application, as .docx bytes.

    For a state exam only section 1's date is filled: the exams, their dates
    and the whole of section 2 stay dotted. For a thesis section 2 is filled
    and section 1 stays dotted. The Programme Council's decision box, the
    salutation, the signatures and the reviewer are never filled.
    """
    thesis = application["grad_type"] == "thesis"
    exam = application["grad_type"] == "exam"
    submitted = (local_date(application["submitted_at"])
                 if application["submitted_at"] else "")
    topic = application["topic"] if thesis else ""
    context = {
        "names": _or_dots(student_name(application), DOTS["names"]),
        "fn": _or_dots(application["fn"], DOTS["fn"]),
        "phone": _or_dots(application["phone"] if thesis else "",
                          DOTS["phone"]),
        "email": _or_dots(application["email"], DOTS["email"]),
        "programme": _or_dots(
            programme_label(application["programme"], lists) if thesis
            else "", DOTS["programme"]),
        "grad_type": _or_dots(grad_type_label(application, lists),
                              DOTS["grad_type"]),
        "exam_date": _or_dots(submitted if exam else "", DOTS["date"]),
        "topic": _or_dots(topic, "\n".join([DOTS["topic"]] * 3)),
        "supervisor": _or_dots(
            supervisor_label(application, lists) if thesis else "",
            DOTS["supervisor"]),
        "average_grade": _or_dots(
            application["average_grade"] if thesis else "",
            DOTS["average_grade"]),
        "thesis_date": _or_dots(submitted if thesis else "", DOTS["date"]),
    }
    return _render(ZAIAVLENIE, context)


def prilozhenie2(application, lists):
    """Приложение 2, the thesis proposal, as .docx bytes. Each section keeps
    its line breaks; the date it is handed in and the supervisor's signature
    stay blank."""
    adjective = texts.DOC_THESIS_ADJECTIVE.get(_degree(application, lists))
    context = {
        "thesis_heading": _Text(adjective.upper() if adjective
                                else texts.DOC_THESIS_EITHER),
        "names": _or_dots(student_name(application), DOTS["student"]),
        "fn": _or_dots(application["fn"], DOTS["fn"]),
        "topic": _or_dots(application["topic"], DOTS["proposal_topic"]),
    }
    for field in db.PROPOSAL_FIELDS:
        context[field] = _or_dots(application[field], DOTS["section"])
    return _render(PRILOZHENIE2, context)


def report_row(position, application, lists):
    """One student's row of the topic-approval report, as it is kept."""
    return {"position": position, "application_id": application["id"],
            "fn": application["fn"], "name": student_name(application),
            "topic": application["topic"],
            "supervisor": supervisor_label(application, lists)}


def doklad_temi(programme_code, rows, generated_at, lists):
    """The topic-approval report for one programme, as .docx bytes.

    Addressed to the dean of the programme's faculty, dated the day it is
    generated; the outgoing number, its year, the signatures and the
    Рецензент column stay blank (NOW.md requirement 7).
    """
    programme = lists.programmes[programme_code]
    faculty = lists.programme_faculty(programme_code)
    context = {
        "dean": _Text((faculty["dean_title"] + " " + faculty["dean"])
                      .upper()),
        "faculty": _Text(faculty["name"].upper()),
        "degree": _Text(programme["degree"]),
        "programme": _Text(programme["name"]),
        "thesis_adjective": _Text(
            texts.DOC_THESIS_ADJECTIVE[programme["degree"]]),
        "date": _Text(local_date(generated_at)),
        "students": [{"position": _Text(str(row["position"])),
                      "fn": _Text(row["fn"]), "name": _Text(row["name"]),
                      "topic": _Text(row["topic"]),
                      "supervisor": _Text(row["supervisor"])}
                     for row in rows],
    }
    return _render(DOKLAD_TEMI, context)
