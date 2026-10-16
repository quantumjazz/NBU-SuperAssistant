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
SITE_DEPARTMENT = "Департамент „Администрация и управление“, НБУ"
SITE_FOOTER = "Програмен съвет на департамент „Администрация и управление“, Нов български университет"
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
MAIL_CONSOLE_ATTACHMENT = "Прикачен файл: {} ({} байта)"
MAIL_DEV_CONSOLE = ("Режим за разработка: писмата не се изпращат, а се "
                    "отпечатват в прозореца на Terminal, в който работи "
                    "приложението.")
MAIL_DEV_OWNER = "Режим за разработка: всички писма отиват само до {}."

# --- Student sign-in ---------------------------------------------------------

SIGNIN_TITLE = "Вход за студенти"
SIGNIN_INTRO = ("Въведете електронната си поща и ще ви изпратим писмо с "
                "връзка за вход и шестцифрен код. Парола не е нужна.")
SIGNIN_HOW = ("Въвеждате електронната си поща.",
              "Отваряте връзката от писмото или въвеждате кода.",
              "Попълвате заявлението и го подавате.")
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
STEP_1 = "Заявление-декларация"
STEP_2 = "Предложение за теза"
SECTION_PERSON = "Лични данни"
SECTION_THESIS = "Теза"
SECTION_SUPERVISOR = "Научен ръководител"
DRAFT_LEAD = ("Попълнете заявлението и го подайте. Можете да спрете и да "
              "продължите по-късно: въведеното се пази, когато натиснете „Запази“.")
STATUS_CHIP = {"awaited": "Чака ръководителя", "confirm": "Потвърдено", "decline": "Не е потвърдено", None: "Подадено"}
STATUS_NEXT = {"awaited": "Изпратихме на научния ръководител писмо с молба за потвърждение.",
               "confirm": "Администрацията проверява данните и подготвя доклада.",
               "decline": "Изберете друг научен ръководител по-долу."}
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
SUPERVISOR_NONE = "Изберете от списъка"
SUPERVISOR_OUTSIDE = "Или преподавател извън департамента"
SUPERVISOR_OUTSIDE_HINT = ("Попълнете тези три полета само ако научният ви "
                           "ръководител не е в списъка.")
PROGRAMME_NONE = "Изберете от списъка"
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
REFUSED_FN = "Въведете само цифрите на факултетния номер."
# The form's own sentence, verbatim (the owner, 13 October 2026).
DECLARE_CREDITS = ("Декларирам, че към момента съм покрил(а) всички кредити "
                   "по програмна схема към програмата.")
TICK_REQUIRED = "Отбележете това поле, за да подадете заявлението."
# The schedule of sessions (constitution 5.13): built from the sessions list,
# its column headings and its note as the department's framework schedule
# prints them. A session's date is always written as SESSION_DATE, a
# deadline as SESSION_DEADLINE, from the date in the list; the year and „г.“
# are kept on one line (a no-break space between them).
SCHEDULE_TITLE = "Сесия за дипломиране"
SCHEDULE_LEAD = "График на сесиите за защита на тези и за държавен изпит"
SCHEDULE_COLUMNS = (
    "Сесия",
    "Подаване на заявления и общи справки за одобряване на теми",
    "Подаване на заявления и общи справки за държавен изпит",
    "Предаване на одобрени бакалавърски/магистърски тези – 1 екз. + 2 бр. CD")
SCHEDULE_PASSED = "отминала"
SCHEDULE_NOTE = ("В графика са посочени само началните дати на сесиите. "
                 "Продължителността им зависи от броя на допуснатите до "
                 "защита и държавен изпит дипломанти.")
SESSION_CHOOSE = "Изберете сесия"
SESSION_NONE_OFFERED = ("В графика няма предстояща сесия. Свържете се с "
                        "администрацията на департамента.")
# The sentence the student ticks, as the approved plan words it (NOW.md of
# milestone 3, requirement 4; the owner, 16 October 2026: "Yes, all of it").
ACK_SCHEDULE = ("Запознат(а) съм с рамковия график на сесиите за защита на "
                "тези и за държавен изпит и със сроковете в него.")
REFUSED_SESSION = "Изберете сесия от графика."
SESSION_DATE = "{day} {month} {year}\u00a0г. ({weekday})"
SESSION_DEADLINE = "до {day} {month} {year}\u00a0г."
MONTHS = ("януари", "февруари", "март", "април", "май", "юни", "юли",
          "август", "септември", "октомври", "ноември", "декември")
WEEKDAYS = ("понеделник", "вторник", "сряда", "четвъртък", "петък", "събота",
            "неделя")
SESSION_NONE = "—"
SESSION_CHOSEN = "Избрана сесия: {}"
ACKNOWLEDGED = "Запознат(а) с графика на сесиите"
ACKNOWLEDGED_VALUE = {True: "да", False: "—"}
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
STATUS_REMOVED_TITLE = "Заявлението е премахнато"
STATUS_REMOVED = ("Администрацията премахна заявлението ви и то вече не "
                  "може да бъде променяно. Ако смятате, че това е грешка, "
                  "свържете се с администрацията на департамента.")
# The heading and the line, verbatim, "visible in each case" (the owner,
# 16 October 2026): the student prints and hands in nothing.
FORMS_TITLE = "Попълнени документи"
FORMS_LEAD = ("Не е нужно да отпечатвате и представяте документите: "
              "администрацията на департамента вече разполага с тях. "
              "Можете да ги изтеглите за справка.")
FORMS_ZAIAVLENIE = "Заявление-декларация (.docx)"
FORMS_PRILOZHENIE2 = "Приложение 2 (.docx)"
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
    "grad_session": "Сесия",
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
CONFIRM_SUBJECT = "Научният ръководител потвърди"
CONFIRM_TEXT = (
    "Здравейте, {student},\n\n"
    "{supervisor} потвърди молбата ви за научно ръководство на тема "
    "„{topic}“.\n\n"
    "Състоянието на заявлението си можете да видите на страницата му:\n\n"
    "{link}\n")
ANSWER_TITLE_CONFIRM = "Потвърждавам научното ръководство"
ANSWER_TITLE_DECLINE = "Не потвърждавам научното ръководство"
# The title and heading of an answer page that can no longer record an answer
# (an invalid link, an answered or a replaced request): it names no choice.
ANSWER_TITLE_NEUTRAL = "Молба за научно ръководство"
ANSWER_INTRO = "{student}, {programme}, тема „{topic}“."
ANSWER_CHIP = "Молба за научно ръководство"
ANSWER_LEAD = "Студентът ви посочва за научен ръководител. Запишете отговора си с бутона по-долу; коментарът е по желание."
ANSWER_FIELDS = ("Студент", "Програма", "Тема")
ANSWER_COMMENT = "Коментар (по желание, вижда го само администрацията)"
ANSWER_RECORD_CONFIRM = "Запиши „Потвърждавам“"
ANSWER_RECORD_DECLINE = "Запиши „Не потвърждавам“"
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
NAV_BIN = "Кошче"
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
STAFF_COLUMNS = ("Студент", "F№", "Програма", "Код", "Вид", "Сесия",
                 "Кредити", "Тема", "Научен ръководител", "Отговор",
                 "Проверка")
# Under the session in the table: whether the student ticked knowing the
# schedule, with ACKNOWLEDGED_VALUE.
STAFF_ACKNOWLEDGED_SUB = "график: {}"
STAFF_PROGRAMME_CODE = "Код на програмата"
STAFF_DECLARED = "Декларира покрити кредити"
STAFF_DECLARED_VALUE = {True: "да", False: "—"}
STAFF_EMPTY = "Още няма подадени заявления."
STAFF_TYPE = {"thesis": "теза", "exam": "държавен изпит"}
STAFF_ANSWER = {"awaited": "чака отговор", "confirm": "потвърди",
                "decline": "не потвърди", None: "—"}
STAFF_CHECK = {"passed": "успешна", "not_passed": "неуспешна", None: "—"}
STAFF_WAITING_SUPERVISOR = "чака научния ръководител"
STAFF_WAITING_CHECK = "чака проверка"
STAFF_WAITING_REPORT = "чака доклад"
STAFF_LEGEND = "Оцветените редове чакат действие."
STAFF_LEAD = "Всяко подадено заявление, с отговора на научния ръководител и последната проверка. Отворете име, за да видите всичко и да запишете проверка."
STAFF_COUNT_ALL = ("заявление", "заявления")
STAFF_COUNT_WAITING = {"supervisor": ("чака научния ръководител", "чакат научния ръководител"),
                       "check": ("чака проверка", "чакат проверка"),
                       "report": ("чака доклад", "чакат доклад")}
STAFF_CHECK_CHIP = {"passed": "проверено", "not_passed": "неуспешна", None: "непроверено"}
STAFF_APPLICATION_TITLE = "Заявление на {}"
STAFF_SUBMITTED_AT = "Подадено на"
STAFF_STUDENT_EMAIL = "Електронна поща на студента"
STAFF_FORMS_TITLE = "Документи на студента"
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
STAFF_CORRECTION_LINE = "{}: от „{}“ на „{}“ ({}, {})"
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
STAFF_RETAINED_THESIS = "Запазени данни за теза"
STAFF_SUPERVISOR_MAIL_FAILED = ("Нищо не е променено: молбата не можа да бъде "
                                "изпратена.")
STAFF_SESSION_FORM = "Поправи сесията"
STAFF_SESSION_HINT = ("Може да бъде избрана всяка сесия от графика, "
                      "включително отминала.")
STAFF_SESSION_OPTION_PASSED = "{} – отминала"
STAFF_SESSION_SAVE = "Запиши сесията"

# The bin (constitution 5.14 and 5.15): an application or a report staff
# remove waits here, to be put back or deleted.
BIN_TITLE = "Кошче"
BIN_LEAD = ("Премахнатите заявления и доклади чакат тук, докато бъдат "
            "върнати или изтрити окончателно.")
BIN_EMPTY = "Кошчето е празно."
BIN_APPLICATIONS = "Заявления"
BIN_NO_APPLICATIONS = "Няма премахнати заявления."
BIN_REPORTS = "Доклади"
BIN_NO_REPORTS = "Няма премахнати доклади."
BIN_REASON = {"graduated": "дипломиран(а)", "other": "друго"}
BIN_COLUMNS = ("Студент", "F№", "Програма", "Причина", "Премахнато", "")
BIN_REMOVE_FORM = "Премахни заявлението"
BIN_REMOVE_HINT = ("Заявлението отива в кошчето: излиза от таблицата и от "
                   "докладите, които ще бъдат създадени (вече създадените "
                   "не се променят), научният ръководител не получава "
                   "напомняния, а студентът не може да го променя. От "
                   "кошчето може да бъде върнато или изтрито окончателно.")
BIN_REASON_LABEL = "Причина"
BIN_REASON_GRADUATED = "Дипломиран(а)"
BIN_REASON_OTHER = "Друго"
BIN_NOTE = "Бележка (по желание)"
BIN_REMOVE = "Премахни"
BIN_CHOOSE_REASON = "Изберете причина."
BIN_REMOVED = "Заявлението е преместено в кошчето."
BIN_IN_BIN = "В кошчето"
BIN_IN_BIN_LINE = "Премахнато от {} на {}. Причина: {}."
BIN_NOTE_LINE = "Бележка: {}"
BIN_RESTORE = "Върни"
BIN_RESTORED = "Заявлението е върнато."
BIN_DELETE = "Изтрий окончателно"
BIN_DELETE_TITLE = "Окончателно изтриване на заявление"
BIN_DELETE_LEAD = ("Изтриването премахва заявлението и всичко записано към "
                   "него: отговорите на научния ръководител, проверките, "
                   "корекциите и реда му в докладите, включително в тези "
                   "в кошчето. Файловете на докладите остават такива, "
                   "каквито са, а нощните копия от последните 30 дни и "
                   "архивите, направени преди изтриването, още го "
                   "съдържат. "
                   "Изтриването не може да бъде отменено.")
BIN_DELETED = "Заявлението е изтрито."
BIN_NOT_IN_BIN = ("Заявлението вече не е в кошчето: върнато е или е "
                  "изтрито. Нищо не е променено.")
BIN_REMOVED_MEANWHILE = ("Заявлението междувременно е преместено в кошчето "
                         "или е изтрито. Нищо не е променено.")
BIN_DELETIONS = "Изтрити заявления"
BIN_DELETIONS_COLUMNS = ("Заявление", "Причина", "Премахнато", "Изтрито")
BIN_NUMBER = "№ {}"
BIN_BY_AT = "{}, {}"



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
                 "проверка е успешна. Всеки създаден доклад се пази тук, "
                 "докато не бъде преместен в кошчето.")
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
REPORTS_REMOVE = "Премахни"
REPORTS_REMOVE_HINT = ("„Премахни“ премества доклада в кошчето и изброените "
                       "в него студенти отново чакат доклад. От кошчето "
                       "докладът може да бъде изтеглен, върнат или изтрит "
                       "окончателно.")
REPORTS_REMOVED = "Докладът е преместен в кошчето."
REPORTS_RESTORED = "Докладът е върнат."
REPORTS_DELETE_TITLE = "Окончателно изтриване на доклад"
REPORTS_DELETE_LEAD = ("Изтриването премахва файла и записа на доклада; "
                       "архивите, направени преди изтриването, още ги "
                       "съдържат. Изтриването не може да бъде отменено.")
REPORTS_DELETED = "Докладът е изтрит."
REPORTS_NOT_IN_BIN = ("Докладът не е в кошчето: само доклад от кошчето може "
                      "да бъде върнат или изтрит. Нищо не е променено.")
REPORTS_REMOVED_MEANWHILE = ("Докладът междувременно е преместен в кошчето "
                             "или е изтрит. Нищо не е променено.")
REPORTS_DELETIONS = "Изтрити доклади"
REPORTS_COL_REMOVED = "Премахнат"
REPORTS_COL_DELETED = "Изтрит"



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

CLI_MAIL_TEST_USAGE = ("Употреба: python -m superassistant mail-test <адрес>\n"
                       "Изпраща едно пробно писмо за <адрес> според режима "
                       "за поща (SUPERASSISTANT_MAIL_MODE).")
CLI_MAIL_TEST_BAD_ADDRESS = ("„{}“ не прилича на адрес на електронна поща; "
                             "нищо не е изпратено.")
CLI_MAIL_TEST_UNCONFIGURED = ("Пощата не е настроена, затова нищо не е "
                              "изпратено: {}")
CLI_MAIL_TEST_MODE_UNSET = "console (SUPERASSISTANT_MAIL_MODE не е зададено)"
CLI_MAIL_TEST_PLAN_CONSOLE = ("Режим {mode}: писмото за {address} ще бъде "
                              "отпечатано тук, без да бъде изпратено.")
CLI_MAIL_TEST_PLAN_OWNER = ("Режим owner: писмото за {address} ще отиде до "
                            "{owner}, с {address} написан най-отгоре.\n"
                            "  Сървър за поща: {relay}\n"
                            "  Подател: {sender}")
CLI_MAIL_TEST_PLAN_SEND = ("Режим send: писмото ще отиде до {address}.\n"
                           "  Сървър за поща: {relay}\n"
                           "  Подател: {sender}")
CLI_MAIL_TEST_PRINTED = "Писмото е отпечатано по-горе; нищо не е изпратено."
CLI_MAIL_TEST_ACCEPTED = ("Сървърът за поща прие писмото.\n\n"
                          "Прието не значи доставено: проверете пощенската "
                          "кутия и папката за спам.")
CLI_MAIL_TEST_REFUSED = ("Писмото не е изпратено: сървърът за поща не го "
                         "прие или не можа да бъде достигнат.\n{}")
CLI_MAIL_TEST_SUBJECT = "Пробно писмо от NBU-SuperAssistant"
CLI_MAIL_TEST_TEXT = ("Това е пробното писмо от командата "
                      "`python -m superassistant mail-test {address}`.\n\n"
                      "Щом го четете, писмата на NBU-SuperAssistant "
                      "({base_url}) стигат до тази пощенска кутия.\n")

# The nightly copy (constitution 6.7): the file's columns, the message to the
# owner and what the command says.
SNAPSHOT_COLUMNS = (
    "№", "Подадено на", "Електронна поща на студента", "Вид",
    "Собствено име", "Бащино име", "Фамилия", "F№",
    "Декларира покрити кредити", "Запознат(а) с графика на сесиите",
    "Сесия", "Телефон", "Програма и форма на обучение",
    "Код на програмата", "Тема на тезата", "Среден успех от следването",
    "Научен ръководител", "Електронна поща на научния ръководител",
    "Обосновка на темата", "Цели и задачи",
    "Обект и предмет на изследването",
    "Методологична база на изследването",
    "Информационна база на изследването", "Примерен план-съдържание",
    "Времеви график", "Отговор на научния ръководител", "Отговорено на",
    "Коментар на научния ръководител", "Последна проверка", "Проверено на",
    "Бележка към проверката", "В доклад", "В кошчето", "Премахнато на",
    "Бележка при премахване")
SNAPSHOT_YES_NO = {True: "да", False: "не"}
SNAPSHOT_NOT_BINNED = "не"
SNAPSHOT_SUBJECT = "Копие на заявленията към {date}"
SNAPSHOT_TEXT = ("Здравейте,\n\n"
                 "прикачен е файлът {name}: копие на всички подадени "
                 "заявления към {moment}, общо {count}, от тях в кошчето "
                 "{binned}.\n\n"
                 "Файлът се отваря с Excel. На сървъра се пазят копията от "
                 "последните {days} дни.\n")
# The word after the count: its first form for one, the second otherwise.
CLI_SNAPSHOT_WRITTEN = "Копието е записано: {path} ({count} {word}, {size} байта)."
CLI_SNAPSHOT_WORD = ("заявление", "заявления")
CLI_SNAPSHOT_PRUNED = "Изтрити стари копия: {}"
CLI_SNAPSHOT_SENT = "Копието е изпратено до {}."
CLI_SNAPSHOT_PRINTED = "Писмото е отпечатано по-горе; нищо не е изпратено."
CLI_SNAPSHOT_NO_OWNER = ("Копието не е изпратено: SUPERASSISTANT_OWNER_USERNAME "
                         "не е зададено, затова няма адрес на собственика.")
CLI_SNAPSHOT_NOT_SENT = "Копието не е изпратено: {}"
