# NOW — Milestone 1: from the application to the topic-approval report

## Goal

On the owner's Mac, from an empty installation and with invented people only, the process in `CONSTITUTION.md` 5.1 to 5.7 works end to end: a student signs in and applies, the supervisor answers by email, staff check the application, and the topic-approval report comes out in Word.

## Required behaviour

1. **Student sign-in** by emailed link or six-digit code (constitution 5.2, 6.6). Opening the link only shows its „Влез“ page and spends nothing; pressing „Влез“, or typing the code, signs the student in. Signing in again with the same address reaches the same application.

2. **The application** (5.3, 7.1). Two tabs; the first tab reminds the student to talk to a prospective supervisor beforehand (5.1). Every student gives three names, F№ and the graduation type; the email address is the one signed in with. For a state exam "only names and faculty numbers are needed": nothing more is asked, not even a programme (8.3), and there is no second tab. For a thesis the first tab also asks telephone, programme and form of study (РО or ДО) from the owner's list, topic, average grade and the supervisor. The supervisor is chosen from the professors list or typed, with a title from the owner's list and an email address, in the field for a professor from outside the department. The second tab asks the proposal's sections, from обосновка на темата to времеви график (`docs/domain.md`). Entries are kept as typed, without spaces at either end, F№ in capitals. Refused, with the characters shown: a character a Word file cannot hold (a control character other than a line break in the proposal); and, in the student's names, the topic or a typed supervisor's name, a word (a run of letters) that mixes Latin and Cyrillic letters, adopted from `docs/domain.md`, so „CRM-система“ passes. The student can save and return until submitting. Afterwards the student may change only the supervisor, after a decline; other corrections are staff's (requirement 5). The application shows whether it is submitted, the supervisor's answer or that it is awaited, and the latest check's result, not staff's note.

3. **The supervisor's answer** (5.4). Submitting a thesis application emails the supervisor the student's name, F№, programme, topic and proposal (6.7 as amended), with two buttons, „Потвърждавам“ and „Не потвърждавам“. Each opens a page with an optional comment and a button that records the answer; opening a link records nothing (8.2). The answer, its comment (for staff only) and its time are recorded and never overwritten. The request and its reminders carry the same links, which work until an answer is recorded or the request is replaced, and afterwards only show the answer, if one was recorded. On a decline the student is told by email and on the application page, and choosing another supervisor sends a new request. If the relay refuses a message, nothing is recorded as sent and whoever caused it is told; a thesis application is submitted only once its request has gone. A command run by hand reminds a supervisor who has not answered three days after the request and three days after that reminder, at most twice, as settings (8.4); a second run on the same day sends nothing more.

4. **The student's forms** (5.5). After submitting, the student downloads the заявление-декларация, and for a thesis Приложение 2, as Word files filled from the records, the заявление dated with the submission date and the proposal keeping its line breaks. Everything else the records do not hold stays blank, to be filled by hand, Приложение 2's дата на предаване included, and no template prints a year copied from the samples.

5. **Staff** (6.5, 2.4, 5.6). Staff register with an email address, a username and a password, with no emailed code, and sign in with the username or email address and the password, never with a link or code. A new account other than the owner's sees nothing until the owner approves it on the owner's page, where the owner also resets staff passwords without email (8.1). The owner's account is the one a setting names, and the service does not start if no account has that name; only that account reaches the owner's page, and a host command resets its password. Staff see a table of submitted applications with the columns student, F№, programme, type, topic, supervisor, answer and check, in which those waiting for the supervisor, for a check or, once confirmed and passed, for their first report stand out at a glance (7.3). They can open any application and see every field entered and the answer with its comment and time. They record each check against the university's databases: passed or not passed, a note, who checked and when; the latest check counts. They may correct what a student entered (3.3, `CLAUDE.md` "Protect and verify"); the earlier value is kept, with who corrected it and when. A staff change of the supervisor or the supervisor's address replaces the request with a new one; an answer already recorded stays with the earlier request.

6. **The owner's lists** (2.6). Academic titles, each written one way; professors with a title from that list and an email address; programmes with degree, form of study and faculty; faculties with their dean. They start from `docs/domain.md`, with each programme's faculty as the owner confirmed (ДО to ФДЕНО, РО bachelor's to БФ, РО master's to МФ). They are files that the owner edits, kept in the data directory; one that cannot be read, or lacks an entry an application uses, stops the service from starting, naming the file and line. The application offers the student what they hold, and every email and document takes names and titles from them, apart from what is typed for a professor from outside the department.

7. **The topic-approval report** (5.7, 7.5). Staff generate it for one faculty and programme at a time, as a Word file in the layout that `docs/domain.md` records: addressed to that faculty's dean; introduced by „Студенти от {БП/МП} „{programme}“, изпълнили условията за допускане до дипломиране с {бакалавърска/магистърска} теза:“; listing every thesis application of that programme whose supervisor confirmed and whose latest check passed; columns №, F№, Име, Тема, Научен ръководител and an empty Рецензент; dated the day it is generated (7.4); Изх. №, its year and the signatures blank. Each generated report is kept in the data directory with its date and students; generating a later report never removes an earlier one.

## Required proof

1. Each rule tested over generated inputs of any length and in any characters, mixed scripts included:
   - which faculty and dean a programme leads to;
   - which applications a report lists and leaves out, by programme, type, answer and latest check, and that earlier reports are kept (requirement 7);
   - what each answer, a staff change of the supervisor and the staff check do to an application, and what its page then shows the student;
   - which supervisors a reminder run selects for given days and count, runs repeated on one day included;
   - opening a sign-in link spends nothing; „Влез“ or the code signs the student in once; a used or expired link or code is refused; requests per address and per source are rate-limited; links and codes are stored hashed;
   - opening a supervisor's link records nothing; its page's button records the answer, comment and time; the links of the request and its reminders work until then or until the request is replaced, and afterwards only show the answer, if one was recorded;
   - checks and corrections are recorded as requirement 5 states, each keeping the value it replaces;
   - what requirement 2 stores and refuses;
   - a list file with an error, or lacking an entry an application uses, stops the start with file and line named.

2. Every Word file, the заявление-декларация for each graduation type, Приложение 2 and the report, checked twice: by content, read back from the .docx over generated names, topics and lists, so that its wording, dates, names and titles are as requirements 4, 6 and 7 set out, each student's data is in the right cells, the columns are in order and the cells left blank are empty; and by eye, rendered to an image or opened in Word. No template holds a student row or a year copied from a sample.

3. Each role tested for what it must not see:
   - a student reaches only their own application, the same at every sign-in, and changes it only as requirement 2 allows; never another student's application, a staff page or the owner's page;
   - a supervisor's link reaches only its own request;
   - an account not yet approved, and a signed-out visitor, see no student data; only the owner's account reaches the owner's page, and a setting naming no account stops the start.

4. All mail through a fake relay, checking the recipient and content of every message: the sign-in link and code; the request to a listed and to a typed supervisor, with the contents requirement 3 lists; the decline notice; the new request after choosing again and after a staff change; the reminders; and each of these refused by the relay, with what is then shown. Mail mode "owner" delivers every message to the owner's address with the intended recipient at its top, and mail mode "console" prints it; so does a run with no mode set, and none of the three sends to the intended recipient; all three are tested, so no test or development run sends to anyone else (6.9).

5. Browser tests, at phone width (390 px) for students and supervisors:
   - a thesis application from the link's „Влез“ page to download, with the first tab's reminder shown, the professors and programmes offered read from the list files and no field asked twice;
   - a state-exam application with no second tab, its page then showing "submitted";
   - a supervisor's answer through each button, with a comment, the answer then shown to the student and in the staff table;
   - a staff account registered, approved on the owner's page, and signed in by username and by email address with the password; a wrong password refused and the password stored with a slow salted hash; a password reset on the owner's page, after which only the new one works, and the owner's by the host command; the table, one opened application and a check recorded as requirement 5 describes, no unsubmitted application shown and each kind of waiting marked.

   The whole set of tests passes on Python 3.9 and on Python 3.12.

## Constraints and exclusions

Constitution section 6, with 6.7 as amended, and `CLAUDE.md` apply in full, except what DEFERRED lists. The installation starts empty, so there is no earlier behaviour to preserve.

Stop and report if a requirement needs an answer to an open decision, a service other than the SMTP relay, or a layout the samples do not support.

DEFERRED: the graduation report and what only it needs (sessions, commission, reviewers, outgoing number; 8.5, 8.6); keeping students already reported out of a later report, which until then lists them again; importing the registry table; deployment to the laptop-server, with HTTPS, mail to the intended recipients and the reminder timer; real students (8.7); the Programme Council протокол; electronic signatures; changing a recorded answer.

## Completion

Completion requires requirements 1 to 7 met, proofs 1 to 5 passing with no unresolved blocker, and the approvals and the owner's authorization that `CLAUDE.md` "Milestone workflow" requires. Then the owner, on the Mac, with mail mode "owner" set, a professors list of invented names in the data directory, the owner's account set and a staff account approved on the owner's page:
1. completes one thesis application in a phone-sized window;
2. answers as the supervisor, through the buttons of the request that arrives in the owner's own mailbox;
3. checks the application as staff;
4. as the student, downloads the two forms;
5. as staff, generates the topic-approval report and opens it in Word.

Owner acceptance closes the milestone.
