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

SIGNIN_TITLE = "Вход за студенти"
SIGNIN_INTRO = ("Въведете адреса си на електронна поща. Ще получите писмо с "
                "връзка за вход и шестцифрен код.")
SIGNIN_EMAIL = "Електронна поща"
SIGNIN_SEND = "Изпрати връзка и код"
SIGNIN_TOO_MANY = ("Поискани са твърде много писма за кратко време; опитайте "
                   "отново след час.")
SIGNIN_NOT_SENT = ("Писмото не можа да бъде изпратено, затова опитайте "
                   "отново по-късно.")
SIGNIN_CHECK_TITLE = "Проверете пощата си"
SIGNIN_CHECK_TEXT = ("Изпратихме писмо на {}. Отворете връзката в него или "
                     "въведете тук кода от писмото.")
SIGNIN_CODE = "Шестцифрен код"
SIGNIN_CODE_BUTTON = "Влез"
SIGNIN_OTHER_ADDRESS = "Друг адрес"
SIGNIN_REFUSED = ("Тази връзка или този код вече не важи или е грешен, "
                  "затова поискайте нов от страницата за вход.")
SIGNIN_LINK_TITLE = "Вход"
SIGNIN_LINK_TEXT = "Натиснете „Влез“, за да отворите заявлението си."
SIGNIN_LINK_BUTTON = "Влез"
SIGNIN_START_AGAIN = "Към страницата за вход"
SIGNIN_STAFF_LINK = "Вход за служители"

SIGNIN_MAIL_SUBJECT = "Вход в заявлението за дипломиране"
SIGNIN_MAIL_TEXT = """Здравейте,

за да влезете в заявлението си за дипломиране, отворете тази връзка и \
натиснете „Влез“:

{link}

или въведете този код на страницата, от която поискахте писмото:

{code}

Връзката и кодът важат {minutes} минути и могат да се използват веднъж.

Ако не сте поискали вход, не правете нищо: без връзката или кода никой не \
може да влезе с този адрес.
"""



# --- The application ---------------------------------------------------------



# --- The supervisor ----------------------------------------------------------



# --- Staff accounts and sign-in ----------------------------------------------

NAV_APPLICATION = "Заявление"
NAV_STAFF = "Заявления"
NAV_REPORTS = "Доклади"
NAV_OWNER = "Сметки"

STAFF_REGISTER_TITLE = "Регистрация на служител"
STAFF_REGISTER_INTRO = ("Новата сметка не вижда нищо, докато собственикът "
                        "не я одобри.")
STAFF_USERNAME = "Потребителско име"
STAFF_USERNAME_HINT = "Без знака „@“."
STAFF_EMAIL = "Електронна поща"
STAFF_PASSWORD = "Парола"
STAFF_PASSWORD_AGAIN = "Паролата отново"
STAFF_REGISTER_BUTTON = "Регистрирай"
STAFF_REGISTER_ERRORS = {
    "username": "Въведете потребителско име.",
    "username-at": "Потребителското име не може да съдържа „@“.",
    "email": "Въведете адрес на електронна поща.",
    "password": "Въведете парола.",
    "username-taken": "Това потребителско име вече е заето.",
    "email-taken": "Този адрес вече има сметка.",
    "mismatch": "Двете пароли не съвпадат.",
}
STAFF_REGISTERED_TITLE = "Сметката е създадена"
STAFF_REGISTERED_WAITING = ("Сметката чака одобрение от собственика. След "
                            "това ще влизате с потребителското име или "
                            "адреса си и паролата.")
STAFF_REGISTERED_OWNER = ("Това е сметката на собственика и не чака "
                          "одобрение; можете да влезете.")
STAFF_SIGNIN_TITLE = "Вход за служители"
STAFF_LOGIN = "Потребителско име или електронна поща"
STAFF_SIGNIN_BUTTON = "Влез"
STAFF_SIGNIN_FAILED = "Потребителското име, адресът или паролата не са верни."
STAFF_SIGNIN_WAITING = "Сметката още чака одобрение от собственика."
STAFF_TO_REGISTER = "Нямате сметка? Регистрирайте се."
STAFF_TO_SIGNIN = "Към входа за служители"
STAFF_TO_STUDENTS = "Вход за студенти"



# --- Staff work: tables, checks, corrections ---------------------------------



# --- The owner's page --------------------------------------------------------

OWNER_TITLE = "Сметки на служителите"
OWNER_WAITING = "Чакат одобрение"
OWNER_NONE_WAITING = "Няма сметки, които чакат одобрение."
OWNER_APPROVE = "Одобри"
OWNER_APPROVED = "Сметката „{}“ е одобрена."
OWNER_ALL = "Всички сметки"
OWNER_COL_USERNAME = "Потребителско име"
OWNER_COL_EMAIL = "Електронна поща"
OWNER_COL_STATE = "Състояние"
OWNER_COL_PASSWORD = "Нова парола"
OWNER_STATE_OWNER = "собственик"
OWNER_STATE_APPROVED = "одобрена"
OWNER_STATE_WAITING = "чака одобрение"
OWNER_NEW_PASSWORD = "Нова парола"
OWNER_NEW_PASSWORD_AGAIN = "Новата парола отново"
OWNER_SET_PASSWORD = "Смени паролата"
OWNER_PASSWORD_SET = ("Паролата на „{}“ е сменена и всички влизания с "
                      "предишната са прекратени. Кажете новата парола на "
                      "човека: системата не я изпраща.")
OWNER_PASSWORD_EMPTY = "Въведете новата парола."
OWNER_PASSWORD_MISMATCH = "Двете пароли не съвпадат; паролата не е сменена."



# --- Documents and reports ---------------------------------------------------



# --- The command line --------------------------------------------------------

CLI_NO_OWNER_SETTING = ("SUPERASSISTANT_OWNER_USERNAME не е зададено, затова "
                        "няма сметка на собственика, чиято парола да се "
                        "смени.")
CLI_NO_RECORDS = ("В {} няма записи, затова няма сметка „{}“ "
                  "(SUPERASSISTANT_DATA_DIR).")
CLI_NO_ACCOUNT = ("Никоя сметка в {} няма потребителското име „{}“, което "
                  "SUPERASSISTANT_OWNER_USERNAME назовава.")
CLI_PASSWORD_PROMPT = "Нова парола за „{}“: "
CLI_PASSWORD_AGAIN = "Новата парола отново: "
CLI_PASSWORD_EMPTY = "Паролата не може да е празна; нищо не е променено."
CLI_PASSWORD_MISMATCH = "Двете пароли не съвпадат; нищо не е променено."
CLI_PASSWORD_SET = ("Паролата на „{}“ е сменена; всички браузъри, влезли с "
                    "предишната, са изведени.")
