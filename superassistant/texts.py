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



# --- The command line --------------------------------------------------------
