# Milestone 2: the pilot on the laptop-server

## 2026-10-10 — Started without a NOW.md, on the owner's decision

- **Request** (owner, verbatim): "Milestone 2, the pilot on the laptop-server: the app runs as a service behind the Cloudflare Tunnel at a visiometrica.com address, with HTTPS and a fresh database (not ~/superassistant-data)"; "generally we will mirror the CourseBench configuratio routine".
- **Plan:** none. Owner, verbatim: "do we really need a now file; just guide me through necessary steps to achieve the goals of this milestone". `NOW.md` stays milestone 1's frozen `65d0ad16…`.
- **Scope:** what Opus 5.5 showed the owner as REQUIRED NOW on 10 October:
  - the visitor's address behind the tunnel;
  - a sending mode;
  - host commands reading the settings file;
  - hosted start refusals, `/healthz`, a mail test and a startup line;
  - the reminder timer;
  - the deployment files.
  It also includes Codex's migration race, which the timer's second process makes live.
- **Owner decisions** (verbatim answers):
  - address "use the nbu-superassistant";
  - code folder "apps/nbu-superassistant";
  - records "Yes, ~/nbu-superassistant-data (Recommended)";
  - service "Rename to "nbu-superassistant"" (`1b3e254`);
  - sender "Yes, nbu-superassistant@visiometrica.com (Recommended)";
  - mail "Real recipients from day one", whose option limited the pilot, until 8.7, to "invented students, testers who agreed";
  - reminders "Daily at 09:00, calendar days (Recommended)";
  - the Resend key CourseBench uses.
- **Review:** Opus 5.5 implements; Codex reviews the code (`CLAUDE_1.md`).
- **DEFERRED** (Opus 5.5's proposal; the owner did not comment):
  - limits on staff sign-in;
  - the typed-supervisor message;
  - DMARC;
  - a paid Resend plan.

## 2026-10-10 — Implemented; review target `bdb42be` for Codex

- **Implementer:** Opus 5.5 (`claude-opus-5-5`).
  - One round of three delegated builders, in isolated worktrees, merged in `0534b19`.
  - One round of four read-only reviewers on `0534b19`. Every finding was reproduced and fixed in `bdb42be`, each fix with a regression shown to fail on `0534b19`.
- **Changed:**
  - mail mode `send`;
  - the visitor's address from `SUPERASSISTANT_CLIENT_IP_HEADER`, an IPv6 visitor counted by its /64;
  - `.env.production`, read by `wsgi.py` and the host commands, which refuse a value systemd would read differently;
  - refusals for a hosted installation;
  - `/healthz`, `mail-test` and a startup line;
  - errors logged by route, never by address;
  - reminders by calendar day in Sofia;
  - migrations under a lock;
  - the service and the 09:00 timer (Europe/Sofia), `.env.production.example` and `docs/deployment.md`.
- **Accepted behaviour changed on purpose:**
  - a mode sends to the intended recipient: `test_no_mode_sends_to_the_intended_recipient` is replaced, and its assertions are kept;
  - reminders count calendar days.
- **Checks on `bdb42be`** (Opus 5.5):
  - Python 3.9.6 and 3.12.14: 211 passed and browser 7 passed on each.
  - gunicorn 26.2, with the unit's arguments, answered `/healthz`.
  - smtp.resend.com offers SMTPUTF8.
- **Open for the owner:** anyone who reaches the public address can make the service mail any address. How the pilot's limit is kept until 8.7 is undecided.
- **Outstanding:** Codex's review, the push and the install.

## 2026-10-10 — The pilot gets no gate; two lists will lock it down later

- **Supersedes** the "Open for the owner" line of the entry above.
- **Owner** (verbatim): "there is no way we are building the possibility that a user can sign in, select a role 'advisor' and be one"; "we will create roles that an admin (me) can assign"; "I will provide a list of emails … the members of the list (my faculty) = possible advisors, also a freeform will enable the selection of other advisoer, eg members of other departments (utill we add them) and even professors from other universities"; "at some point we will lock this down further when i add the list of all student numbers and mails"; "both list are a future taks, of course".
- **So:** nothing gates the pilot in this milestone. The code already matches the design: supervisors have no accounts, staff accounts need the owner's approval, and a supervisor is chosen from the professors list or typed.
- **DEFERRED** (future tasks, owner):
  - the faculty list of possible supervisors;
  - the list of students' faculty numbers and addresses.
- **Change:** `docs/deployment.md` only, worded to match.

## 2026-10-10 — Deployed on the laptop-server

- **Code:** `4ed7ec7`. Its code is the same as `bdb42be`.
  - Pushed to the owner's new public repository `quantumjazz/NBU-SuperAssistant`.
  - Cloned to `/home/victor/apps/nbu-superassistant`.
- **Laptop checks** (Opus 5.5, over ssh):
  - On Python 3.12.3, 211 passed. The browser tests were not run there.
  - The records folder `/home/victor/nbu-superassistant-data` (mode 700) is new.
  - The owner's list of 22 professors is accepted by the start's list check.
- **Settings:** `.env.production` (mode 600, ignored by git). The Resend key was copied on the laptop from CourseBench's file and never displayed.
- **Owner's sudo steps:**
  - The service and timer units were installed and enabled.
  - The account `victor` was registered through `ssh -L` before the address was public, then named owner.
  - A tunnel line was added; `cloudflared ingress validate` passed. The earlier config is kept as `config.yml.bak-20261010-224504`.
  - A DNS CNAME was created and cloudflared restarted.
- **Evidence:**
  - `https://nbu-superassistant.visiometrica.com/healthz` answers ok.
  - The session cookie is `Secure; HttpOnly; SameSite=Lax`.
  - `/owner` and `/application` redirect a visitor who is not signed in.
  - The start line names the https address, mail `send` through smtp.resend.com:587 and the CF-Connecting-IP header.
  - `mail-test` to vavramov@nbu.bg was accepted and reached the inbox (the owner's screenshot).
  - CourseBench answers 200.
  - The timer's next run is 11 October at 09:00 EEST.
- **Outstanding:**
  - Codex's review of `4ed7ec7`;
  - the owner's hands-on checks.

## 2026-10-10 — The live pilot checked; Приложение 2 fixed in `e3b51b9`

- **The owner's test:** one thesis application, with the owner as the student. The supervisor is доц. д-р Екатерина Цветанова-Георгиева; her request was sent at 22:54. `victor` recorded the staff check as passed at 22:57. Her answer is pending. Owner (verbatim): "everything looks good; check yourself".
- **Opus 5.5's read-only check** (two delegated agents, one round): the records, the mail and the logs are as designed.
  - The sign-in was spent once and stored hashed.
  - The request went to the address in the professors list.
  - The per-source limit was keyed by Cloudflare's visitor address, not 127.0.0.1.
  - The journal holds no error and no token.
  - If she does not answer, the reminders go on 13 and 16 October at 09:00.
- **Found:** rendered through Word, Приложение 2 put the supervisor's slot at the left edge of the next line. This is a milestone-1 template defect.
- **Fixed in `e3b51b9`:**
  - The year is replaced by dots of equal width.
  - A regression test pins the line's width.
  - Checked by eye through Word against the sample.
  - Python 3.9.6 and 3.12.14: 212 passed and browser 7 passed.
  - Pushed. The laptop pulled it.
- **DEFERRED until real students (8.7):** the sign-in limit of 10 an hour per visitor counts one public address, so students on one campus network would share it.
- **Outstanding:** Codex's review, now of `e3b51b9`; then the supervisor's answer and the report.

## 2026-10-11 — Codex's review of `e3b51b9`: M2-C1 disputed, M2-C2 and M2-C3 fixed in `c479104`

- **Review** (Codex, relayed by the owner): CHANGES REQUESTED at `e3b51b9`. The Приложение 2 fix is verified. The three findings:
  - M2-C1 asks that a carriage return be kept inside a settings-file value;
  - M2-C2 asks that a backup or restore stop every writer;
  - M2-C3 asks that no backup overwrite another, and that a restore keep the current records.
  - Codex's checks: 212 + 7 passed on each Python.
- **M2-C1, disputed with evidence:**
  - The host's systemd 255 was given Codex's line through a transient unit. The value it set was "re_FAKE_before", so a carriage return ends a line there.
  - The reader already matched that. The proposed change would have made it disagree.
  - The behaviour is kept, made explicit, and pinned by a test holding the file systemd was given.
- **M2-C2 and M2-C3, fixed in `docs/deployment.md`:**
  - Stop the timer, wait out a running reminder, stop the service.
  - Backups get per-second names, written under `noclobber` and `umask 077`.
  - A restore keeps the current records in a before-restore folder, and starts nothing after a failed step.
  - Both procedures were run from the doc's blocks on the laptop, against fake records.
- **Checks on `c479104`** (Opus 5.5): Python 3.9.6 and 3.12.14, 213 passed and browser 7 passed on each.
- **Outstanding:** Codex's review of `c479104`, covering M2-C1's evidence and the M2-C2 and M2-C3 fixes only.

## 2026-10-11 — Codex's re-review of `c479104`; M2-C3 fixed again in `9d34f5b`

- **Review** (Codex, relayed by the owner): CHANGES REQUESTED at `c479104`.
  - M2-C1 is withdrawn. Codex confirmed in systemd v255.4's parser that CR and LF both end a line.
  - M2-C2 is resolved.
  - M2-C3 stays open: after a partial unpacking, the documented `mv "$kept" …` nested the kept records inside the partial folder.
  - Codex's checks: 213 + 7 passed on each Python.
- **An independent adversarial check** (one delegated agent, 71 cases on the laptop, invented records in /tmp) passed Codex's guarded recovery. It broke the restore itself:
  - a retried or undone restore could start the service on a partial extraction;
  - a wrong archive could write over another folder in the home folder.
- **Fixed in `9d34f5b`** (`docs/deployment.md` only):
  - The restore unpacks only the records folder into a private staging folder. It moves the current records aside only once that succeeded and gave a real folder.
  - Codex's guarded sequence stays as the undo.
  - Backups are written as `.tgz.partial` and renamed only after `tar` succeeds.
- **Rerun of the 71 cases:**
  - every damaged or wrong archive left the current records in place and started nothing;
  - the retried and undone restores ended on the original records;
  - the other app's folder was untouched.
- **Residual:** a tar stream cut at a member boundary inside a valid gzip unpacks with status 0. The `.partial` naming keeps the doc's own backups from ever being such a file.
- **Outstanding:** Codex's review of `9d34f5b`.

## 2026-10-11 — Codex's re-review of `9d34f5b`; the undo quiesces, `aaf8fd2`

- **Review** (Codex, relayed by the owner): CHANGES REQUESTED at `9d34f5b`, M2-C3 only.
  - Verified: the staging, a retry after a failure, the refusal of a wrong archive, the folder checks and the `.partial` backups.
  - Open: after a successful restore, the undo moved both records folders while the service, the timer and a reminder run could still write.
- **Fixed in `aaf8fd2`** (`docs/deployment.md` only): after the `$kept` checks, the undo stops the timer, waits while a reminder run is under way, and stops the service before its first move. It restarts both only once the records are back. An absent `$kept` still does and stops nothing.
- **Verified on the laptop** with the doc's own blocks, invented records, real `tar` and `mv`, and stateful stubs for `sudo` and `systemctl`:
  - a restore, then a reminder run active for three polls, then the undo: both moves came at web, timer and reminder all inactive;
  - A came back, and B stayed whole in `failed-restore-…` (mode 700);
  - the undo repeated, and run in a new window, stopped and moved nothing;
  - 0 moves with a writer possibly running.
  - The 71-case harness gave the same outcome in every case.
- **Outstanding:** Codex's review of `aaf8fd2`.

## 2026-10-11 — Final code approved: `aaf8fd2`; ready for owner acceptance

- **Approvals of `aaf8fd2`:**
  - Codex APPROVED, relayed by the owner (verbatim): "APPROVED at aaf8fd2. M2-C3 is resolved. No further changes requested."
  - Opus 5.5 (`claude-opus-5-5`), the implementer, APPROVED the same commit.
- **Findings:**
  - M2-C1 was withdrawn by Codex, after systemd v255.4's own parser showed that CR ends a line.
  - M2-C2 was resolved at `c479104`.
  - M2-C3 was resolved at `aaf8fd2`.
- **Checks:**
  - Code and tests are unchanged since `c479104`, where 213 passed and browser 7 passed on Python 3.9.6 and 3.12.14, for Opus 5.5 and for Codex alike.
  - The documentation fixes were verified on the laptop with invented records, and Codex's focused checks confirmed them.
- **The live pilot** (Opus 5.5, read-only):
  - The reminder timer's first run, on 11 October at 09:00:06, sent 0 (none was due) and ended in success.
  - The service is active, with no error in its journal since 10 October 22:45, and `/healthz` answers ok.
- **Phase:** READY FOR OWNER ACCEPTANCE; the owner's acceptance is outstanding.
  - The owner's test of 10 October covered an application from a phone, the request to the supervisor, and a staff check.
  - The supervisor's answer and the topic-approval report wait on доц. д-р Екатерина Цветанова-Георгиева: her reminders go on 13 and 16 October. A staff change of supervisor would move them on.
- **DEFERRED:**
  - as listed on 10 October;
  - the sign-in limit's shared campus address (8.7).

## 2026-10-11 — COMPLETE: accepted by the owner

- **Owner acceptance** (verbatim): "I accept, push to github, pull to the laptop and I will do real world testing - the results - -> in another chat".
- **Accepted code:** `aaf8fd2`, approved by Codex and Opus 5.5 (the entry above), running at https://nbu-superassistant.visiometrica.com. Milestone 2 had no `NOW.md`, on the owner's waiver in this record's first entry.
- **Not seen before acceptance:** the supervisor's answer and the topic-approval report for the owner's test application. Both wait on the supervisor.
- **Next:** the owner's real-world testing, with the results in a new chat.
- **DEFERRED:**
  - limits on staff sign-in;
  - the typed-supervisor message;
  - DMARC and a paid Resend plan;
  - the sign-in limit's shared campus address;
  - the owner's student list and faculty list (future tasks);
  - roles the owner assigns.
- **Status:** COMPLETE.

## 2026-10-11 — Interface restyle, an owner-authorized task: code `c89c2d6` for Codex

- **Authorization** (the owner, quoted in the owner's brief to Opus 5.5): the interface was "cold, uninviting and rather crude". The owner chose Fable's preview "B with the system font, write the brief for Opus 5.5", and removed the global slide rule against cards and chips: "this comes from CourseBench and it's wrong". A task, not a milestone: no `NOW.md`.
- **Code:** `5129c3d` is Fable's `mockup.patch` (SHA-256 `133786b5…`) plus Opus 5.5's fixes. They follow from checking 66 invented-people states in Chromium and the Mac's WebKit:
  - the status sentences are true in every state;
  - Safari selects and iPhone focus zoom;
  - contrast, focus and number agreement;
  - long text wraps;
  - a `?v=` hash on the stylesheet link, because Cloudflare gives browsers `max-age=14400`.
  `c89c2d6` adds four follow-ups from two read-only verifiers (no blocker). No route, record, email or Word template changed.
- **Wording not yet seen by the owner:** STATUS_NEXT "awaited", DRAFT_LEAD and the count chips' plurals.
- **Checks:** 214 passed and 7 browser passed on Python 3.12.14 and 3.9.6. The new test fails on the mock-up's `?v=preview2`.
- **Not checked:** Safari's own window and the iOS Simulator. No screen-recording permission; Xcode's licence unaccepted.
- **Outstanding:** Codex's review; the push and the documented update; every live page opened; the owner's acceptance on a phone and in Safari.
- **DEFERRED** (these predate the restyle): the answer page's title and heading in some states; the choose-again mail-failure message; "одобрена".

## 2026-10-11 — Interface restyle: `c89c2d6` approved; pushed for the laptop update

- **Approvals of `c89c2d6`** (range `a0c7e2b..c89c2d6`):
  - Codex APPROVED, relayed by the owner (verbatim): "APPROVED — interface restyle at `c89c2d6`, covering `a0c7e2b..c89c2d6`. No R-C findings or required changes."
  - Opus 5.5 (`claude-opus-5-5`), the implementer, APPROVED the same commit.
- **Codex's checks**, in scratch copies:
  - 214 passed and 7 browser passed on Python 3.9.6 and 3.12.14;
  - the 66 states rendered in Chromium and the Mac's WebKit;
  - long-token and 16px touch-field checks.
- **Not checked by either agent:** Safari's own window and the iOS Simulator.
- **Outstanding:** the documented update on the laptop (pull, restart, `/healthz`); every live page opened; the owner's acceptance on a phone and in Safari.

## 2026-10-11 — Interface restyle COMPLETE: accepted by the owner

- **Owner acceptance** (verbatim): "I accept, the pages look fine on phone and Safari".
- **Deployed:** GitHub `main` and the laptop are at `d09a221`. The code is `c89c2d6`, approved by Codex and Opus 5.5. The owner ran the documented restart, and `/healthz` answered `{"status":"ok"}`.
- **Live check** (Opus 5.5, built-in browser, read-only):
  - `/`, `/staff/sign-in`, `/staff/register`, an unknown `/answer/…` link and `/healthz` render the new templates.
  - The stylesheet link is `?v=148d6ee5e31c`, the SHA-256 prefix of `style.css` at `c89c2d6`.
  - No development banner shows (mode send).
  - The owner checked the signed-in pages.
- **Open owner questions:**
  - whether to commit `docs/design/ui-mockup-2026-10-11/` as the design record;
  - whether this task's record stays in this file.
  The three new sentences were live at acceptance, and no change was asked.
- **DEFERRED:** as in the entry for `c89c2d6`. In addition, an iPad with a trackpad may get 15px fields.
- **Status:** COMPLETE.

## 2026-10-12 — Confirmation notice and the ФДЕНО address line, an owner-authorized task: code `0641e0f` for Codex

- **Authorization** (the owner, quoted in Fable's brief to Opus 5.5): "I think that students are not notified when the proposed advisor decides on their application". On Fable's proposal to fix the confirmation email and the ФДЕНО address line before milestone 3: "you are correct, go ahead". The ФДЕНО report "will read exatly like other reports, but with this "ДОЦ. Д-Р ВЕНЦИСЛАВ ДЖАМБАЗОВ / ДЕКАН НА ФДЕНО"". A task, not a milestone.
- **Code `0641e0f`** (range `617aa11..0641e0f`):
  - a recorded confirmation emails the student, as a decline does: after the answer, under the same "notice" bound. A refusal keeps the answer, and the page says so;
  - the starter list names ФДЕНО „ФДЕНО“; БФ and МФ stay in full.
- **Tests:** the only existing assertion changed is the starter name in `tests/test_foundation.py`, as the brief directs. Five new tests fail without the change.
- **Checks:** 219 passed and 7 browser passed on Python 3.9.6 and 3.12.14. A ФДЕНО and a БФ report were rendered and looked at. Four read-only subagent checks found one vacuous assertion, now removed.
- **Outstanding:** Codex's review; the push; the laptop's `faculties.csv` cell, on the owner's yes; the update; a live confirmation reaching the test student; the owner's acceptance.
- **DEFERRED** (predates this task): the `supervision.py` docstring says every message is sent inside its recording transaction; neither notice is.

## 2026-10-12 — Confirmation notice and the ФДЕНО address line: `0641e0f` approved; pushed for the laptop update

- **Approvals of `0641e0f`** (range `617aa11..0641e0f`):
  - Codex APPROVED, relayed by the owner (verbatim): "APPROVED — code `0641e0f`, range `617aa11..0641e0f`. No code changes required."
  - Opus 5.5 (`claude-opus-5-5`), the implementer, APPROVED the same commit.
- **Codex's checks**, in a scratch copy:
  - 219 passed and 7 browser passed on Python 3.9.6 and 3.12.14;
  - one notice per recorded confirmation, none for a duplicate or replaced link; a relay or throttle failure keeps the answer and shows the notice;
  - the three faculties' reports generated, read back and looked at;
  - an existing `faculties.csv` untouched by start and restart.
- **Correction**, found by Codex. It supersedes "Five new tests fail without the change" in the entry for `0641e0f`: three of the five new cases fail without the change, namely the two confirmation flow tests and the УБП-ДО report case. The БФ and МФ report cases are guards that also pass on `617aa11`.
- **Outstanding:** the laptop's `faculties.csv` cell, on the owner's yes; the documented update and the owner's restart; a live confirmation reaching the test student; the owner's acceptance.

## 2026-10-13 — Confirmation notice and the ФДЕНО address line: deployed; docstring `14e8580` for Codex

- **Deployed:** the laptop is at `abf31dd`.
  - Line 4 of its `faculties.csv` now reads `ФДЕНО,ФДЕНО,доц. д-р,Венцислав Джамбазов`, changed on the owner's "yes, change line 4". The old file is kept beside it as `faculties.csv.2026-10-13`.
  - The owner restarted the service at 09:50:47, after the 09:00 reminder run, and `/healthz` answered `{"status":"ok"}`. The public pages render.
- **Docstring `14e8580`** (range `abf31dd..14e8580`), on the owner's "address the second deferred item now": the `supervision.py` docstring now says that requests and reminders are sent inside their transaction and both notices are sent after the answer's. Docstring only. 219 passed and 7 browser passed on Python 3.9.6 and 3.12.14. This resolves the DEFERRED docstring item.
- **Outstanding:** Codex's review of `14e8580`; a live confirmation reaching the test student; the owner's acceptance.
- **Moved to a new thread** by the owner: the answer page's title for an invalid link, and the owner's new ideas.

## 2026-10-13 — Docstring `14e8580` approved; pushed and pulled to the laptop

- **Approvals of `14e8580`** (range `abf31dd..14e8580`):
  - Codex APPROVED, relayed by the owner (verbatim): "APPROVED — 14e8580, range abf31dd..14e8580. No changes required."
  - Opus 5.5 (`claude-opus-5-5`), the implementer, APPROVED the same commit.
- **Codex's checks**, in a scratch copy, on Python 3.9.6 and 3.12.14: valid syntax, and the executable code is identical outside the module docstring. The full suites were not repeated in that pass. Opus 5.5's run on `14e8580`: 219 passed and 7 browser passed on both.
- **Deployed:** this entry is pushed and pulled to the laptop. A docstring needs no restart.
- **Outstanding:** a live confirmation reaching the test student; the owner's acceptance; then the completion entry.

## 2026-10-13 — The task before milestone 3: code `4e83744` for Codex

- **Authorization:** the owner's "Scope: I agree" and "hardcode “F” so students enter only the numbers", 13 October 2026 (`milestone-3.md`).
- **Code `4e83744`** (range `b756685..4e83744`): the brief's five changes.
- **New wording:** „Молба за научно ръководство“; DECLARE_CREDITS, the form's sentence; „Отбележете това поле, за да подадете заявлението.“; „Въведете само цифрите на факултетния номер.“; „Код“, „Кредити“, „Код на програмата“, „Декларира покрити кредити“, „да“, „—“; „Изтрий“, „Изтриване на доклад“, „Изтриването премахва файла и записа на доклада. Изброените в него студенти отново чакат доклад.“, „Изтрий доклада“, „Докладът е изтрит.“, „Изтрити доклади“, „Изтрит“.
- **New tests failing with their change reverted:** answer page 3 of 5 (open, recorded are guards); declaration 5 of 8 (another student, type correction, заявление are guards); F№ 8/8; programmes 11/11; deletion 5/5.
- **Adjusted fixtures:** the brief's, plus `thesis_data` and the browser's F400001/F400002; unchanged after checking: `test_application_flow.py` 409–420, `test_documents.py` 76–81 and 307, browser 211.
- **Programmes, for the owner:** BSNADM01, BSNADM04, BSNBUB04, BSNDIU01, BSNTUR01, BSNDIT01, BSNDIT04, MSNADM21, MSNALH03, MSNHRB05, MSNHRE08, MSNMBA01, MSNMBA12, MSNMBA81, MSNMBA80, MSNSMQ11, MSNSMQ09.
- **Checks:** 256 passed, 7 browser passed on Python 3.9.6 and 3.12.14; two Word-rendered reports and tab 1 at 390 px looked at.
- **Laptop, after the owner's yes to the list:** pull per "Updating", no restart; copy the 17-row list over `programmes.csv`, keeping `programmes.csv.<date>`; restart; `/healthz`. That start records the old codes' moves as the owner's corrections. Likewise the Mac.
- **Outstanding:** Codex's review; the owner's yes; the update; acceptance.

## 2026-10-14 — The task before milestone 3: Codex's review of `4e83744`; fix `42a25f4` for Codex

- **Codex, on `4e83744`** (range `b756685..4e83744`, record `53f2cc2`), relayed by the owner: CHANGES REQUESTED, one finding, T13-C1 [P2]: `reports.delete` removed the file before COMMIT; a real reader lock makes COMMIT fail, the rows roll back, and the kept report's download returns 404. Codex also verified the tests on both Pythons, the recorded reversion counts, the mapping done once by two simultaneous starts, and the laptop ordering: "No other required changes found."
- **Fix** (range `53f2cc2..42a25f4`): `8560b14` removes the file only after the deletion commits; a failed transaction, COMMIT included, is rolled back at once and the file stays. `42a25f4` is test only.
- **Trade-off, to accept knowingly:** after the commit the deletion stands; a removal failure other than a missing file is raised and leaves that file.
- **Tests:** a regression with a real reader lock (report, student row, file and download remain, nothing logged; fails on `4e83744` at the file check); a failure inside the transaction surfaces as itself; the unlink test adjusted to the new order.
- **Checks:** 258 passed and 7 browser passed on Python 3.9.6 and 3.12.14; Codex's script, 30 s timeout: file and rows kept. Three read-only verifiers (web route on both Pythons, adversarial review, five mutations): holds.
- **Outstanding:** Codex's review of the fix; the owner's yes to replacing `programmes.csv`; the update; acceptance.

## 2026-10-14 — The task before milestone 3: Codex's review of `42a25f4`; fix `dfceedb` for Codex

- **Codex, on `42a25f4`** (range `53f2cc2..42a25f4`, record `b249a6e`), relayed by the owner: CHANGES REQUESTED; "T13-C1’s original commit-lock failure is fixed." T13-C2 [P2]: a removal failing after the commit (real folder rights) deleted the rows and logged the deletion but left the file; download and retry returned 404. "`b249a6e` identifies the trade-off but records no owner acceptance."
- **Correction:** supersedes `b249a6e`'s "Trade-off, to accept knowingly"; none remains.
- **Fix** (range `42a25f4..dfceedb`): a deletion is whole or nothing. `8e1d259`: before the COMMIT the file is moved aside (`.deleting`), needing the rights removal needs; any failure puts it back, then rolls back: report, rows and file stay, nothing is logged, retry works. Every start tidies the reports folder under the write lock. `dfceedb`: the file goes back only while its report is kept.
- **Tests:** real folder rights through the page; order of move, COMMIT and put-back; a start finishing a stopped deletion; the tidy's lock; SQLite's own rollback. Each fails on `42a25f4` or a mutation; the T13-C1 regression still passes.
- **Checks:** 266 passed and 7 browser passed on Python 3.9.6 and 3.12.14; Codex's two scripts: rows and file kept, retry deletes. Three read-only verifiers at `8e1d259`, killed processes included: holds, one test gap, closed in `dfceedb`.
- **Outstanding:** Codex's review; the owner's yes to replacing `programmes.csv`; the update; acceptance.

## 2026-10-14 — The task before milestone 3: Codex's review of `dfceedb`; fix `f37fcf4` for Codex

- **Codex, on `dfceedb`** (range `42a25f4..dfceedb`, record `a569638`), relayed by the owner: CHANGES REQUESTED; "The original T13-C1 and T13-C2 reproductions now pass." T13-C3 [P2]: after an automatic rollback the report check and the file's restoration were unlocked; a second deletion committing between them left rows 0/0, one deletion logged, and the original file present, untouched by `tidy`. Codex also verified 266 and 7 browser tests on both Pythons.
- **Fix `f37fcf4`** (range `a569638..f37fcf4`): once the deletion's transaction has ended without its ROLLBACK, the write lock is taken again before the records are read and held until the file is settled: back while the report is kept, removed once it is not. `tidy` settles by the same rule.
- **Tests:** a deterministic two-connection regression (hooks on the file moves), failing on `dfceedb`; the "committed, then an error" case now expects the file gone at once; the order test pins one held lock. Every mutation tried, including the unlocked settle, fails a test on both Pythons.
- **Checks:** 267 passed and 7 browser passed on Python 3.9.6 and 3.12.14. Codex's scripts: folder rights and the 30 s reader lock keep report, rows and file; the race script now finds the second deletion held off by the lock, the report kept.
- **Outstanding:** Codex's review; the owner's yes to replacing `programmes.csv`; the update; acceptance.

## 2026-10-14 — The task before milestone 3: `f37fcf4` approved

- **Approvals of `f37fcf4`** (range `a569638..f37fcf4`, record `632bf94`):
  - Codex APPROVED, relayed by the owner (verbatim): "APPROVED — `f37fcf4`, range `a569638..f37fcf4`, record `632bf94`. T13-C3 is resolved; T13-C1 and T13-C2 remain resolved. No further changes requested."
  - Opus 5.5 (`claude-opus-5-5`), the implementer, APPROVED the same commit.
- **The task's code**, `b756685..f37fcf4`: `4e83744`, the five changes, in which Codex found no other required change; then the report-deletion fixes `8560b14` and `42a25f4` (T13-C1), `8e1d259` and `dfceedb` (T13-C2), `f37fcf4` (T13-C3).
- **Codex's checks**, on Python 3.9.6 and 3.12.14:
  - 267 passed and 7 browser passed, no skips;
  - the concurrency regression 10 of 10 on each, failing on `dfceedb` and the unlocked mutation; all nine reversion and mutation checks detected;
  - a folder refusing changes keeps the download and allows retry; the 30 s reader lock keeps rows and file;
  - settling and start-up tidying keep kept reports' files and remove deleted ones, under the write lock.
  Automatic rollback is simulated in the concurrency test; its competing thread uses a real connection.
- **Not pushed:** GitHub and the laptop are at `b756685`.
- **Outstanding:** the owner's yes to replacing the laptop's `programmes.csv`; the push and the laptop update in the recorded order; the owner's acceptance, with the new wording and the 17 programmes (entry for `4e83744`).
