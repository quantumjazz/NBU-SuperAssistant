# CONSTITUTION — NBU-SuperAssistant

## 1. Purpose

NBU-SuperAssistant runs the graduation paperwork of the Programme Council of department „Администрация и управление“ at New Bulgarian University (NBU). Through it:
- students apply online;
- supervisors confirm by email;
- administrative staff check the applications against the university's databases;
- the Programme Council's reports to the deans are produced as Word documents.

Every fact is entered once, by the person who knows it. Every document is generated from those records rather than retyped.

## 2. Goals

1. A student registers with an email address, signs in through a link sent to that address and completes one application in two parts:
   - the заявление-декларация;
   - for a thesis, the thesis proposal (Приложение 2).
2. A student who chooses a thesis names a supervisor. The supervisor is asked by email to confirm or decline, needs no account, and the answer is recorded with the application.
3. The student receives the application pre-filled as Word documents to print and sign.
4. Staff see in tables the applications, the data entered and the supervisors' answers. They record the checks they make against the university's databases and add the data only staff know.
5. Staff generate two reports as Word documents in the department's current layouts, ready for signature:
   - the topic-approval report (Доклад за утвърждаване на теми);
   - the graduation report (Доклад за държавен изпит / защита).
6. Names, academic titles, programmes and deans come from lists the owner maintains, so the same person or programme is written the same way in every document.

## 3. Anti-goals — what this must NEVER become

1. It is not the university's record of students, credits or grades. Staff check against the university's databases; NBU-SuperAssistant does not replace them.
2. It takes no decisions. A supervisor's confirmation records consent. The Programme Council, the Department Council and the deans decide, and signatures are given as the university requires.
3. It is not a document editor. A wrong document is corrected in the records and generated again.
4. It collects nothing the paperwork does not need.
5. It is not a general form builder, survey tool or learning platform.

## 4. Users

1. **Students** of the department's bachelor's and master's programmes, regular (РО) and distance (ДО), applying to graduate by thesis or by state exam. About 1,000 students study in the department; many will use a phone.
2. **Supervisors** (научни ръководители): professors of the department, chosen from a list, and occasionally a professor from outside it. They act only by email and need no account.
3. **Staff**: administrative staff who register as users. They work with the tables, check data and generate reports.
4. **The owner**: the Director of the Programme Council. The owner maintains the lists, approves staff accounts, signs the reports and operates the system.

## 5. The process

As designed by the owner on 9 October 2026:

1. Students are advised to talk to a prospective supervisor before applying. This happens outside the system, and the application reminds them of it.
2. The student enters an email address on the sign-in page. The email that arrives carries:
   - a link that opens a page with a „Влез“ button, leading straight to the application;
   - a six-digit code that does the same when typed on the sign-in page.

   ("Users will login using the emailed link as we discussed.")
3. The application has two tabs, following the two paper forms: "basically the 'zaiavlenie-za-diplomirane' as 1 tab maybe and second tab - the prilojenie-2". On the first tab the student chooses the graduation type.
   - For a state exam, "only names and faculty numbers are needed": no programme is chosen, the programme stays blank on the заявление-декларация, and there is no second tab. Staff enter the programme before the graduation report.
   - For a thesis, both tabs are filled in. The supervisor is chosen from the department's list of professors, or entered in the field for a professor from outside the department. A field that appears on both paper forms is asked once.
4. For a thesis, NBU-SuperAssistant emails the supervisor for confirmation, and the answer ("I approve", "I don't") appears in the staff tables.
   - The email has two buttons, „Потвърждавам“ and „Не потвърждавам“. Each opens a page with an optional comment and a button that records the answer; opening a link records nothing. Only staff see the comment.
   - If the supervisor declines, the student is told and may choose another supervisor.
   - A supervisor who has not answered receives a reminder three days after the request and another three days after that, at most two. The days and the number are settings. Running the reminder command twice in a day sends nothing extra.
5. The student receives the pre-filled заявление-декларация, and for a thesis Приложение 2, as Word files to print and sign. Whether this later becomes redundant is a future decision.
6. Staff check the data against the university's databases and record the result.
7. Staff generate the topic-approval report, in Word.
8. Later, staff generate the graduation report, in Word.

The baseline is that students enter their own data. A table of students' names and faculty numbers may be obtained later; it then serves to match and check what students entered. Its absence never blocks the process.

## 6. Hard constraints

1. The application is written in Python. The browser interface uses standard web technologies (HTML, CSS, JavaScript) served by the Python application.
2. It must remain practical for one academic to operate and maintain:
   - few dependencies;
   - no outside service other than an SMTP relay;
   - records that are backed up by copying files.
3. Where it runs:
   - During development, on the owner's computer.
   - For the pilot, on the owner's laptop-server behind its Cloudflare Tunnel, at a visiometrica.com address, as CourseBench runs.
   - Moving to another host later takes configuration, never code changes.
4. Students and supervisors need nothing but an email address. No Microsoft 365, university single sign-on or third-party login is required.
5. Staff accounts:
   - Staff register with an email address and a username, the way CourseBench accounts are made: "No tokens, only mails and usernames for registration".
   - Staff sign in with a username or email address and a password, never with an emailed link or code: "no tokens for admin login and development".
   - Only students sign in with the emailed link. No staff password, the owner's included, is reset through an emailed code or link.
   - A new account sees nothing until the owner approves it on the owner's page in the application. There the owner also sets a new password for a member of staff who has forgotten theirs, then tells them the new password; the application does not send it.
   - The owner's account is the one a setting on the host names, and needs no approval. The owner's own forgotten password is reset with a command on the host.
6. Security is proportionate to what is held: ordinary personal data, nothing in the special categories. It is never absent:
   - students' sign-in links and codes are single-use and expire;
   - sending mail is rate-limited;
   - passwords are stored with a slow salted hash;
   - the service runs over HTTPS.
7. Personal data covers names, faculty numbers, email addresses, telephone numbers, average grades, thesis topics and proposals, and supervisors' answers.
   - It is visible only to the student it belongs to, to staff and, for that student's request, to the supervisor asked. The request emailed to the supervisor carries the student's name, faculty number, programme, topic and proposal.
   - It lives on the host, outside the code repository.
   - Development and tests use invented people only.
8. Reports and the students' pre-filled forms are Word documents generated from the records in the department's layouts. Their templates are ordinary Word files that the owner can open and edit.
9. A development installation never emails anyone but the owner, and running it needs no tokens or keys.
10. The interface, the emails and the documents are in Bulgarian.

## 7. Success criteria

1. A student completes the application on a phone without help.
2. A supervisor confirms or declines from any mailbox, the university webmail included, with a button in the email and one on the page it opens.
3. Staff see at a glance which applications are waiting for a supervisor, a check or a report.
4. Both reports for a session are generated in seconds. Before signature they need only what the university adds by hand: the outgoing number and the signatures.
5. Generated documents contain no retyping errors. A person, title or programme is written identically everywhere, and the title, addressee and columns always match the type of report.

## 8. Not yet decided

Items 5 to 7 are still open. The owner decides them; until then, no code assumes an answer, and work that depends on one is marked `DEFERRED:` or waits. Items 1 to 4 were decided on 9 October 2026 and are no longer open; they keep their numbers so that references to 8.5 to 8.7 still hold.

1. Decided: how staff accounts are admitted. See 6.5.
2. Decided: how a supervisor answers. See 5.4.
3. Decided: a state-exam student chooses no programme. See 5.3.
4. Decided: when supervisors are reminded, and how often. See 5.4.
5. Who enters the graduation report's data, and when: the session's date, time and place, the commission, each thesis's reviewer and the outgoing number.
6. How applications are grouped into graduation sessions, and how a student moves to a later session.
7. NBU's agreement, a privacy notice and a rule for deleting old records, before real students use the pilot.

## 9. Amendments

| Date | Change | Reason |
| ----- | ------- | ------ |
| 09.10.2026 | 1 draft | Owner's design of 9 October 2026, drafted by Opus 5.5 |
| 09.10.2026 | 2 draft | Owner's answers of 9 October 2026, 22:00: pre-filled forms for students; told on decline and may choose again; reminders; two tabs; no tokens for staff sign-in and development; pilot on the laptop-server at a visiometrica.com address |
| 10.10.2026 | 3 draft | Owner's decisions of 9 October 2026 in the review of milestone 1's `NOW.md`: 8.1 "An owner page in the app", the owner's account named by a setting and its password reset on the host; 8.2 "Buttons, then a page", the comment for staff only; 8.3 "No, names and F№ only"; 8.4 three days, then three more, at most two; 6.7 "Everything in the email". Written into 4.4, 5.3, 5.4, 6.5, 6.7, 7.2 and 8 by Opus 5.5 |
