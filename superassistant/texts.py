"""All Bulgarian wording: the interface, the emails and the documents.

One module, so the owner can read and change every sentence in one place
(CLAUDE.md "Language"). Pages and emails take their words from here; code
never spells out Bulgarian text of its own.

Sections, in order: common, mail, student sign-in, the application, the
supervisor, staff accounts, staff work, the owner's page, documents and
reports, the command line.
"""

import html as _html


def escape(value):
    return _html.escape(value or "", quote=True)


# --- Common ----------------------------------------------------------------

SITE_NAME = "Дипломиране – департамент „Администрация и управление“, НБУ"
SITE_SHORT = "Дипломиране"
SIGN_OUT = "Изход"
SAVE = "Запази"
BACK = "Назад"
NOT_FOUND = "Тази страница не съществува."
FORBIDDEN = "Нямате достъп до тази страница."
CROSS_SITE = "Заявката не идва от тази страница. Опитайте отново."
FIELD_REQUIRED = "Полето „{}“ е задължително."

# --- Mail ------------------------------------------------------------------

MAIL_BAD_ADDRESS = "Това не прилича на адрес на електронна поща."
MAIL_FAILED = "Писмото не можа да бъде изпратено."
MAIL_INTENDED_FOR = "[Режим за разработка] Писмото е предназначено за: {}"
MAIL_CONSOLE_HEADER = "писмо (не е изпратено, режим console)"
MAIL_CONSOLE_FOOTER = "край на писмото"

# --- Student sign-in ---------------------------------------------------------



# --- The application ---------------------------------------------------------



# --- The supervisor ----------------------------------------------------------



# --- Staff accounts and sign-in ----------------------------------------------



# --- Staff work: tables, checks, corrections ---------------------------------



# --- The owner's page --------------------------------------------------------



# --- Documents and reports ---------------------------------------------------

# Words the Word files take from the records. The rest of each document's
# wording is in its template in templates/, which the owner edits in Word.
DOC_PROGRAMME = "{degree} „{name}“, {form}"
DOC_THESIS_ADJECTIVE = {"БП": "бакалавърска", "МП": "магистърска"}
DOC_GRAD_THESIS = "{} теза"
DOC_GRAD_EXAM = "държавен изпит"
DOC_THESIS_EITHER = "БАКАЛАВЪРСКА/ МАГИСТЪРСКА"

REPORTS_TITLE = "Доклади за утвърждаване на теми"
REPORTS_INTRO = ("Докладът изброява заявленията за теза по една програма, "
                 "чийто научен ръководител е потвърдил и чиято последна "
                 "проверка е успешна. Всеки създаден доклад се пази тук.")
REPORTS_PROGRAMME = "Програма"
REPORTS_OPTION = "{label} – {faculty} – заявления за доклада: {count}"
REPORTS_GENERATE = "Създай доклад"
REPORTS_MADE = "Докладът е създаден."
REPORTS_NOTHING = ("Няма заявление за доклада по програма {}: нито едно "
                   "заявление за теза по нея не е потвърдено от научния "
                   "ръководител с успешна последна проверка. Доклад не е "
                   "създаден.")
REPORTS_CHOOSE = "Изберете програма от списъка."
REPORTS_KEPT = "Създадени доклади"
REPORTS_NONE_KEPT = "Още няма създадени доклади."
REPORTS_COL_DATE = "Дата"
REPORTS_COL_PROGRAMME = "Програма"
REPORTS_COL_FACULTY = "Факултет"
REPORTS_COL_STUDENTS = "Студенти"
REPORTS_COL_FILE = "Файл"
REPORTS_DOWNLOAD = "Изтегли"



# --- The command line --------------------------------------------------------
