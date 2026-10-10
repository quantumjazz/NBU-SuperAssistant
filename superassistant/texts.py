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
MAIL_THROTTLED = ("Изпратени са твърде много писма за кратко време, затова "
                  "това не е изпратено. Опитайте отново по-късно.")
MAIL_INTENDED_FOR = "[Режим за разработка] Писмото е предназначено за: {}"
MAIL_CONSOLE_HEADER = "писмо (не е изпратено, режим console)"
MAIL_CONSOLE_FOOTER = "край на писмото"
MAIL_DEV_CONSOLE = ("Режим за разработка: писмата не се изпращат, а се "
                    "отпечатват в прозореца на Terminal, в който работи "
                    "приложението.")
MAIL_DEV_OWNER = "Режим за разработка: всички писма отиват само до {}."

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

NAV_APPLICATION_TITLE = "Заявление за дипломиране"
TAB_1 = "1. Заявление-декларация"
TAB_2 = "2. Предложение за теза"
ADVICE = ("Преди да подадете заявлението, говорете с преподавателя, когото "
          "искате за научен ръководител.")
GRAD_TYPE = "Как ще се дипломирате"
GRAD_THESIS = "С бакалавърска или магистърска теза"
GRAD_EXAM = "С държавен изпит"
THESIS_BACHELOR = "бакалавърска теза"
THESIS_MASTER = "магистърска теза"
EXAM_ONLY_NAMES = ("За държавен изпит са нужни само трите имена и "
                   "факултетният номер.")
THESIS_ONLY = "Попълва се при дипломиране с теза"
SUPERVISOR_FROM_LIST = "Научен ръководител от департамента"
SUPERVISOR_NONE = "— изберете —"
SUPERVISOR_OUTSIDE = "Или преподавател извън департамента"
SUPERVISOR_OUTSIDE_HINT = ("Попълнете тези три полета само ако научният ви "
                           "ръководител не е в списъка.")
PROGRAMME_NONE = "— изберете —"
STUDENT_LINE = "Студент: {} ({})"
TOPIC_LINE = "Тема: {}"
EMAIL_LINE = "Електронна поща: {}"
EMAIL_LABEL = "Електронна поща"
SAVE_DRAFT = "Запази"
NEXT_TAB = "Запази и продължи"
SUBMIT = "Подай заявлението"
SUBMIT_CONFIRM_HINT = ("След подаване можете да промените само научния "
                       "ръководител, ако той откаже. Други корекции прави "
                       "администрацията.")
SAVED = "Запазено."
SUBMITTED = "Заявлението е подадено."
SUBMIT_MAIL_FAILED = ("Заявлението не е подадено: писмото до научния "
                      "ръководител не можа да бъде изпратено. Опитайте "
                      "отново по-късно.")
FIX_BELOW = "Поправете отбелязаните полета."
REFUSED_CONTROL = ("Полето съдържа знак, който не може да се запише в "
                   "документ: {}")
REFUSED_MIXED = ("В дума са смесени латински и кирилски букви. Напишете "
                 "отново: {}")
REFUSED_CHOICE = "Изберете стойност от списъка."
REFUSED_REQUIRED = "Попълнете това поле."
STATUS_TITLE = "Къде е заявлението"
STATUS_DRAFT = "Не е подадено."
STATUS_SUBMITTED = "Подадено на {}."
STATUS_AWAITED = "Чака отговор от научния ръководител."
STATUS_CONFIRMED = "Научният ръководител потвърди."
STATUS_DECLINED = "Научният ръководител не потвърди."
STATUS_CHECK_PASSED = "Проверката на данните е успешна."
STATUS_CHECK_NOT_PASSED = ("Проверката на данните не е успешна. "
                           "Администрацията ще се свърже с вас.")
STATUS_NO_CHECK = "Данните още не са проверени."
FORMS_TITLE = "Документи за печат и подпис"
CHOOSE_AGAIN_TITLE = "Изберете друг научен ръководител"
CHOOSE_AGAIN = "Изпрати молбата"
CHOSEN_AGAIN = "Молбата е изпратена на новия научен ръководител."
ENTERED_TITLE = "Въведени данни"
FIELD_LABELS = {
    "name1": "Собствено име",
    "name2": "Бащино име",
    "name3": "Фамилия",
    "fn": "Факултетен номер (F№)",
    "phone": "Телефон",
    "programme": "Програма и форма на обучение",
    "topic": "Тема на тезата",
    "average_grade": "Среден успех от следването",
    "professor": "Научен ръководител",
    "sup_name": "Име на преподавателя",
    "sup_title": "Академична длъжност и степен",
    "sup_email": "Електронна поща на преподавателя",
    "rationale": "Обосновка на темата",
    "aims": "Цели и задачи",
    "object_subject": "Обект и предмет на изследването",
    "methodology": "Методологична база на изследването",
    "information_base": "Информационна база на изследването",
    "plan": "Примерен план-съдържание",
    "schedule": "Времеви график",
    "grad_type": "Как ще се дипломирате",
}
FIELD_HINTS = {
    "rationale": "актуалност, важност и значимост за теорията и практиката",
    "aims": "обща цел и конкретни задачи за нейното постигане",
    "object_subject": ("организацията, където ще се осъществи изследването, "
                       "и аспектите на самото изследване"),
    "methodology": "методи, инструменти и др.",
    "information_base": ("първични и вторични данни, етични съображения при "
                         "провеждането на изследването"),
    "plan": "глави и други подразделения",
    "schedule": ("основни етапи на изследването и предаване на отделните "
                 "части"),
}



# --- The supervisor ----------------------------------------------------------

REQUEST_SUBJECT = "Молба за научно ръководство: {student}"
REMINDER_SUBJECT = "Напомняне: молба за научно ръководство: {student}"
REMINDER_LEAD = "Напомняне: все още очакваме вашия отговор."
REQUEST_TEXT = (
    "Уважаеми(а) {supervisor},\n\n"
    "{student} (F№ {fn}), {programme}, ви посочва за научен ръководител на "
    "{kind} на тема:\n\n„{topic}“\n\n"
    "{proposal}\n\n"
    "Потвърждавам: {confirm}\n"
    "Не потвърждавам: {decline}\n\n"
    "Всеки от двата адреса отваря страница, на която можете да добавите "
    "коментар и да запишете отговора си.\n")
REQUEST_HTML = (
    "<p>Уважаеми(а) {supervisor},</p>"
    "<p>{student} (F№ {fn}), {programme}, ви посочва за научен ръководител "
    "на {kind} на тема:</p><p><strong>„{topic}“</strong></p>"
    "{proposal}"
    "<p style=\"margin:24px 0\">"
    "<a href=\"{confirm}\" style=\"display:inline-block;padding:10px 18px;"
    "background:#222;color:#fff;text-decoration:none;border-radius:4px;"
    "margin-right:12px\">Потвърждавам</a>"
    "<a href=\"{decline}\" style=\"display:inline-block;padding:10px 18px;"
    "background:#fff;color:#222;border:1px solid #222;text-decoration:none;"
    "border-radius:4px\">Не потвърждавам</a></p>"
    "<p>Всеки бутон отваря страница, на която можете да добавите коментар и "
    "да запишете отговора си.</p>")
DECLINE_SUBJECT = "Научният ръководител не потвърди"
DECLINE_TEXT = (
    "Здравейте, {student},\n\n"
    "{supervisor} не потвърди молбата ви за научно ръководство. Можете да "
    "изберете друг научен ръководител на страницата на заявлението:\n\n"
    "{link}\n")
ANSWER_TITLE_CONFIRM = "Потвърждавам научното ръководство"
ANSWER_TITLE_DECLINE = "Не потвърждавам научното ръководство"
ANSWER_INTRO = "{student}, {programme}, тема „{topic}“."
ANSWER_COMMENT = "Коментар (по желание, вижда го само администрацията)"
ANSWER_RECORD_CONFIRM = "Запиши: Потвърждавам"
ANSWER_RECORD_DECLINE = "Запиши: Не потвърждавам"
ANSWER_RECORDED = "Отговорът ви е записан: {} на {}."
ANSWER_WORD = {"confirm": "Потвърждавам", "decline": "Не потвърждавам"}
ANSWER_ALREADY = "Отговорът по тази молба вече е записан: {} на {}."
ANSWER_REPLACED = "Тази молба вече не е в сила. Не е нужно да отговаряте."
ANSWER_UNKNOWN = "Тази връзка не е валидна."
ANSWER_NOTICE_FAILED = ("Отговорът е записан, но писмото до студента не "
                        "можа да бъде изпратено. Студентът ще го види на "
                        "страницата на заявлението си.")
CLI_REMINDERS_SENT = "Изпратени напомняния: {}"
CLI_REMINDER_FAILED = ("Напомнянето до {} (заявление {}) не е изпратено: {}")



# --- Staff accounts and sign-in ----------------------------------------------

NAV_APPLICATION = "Заявление"
NAV_STAFF = "Заявления"
NAV_REPORTS = "Доклади"
NAV_OWNER = "Профили"

STAFF_REGISTER_TITLE = "Регистрация на служител"
STAFF_REGISTER_INTRO = ("Новият профил не вижда нищо, докато собственикът "
                        "не го одобри.")
STAFF_USERNAME = "Потребителско име"
STAFF_USERNAME_HINT = "Без знака „@“."
STAFF_EMAIL = "Служебна електронна поща"
STAFF_PASSWORD = "Парола"
STAFF_PASSWORD_AGAIN = "Паролата отново"
STAFF_REGISTER_BUTTON = "Регистрирай"
STAFF_REGISTER_ERRORS = {
    "username": "Въведете потребителско име.",
    "username-at": "Потребителското име не може да съдържа „@“.",
    "email": "Въведете адрес на електронна поща.",
    "password": "Въведете парола.",
    "username-taken": "Това потребителско име вече е заето.",
    "email-taken": "Този адрес вече има профил.",
    "mismatch": "Двете пароли не съвпадат.",
}
STAFF_REGISTERED_TITLE = "Профилът е създаден"
STAFF_REGISTERED_WAITING = ("Профилът чака одобрение от собственика. След "
                            "това ще влизате с потребителското име или "
                            "адреса си и паролата.")
STAFF_REGISTERED_OWNER = ("Това е профилът на собственика и не чака "
                          "одобрение; можете да влезете.")
STAFF_SIGNIN_TITLE = "Вход за служители"
STAFF_LOGIN = "Потребителско име или електронна поща"
STAFF_SIGNIN_BUTTON = "Влез"
STAFF_SIGNIN_FAILED = "Потребителското име, адресът или паролата не са верни."
STAFF_SIGNIN_WAITING = "Профилът още чака одобрение от собственика."
NO_OWNER_YET = ("Още не е посочен собственик, който да одобрява профили: "
                "собственикът задава SUPERASSISTANT_OWNER_USERNAME (своето "
                "потребителско име) и стартира приложението отново.")
STAFF_TO_REGISTER = "Нямате профил? Регистрирайте се."
STAFF_TO_SIGNIN = "Към входа за служители"
STAFF_TO_STUDENTS = "Вход за студенти"



# --- Staff work: tables, checks, corrections ---------------------------------

STAFF_TABLE_TITLE = "Подадени заявления"
STAFF_COLUMNS = ("Студент", "F№", "Програма", "Вид", "Тема",
                 "Научен ръководител", "Отговор", "Проверка")
STAFF_EMPTY = "Още няма подадени заявления."
STAFF_TYPE = {"thesis": "теза", "exam": "държавен изпит"}
STAFF_ANSWER = {"awaited": "чака отговор", "confirm": "потвърди",
                "decline": "не потвърди", None: "—"}
STAFF_CHECK = {"passed": "успешна", "not_passed": "неуспешна", None: "—"}
STAFF_WAITING_SUPERVISOR = "чака научния ръководител"
STAFF_WAITING_CHECK = "чака проверка"
STAFF_WAITING_REPORT = "чака доклад"
STAFF_LEGEND = "Оцветените редове чакат действие."
STAFF_APPLICATION_TITLE = "Заявление на {}"
STAFF_SUBMITTED_AT = "Подадено на"
STAFF_STUDENT_EMAIL = "Електронна поща на студента"
STAFF_REQUESTS_TITLE = "Молби до научен ръководител"
STAFF_REQUEST_LINE = "{} ({}), изпратена на {}"
STAFF_REQUEST_ANSWER = "Отговор: {} на {}"
STAFF_REQUEST_COMMENT = "Коментар: {}"
STAFF_REQUEST_REPLACED = "Заменена на {}"
STAFF_REMINDERS = "Напомняния: {}"
STAFF_CHECKS_TITLE = "Проверки в базите данни на университета"
STAFF_CHECK_LINE = "{} от {} на {}"
STAFF_CHECK_FORM = "Запиши проверка"
STAFF_CHECK_PASSED = "Успешна"
STAFF_CHECK_NOT_PASSED = "Неуспешна"
STAFF_CHECK_NOTE = "Бележка"
STAFF_CHECK_RECORD = "Запиши проверката"
STAFF_CHECK_RECORDED = "Проверката е записана."
STAFF_CORRECTIONS_TITLE = "Корекции"
STAFF_CORRECTION_LINE = "{}: „{}“ → „{}“ ({}, {})"
STAFF_CORRECT_FORM = "Поправи въведени данни"
STAFF_CORRECT_SAVE = "Запиши корекцията"
STAFF_CORRECT_FIELD = "Поле"
STAFF_CORRECT_VALUE = "Нова стойност"
STAFF_CORRECT_PROGRAMME_HINT = "За програма въведете кода ѝ:"
STAFF_CORRECTED = "Корекцията е записана."
STAFF_NOTHING_CHANGED = "Нищо не е променено."
STAFF_SUPERVISOR_FORM = "Смени научния ръководител"
STAFF_SUPERVISOR_HINT = ("Смяната изпраща нова молба; отговорът по "
                         "предишната молба остава записан при нея.")
STAFF_SUPERVISOR_SAVE = "Смени и изпрати молба"
STAFF_SUPERVISOR_CHANGED = "Научният ръководител е сменен и молбата е изпратена."
STAFF_TYPE_FORM = "Поправи вида на дипломиране"
STAFF_TYPE_HINT = ("Към теза: данните за теза трябва да са попълнени и се "
                   "изпраща молба до научния ръководител. Към държавен "
                   "изпит: молбата, която е в сила, се оттегля; записаните "
                   "отговори остават.")
STAFF_TYPE_SAVE = "Запиши вида"
STAFF_TYPE_CHANGED = "Видът на дипломиране е поправен."
STAFF_TYPE_MISSING = "За теза липсват: {}."
STAFF_SUPERVISOR_MAIL_FAILED = ("Нищо не е променено: молбата не можа да бъде "
                                "изпратена.")



# --- The owner's page --------------------------------------------------------

OWNER_TITLE = "Профили на служителите"
OWNER_WAITING = "Чакат одобрение"
OWNER_NONE_WAITING = "Няма профили, които чакат одобрение."
OWNER_APPROVE = "Одобри"
OWNER_APPROVED = "Профилът „{}“ е одобрен."
OWNER_ALL = "Всички профили"
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

CLI_NO_OWNER_SETTING = ("SUPERASSISTANT_OWNER_USERNAME не е зададено, затова "
                        "няма профил на собственика, чиято парола да се "
                        "смени.")
CLI_NO_RECORDS = ("В {} няма записи, затова няма профил „{}“ "
                  "(SUPERASSISTANT_DATA_DIR).")
CLI_NO_ACCOUNT = ("Никой профил в {} няма потребителското име „{}“, което "
                  "SUPERASSISTANT_OWNER_USERNAME назовава.")
CLI_PASSWORD_PROMPT = "Нова парола за „{}“: "
CLI_PASSWORD_AGAIN = "Новата парола отново: "
CLI_PASSWORD_EMPTY = "Паролата не може да е празна; нищо не е променено."
CLI_PASSWORD_MISMATCH = "Двете пароли не съвпадат; нищо не е променено."
CLI_PASSWORD_SET = ("Паролата на „{}“ е сменена; всички браузъри, влезли с "
                    "предишната, са изведени.")
