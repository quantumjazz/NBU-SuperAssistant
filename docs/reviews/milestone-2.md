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

## 2026-10-15 — A second task before milestone 3: the bin and the nightly copy

- **Owner's request** to Opus 5.5 (verbatim): "Users remove the entry (select reason - graduation, else), it goes to a 'bin' and deletion is confirmed as a second step." and "every day, say 00.00 hours the app outputs a csv with all students entries data and uploads to a cloud somewhere."
- **Conflicts reported first:** `CLAUDE.md` "Never delete … students' applications"; constitution 6.2 and 6.7.
- **Owner's answers** (verbatim): final deletion "Any staff member (Recommended)"; "Email it to you"; "30 days (Recommended)"; "change now".
- **Rules changed** by Opus 5.5 on "change now", uncommitted: `CLAUDE_1.md` `e8530f68…`; `CONSTITUTION.md` `8fe9b6ab…` (4.3, 5.15, 6.7, amendment row). `NOW.md` unchanged at `5bd1f853…`; the approved constitution `44380e66…` no longer stands, so Fable amends `NOW.md` and both approve again before milestone 3 is authorized.
- **Code** `f07aa5a..fb953f9`: `5f536ea` the bin, `snapshot` and its 00:00 timer; `fb953f9` fixes from a four-reviewer read-only verification: two crash windows, sign-in numbers, secure_delete, the note kept, Bulgarian redirects, Excel cells, the guide.
- **Checks:** 304 passed and 8 browser passed on Python 3.9.6 and 3.12.14; 11 of the new and changed tests fail on `5f536ea`, and on 3.12 the secure_delete test too; mutations: 18 of 20 caught at `5f536ea`, both survivors now tested; the CSV read back in Excel on the owner's Mac.
- **Not pushed.** Outstanding: Codex's review of `f07aa5a..fb953f9`; the laptop update with the new units; the owner's acceptance.

## 2026-10-15 — The second task: Codex's review of `fb953f9`; fix `d253071` for Codex

- **Codex, on `fb953f9`** (range `f07aa5a..fb953f9`, record `0e1f001`), relayed by the owner: CHANGES REQUESTED.
  - T15-C2 [P1]: a deletion let a request's number be given again; a link made from the number and the second alone reached a later student's request.
  - T15-C1 [P2]: the answer's read-back after its COMMIT could find the request deleted, and the page crashed.
  - T15-C3 [P2]: Excel turned a raw cell of 256 ones into 1,11E+255.
  
  Codex also verified 304 passed and 8 browser passed on both Pythons.
- **Fix `d253071`** (range `0e1f001..d253071`):
  - a random nonce in each new request's link, `requests.nonce` in schema 4, which no installation has yet; older requests keep their links;
  - the answer's read-back under its own lock;
  - one-line cells as joined Excel text values.
- **Tests:** the same-second case with another student and supervisor; deletion right after the answer's COMMIT; links and reminders of a request without a nonce; Codex's long cells. 16 cases fail on `fb953f9` on each Python.
- **Checks:** 321 passed and 8 browser passed on Python 3.9.6 and 3.12.14. Codex's script reproduced C1 and C2 before the fix. After it, the C1 hook finds no read after the COMMIT, and the C2 link gets 404 with nothing sent. In Excel, text import reproduced Codex's conversion; the new cells read back exactly.
- **Outstanding:** Codex's review of `0e1f001..d253071`; the laptop update; the owner's acceptance.

## 2026-10-15 — The second task: Codex's review of `d253071`; fix `2b5db84` for Codex

- **Codex, on `d253071`** (range `0e1f001..d253071`, record `c600127`), relayed by the owner: CHANGES REQUESTED. "T15-C1 and T15-C2 are resolved", on both Pythons, with links and reminders of schema-3 requests kept. T15-C3 stays open: a one-line cell too long for a formula was written raw when it held a letter, and Excel's Convert turned 8,200 zeros and „1e5“ into 100000.
- **Fix `2b5db84`** (range `c600127..2b5db84`): every cell is a formula joining only text values and line breaks (`CHAR(10)`, `CHAR(13)`). A cell too long for Excel's 8,192 units gets an apostrophe, whatever it holds. Excel's text import therefore no longer splits multi-line cells into rows either; found while verifying.
- **Tests:** Codex's case, multi-line cells and the earlier long ones; 9 cases fail on `d253071` on each Python.
- **Checks:** 326 passed and 8 browser passed on Python 3.9.6 and 3.12.14. In Excel on the owner's Mac, by AppleScript, opened and text-imported as UTF-8, semicolons, General: every value read back exactly, rows intact. Excel's formulas show the too-long cells are text (ISTEXT, LEN 8204) and a CR LF stays two characters. Codex's UI Convert route was not driven here.
- **Outstanding:** Codex's review of `c600127..2b5db84`; Fable's amendment of `NOW.md` (Fable unavailable for now); the laptop update; the owner's acceptance.

## 2026-10-15 — The second task: `2b5db84` approved

- **Approvals of `2b5db84`** (range `c600127..2b5db84`, record `c2713e1`):
  - Codex APPROVED, relayed by the owner (verbatim): "APPROVED — `2b5db84`, range `c600127..2b5db84`, record `c2713e1`. T15-C3 is resolved. T15-C1 and T15-C2 remain resolved. No further changes requested."
  - Opus 5.5 (`claude-opus-5-5`), the implementer, APPROVED the same commit.
- **The task's code**, `f07aa5a..2b5db84`:
  - `5f536ea`, the bin, the nightly copy and its timer;
  - `fb953f9`, fixes from the read-only verification;
  - `d253071` (T15-C1, T15-C2, T15-C3) and `2b5db84` (T15-C3), Codex's findings.
- **Codex's checks:**
  - 326 passed and 8 browser passed on Python 3.9.6 and 3.12.14, fake mail only.
  - A fresh `snapshot.to_bytes()` file opened in Excel through File > Open, UTF-8, semicolon, General: no conversion prompt; the scientific value stayed text, length 8,204 with its apostrophe; multi-line cells, CR LF and the next row intact.
  - Governance hashes match.
- **Known limits**, as Codex recorded them: "oversized values show an apostrophe; oversized multiline values can still split under Excel text import".
- **Not pushed:** GitHub and the laptop do not have this task.
- **Outstanding:**
  - the owner's yes to the push and the laptop update, which still includes the earlier task's `programmes.csv` replacement and now installing the nightly copy's units;
  - Fable's amendment of `NOW.md` and both approvals before milestone 3;
  - the owner's acceptance.

## 2026-10-15 — The second task: on the laptop; READY FOR OWNER ACCEPTANCE

- **Owner** (verbatim): "Push and update now (Recommended)".
- **Pushed and pulled:** GitHub and the laptop are at `581bb74`. A copy of the live database was taken first: `/home/victor/nbu-superassistant-pre-update-20261015-193832.sqlite3`, schema 3.
- **Found on the laptop, unrecorded here:** it was already at `f07aa5a`. `programmes.csv` has been the 17-row list (`556aa980…`) since 14 Oct 16:31, kept as `programmes.csv.2026-10-14`. The restart at 16:33 recorded the code mapping. This is the update the entries for the task of 13 October left outstanding.
- **The owner's sudo step:** copied the three units, then `daemon-reload`; restarted the service (19:40:22); enabled the snapshot timer.
- **Checks:**
  - `/healthz` ok publicly, and the start line is as before;
  - schema 4, with 3 applications kept, none in the bin;
  - 3 requests without a nonce, their links unchanged;
  - timers: the copy at 00:00 on 16 Oct, the reminders at 09:00.
- **The owner's checks:**
  - as staff, remove a test entry („Друго“), put it back, remove and delete it, then read the deletions;
  - after 00:00, receive „Копие на заявленията към 16.10.2026“ and open its CSV in Excel.
- **Outstanding:**
  - this acceptance;
  - Fable's `NOW.md` amendment and both approvals before milestone 3;
  - the earlier tasks' acceptances.

## 2026-10-15 — A third task before milestone 3: the bin for reports

- **Owner's request** to Opus 5.5 (verbatim): "Another small matter. Can the deleted  reports go first to the bin now and then be deleted?"
- **Owner's answers** to Opus 5.5's proposal (verbatim): a report's students wait again while it is in the bin, "Yes, right away (Recommended)"; "Change now (Recommended)".
- **Rules changed** by Opus 5.5, uncommitted: `CLAUDE_1.md` `a125c54e…`; `CONSTITUTION.md` `bdb5fe14…` (3.3, 4.3, 5 introduction, 5.7, 5.14, 5.15, a 15.10 row). They supersede in part the 13 October answer 5 and reading answer 4 in `milestone-3.md`: the report now disappears at the second step. `NOW.md` unchanged at `5bd1f853…`; Fable's pending amendment takes its report-deletion lines too.
- **Code** `51b1c2d..d39ce3c`:
  - `890adf7`: schema 5, adding only; removing and putting back write rows; only a report in the bin is deleted; a report in the bin is not kept; the bin lists reports and their deletions;
  - `d39ce3c`: test gaps and wording from a four-agent read-only verification (no blocker).
- **Checks:** 340 passed and 9 browser passed on Python 3.9.6 and 3.12.14; 14 faults re-applied in a scratch copy, each caught; a schema-4 folder made by `51b1c2d` upgraded, every row and file kept; pages screenshotted in Chromium (WebKit not installed).
- **Known limit:** code from before `890adf7` lists reports in the bin as kept.
- **Not pushed.** The update needs no new units or settings.
- **Outstanding:** Codex's review of `51b1c2d..d39ce3c`; Fable's amendment; the laptop update; the owner's acceptance.

## 2026-10-15 — The third task: `d39ce3c` approved

- **Approvals of `d39ce3c`** (range `51b1c2d..d39ce3c`, record `d95cbfe`):
  - Codex APPROVED, relayed by the owner (verbatim): "APPROVED: d39ce3c, range 51b1c2d..d39ce3c, record d95cbfe. No changes requested."
  - Opus 5.5 (`claude-opus-5-5`), the implementer, APPROVED the same commit.
- **Codex's checks**, as Codex reported them:
  - 340 passed and 9 browser passed on Python 3.9.6 and 3.12.14, the browser tests "after rerunning outside the execution sandbox";
  - the regression checks of T13-C1 to C3 and T15-C1 to C3 pass;
  - an actual `51b1c2d` data folder upgraded from schema 4 to 5, "preserving every existing row across 13 tables and all five non-database files"; earlier deletions stayed deleted;
  - the governance hashes match: `CLAUDE_1.md` `a125c54e…`, `CONSTITUTION.md` `bdb5fe14…`, `NOW.md` `5bd1f853…`.
- **Not pushed:** GitHub and the laptop are at `51b1c2d`.
- **Outstanding:**
  - the owner's yes to the push and the laptop update (no new units; schema 5 at the restart);
  - Fable's `NOW.md` amendment and both approvals before milestone 3;
  - the owner's acceptance of this task and of the earlier ones.

## 2026-10-15 — The third task: on the laptop; READY FOR OWNER ACCEPTANCE

- **Owner** (verbatim): "push and update the laptop", then "yes" after the restart.
- **Pushed and pulled:** GitHub and the laptop at `e829476`. A copy of the live database was taken first: `/home/victor/nbu-superassistant-pre-update-20261015-234831.sqlite3`, schema 4, 3 applications, no kept report, 1 report deletion, integrity ok. No unit, settings template or requirement changed.
- **The owner's sudo step:** the restart, 23:51:08.
- **Checks:**
  - `/healthz` ok publicly; gunicorn started with no error;
  - schema 5: `reports.binned_at` and `binned_by` added, `report_bin_events` empty; all 13 tables of the copy row for row the same in the live file;
  - timers: the nightly copy at 00:00 on 16 Oct, its first run on the new code; the reminders at 09:00.
- **The owner's checks:** as staff, generate a topic report, press „Премахни“ and see its students marked „чака доклад“; in „Кошче“ download it and press „Върни“; remove it again, press „Изтрий окончателно“, and read „Изтрити доклади“.
- **Outstanding:**
  - this acceptance, and the earlier tasks' acceptances;
  - Fable's `NOW.md` amendment and both approvals before milestone 3.

## 2026-10-16 — Four tasks COMPLETE: accepted by the owner

- **Owner acceptance** (verbatim): "I accept all the tasks; tests will be done tomorrow".
- **Accepted:**
  - the confirmation notice and the ФДЕНО address line: code `0641e0f`, docstring `14e8580`;
  - the task before milestone 3, `b756685..f37fcf4`: the answer page, the declaration tick, the F№ digits, the 17 programmes, and deleting a report, which the bin for reports has since replaced;
  - the bin for applications and the nightly copy, `f07aa5a..2b5db84`;
  - the bin for reports, `51b1c2d..d39ce3c`.
- **Not seen before acceptance:**
  - the owner's own checks on the live site, which the owner will do later ("tests will be done tomorrow");
  - a live confirmation reaching the test student.
  
  Their results, and any fault they find, go in a new entry.
- **Seen since the update:** the nightly copy ran at 00:00 on 16 October on the new code: `zaiavlenia-2026-10-16.csv`, 3 applications, sent to the owner's account address; the unit succeeded.
- **Live:** GitHub and the laptop at `cebfa27`, schema 5.
- **Status:** COMPLETE, all four.
- **Before milestone 3:**
  - Fable's `NOW.md` amendment for both bins, and Fable's and Opus 5.5's approval of the same version;
  - the owner's authorization.

  The governance changes stay uncommitted until then: `CLAUDE_1.md` `a125c54e…`, `CONSTITUTION.md` `bdb5fe14…`.

## 2026-10-16 — Fifth task: staff print each applicant's forms; for Codex's review

- **Owner** (verbatim): "can the staff safely print each Заявление-декларация (.docx) and Приложение of each applicant"; then "Heading: „Попълнени документи“ Line: „Не е нужно да отпечатвате и представяте документите: администрацията на департамента вече разполага с тях. Можете да ги изтеглите за справка.“ must be visible in each case; drop the "If students still sign in person.." version". To Opus 5.5's questions: "Yes, build it now (Recommended)", "Yes, like reports (Recommended)" (the bin), "Yes, fix both (Recommended)" (the templates).
- **Rules changed**, uncommitted: `CONSTITUTION.md` `66b60bd9…` (2.3, 4.3, 5 introduction, 5.5, a 16.10 row). `CLAUDE_1.md` `a125c54e…` and `NOW.md` `5bd1f853…` unchanged; Fable's amendment should name this task in `NOW.md`'s protected list.
- **Code** `7cc6abe..1845492`:
  - `473a99f`: the student's heading and line; staff routes for both forms (bin included, drafts not); templates rebuilt: no empty lines under the заявление's topic, its thesis heading kept with its box, Приложение 2 lines not stretched;
  - `1845492`: notes from a four-agent read-only verification (no blocker, no gap).
- **Checks:** 352 passed and 10 browser on Python 3.9.6 and 3.12.14; 15 mutations, each caught; templates rebuilt identical from the samples; Word renders before and after; pages in Chromium (WebKit not installed).
- **DEFERRED:** 5.3 quotes the tick as signing "the same sentence on paper"; who signs the printed заявление is the owner's question.
- **Not pushed. Outstanding:** Codex's review; the push and laptop update; the owner's acceptance.

## 2026-10-16 — Fifth task: `1845492` approved; accepted by the owner

- **Approvals of `1845492`** (range `7cc6abe..1845492`, record `fa8d551`):
  - Codex APPROVED, relayed by the owner (verbatim): "Codex APPROVED `1845492`, range `7cc6abe..1845492`, record `fa8d551`. No changes requested."
  - Opus 5.5 (`claude-opus-5-5`), the implementer, APPROVED the same commit.
- **Codex's checks**, as Codex reported them:
  - 352 passed and 10 Chromium browser tests passed on Python 3.9.6 and 3.12.14, the browser tests outside the sandbox with fake mail;
  - staff access, the bin, drafts, missing ids, non-thesis Приложение 2, corrected content, file names and both student cards as decided;
  - all three templates rebuilt, every ZIP part matching; no sample student text or year; `doklad_temi.docx` unchanged;
  - governance hashes match: `CLAUDE_1.md` `a125c54e…`, `CONSTITUTION.md` `66b60bd9…`, `NOW.md` `5bd1f853…`.
- **Owner acceptance** (verbatim): "I accept."
- **Not live:** GitHub and the laptop at `7cc6abe`. The update is a pull and a restart; no schema, unit or settings change.
- **Outstanding:**
  - the owner's yes to the push and the laptop update, then the owner's look at the student page in Safari;
  - DEFERRED: who signs the printed заявление (5.3's quote);
  - before milestone 3: Fable's `NOW.md` amendment naming this task with both bins, Fable's and Opus 5.5's approval of the same version, and the owner's authorization. The governance changes stay uncommitted until then.

## 2026-10-16 — Fifth task: live on the laptop

- **Owner** (verbatim): "Yes, push and update the laptop.", then "Done, I restarted the service."
- **Pushed and pulled:** GitHub and the laptop at `b49ec6b` (code `1845492`). A copy of the live database was taken first: `/home/victor/nbu-superassistant-pre-update-20261016-163949.sqlite3`, schema 5, 3 applications, 0 reports, integrity ok. No unit, setting, requirement or schema changed.
- **The owner's sudo step:** the restart, 16:41:38 EEST, after the pull.
- **Checks:**
  - `/healthz` ok on the laptop and publicly; no error in the service log;
  - signed out, `/staff/application/1/zaiavlenie.docx` and `/prilozhenie2.docx` lead to `/staff/sign-in`, so the new routes are served; the student's form address still leads to `/`;
  - schema 5 and 3 applications, as in the copy.
- **The owner's checks:** as a student, the card „Попълнени документи“ and its line, in Safari on a phone; as staff, „Документи на студента“ on an application's page, both files downloaded and opened in Word.
- **Status:** accepted by the owner ("I accept.") and live: COMPLETE. The owner's live checks, and any fault they find, go in a new entry.
- **Outstanding:** DEFERRED, who signs the printed заявление (5.3's quote); before milestone 3, Fable's `NOW.md` amendment naming this task with both bins, both approvals and the owner's authorization. The governance changes stay uncommitted until then.

## 2026-10-16 — Sixth task: the schedule of sessions; for Codex's review

- **Owner** (verbatim): "can we quickly build the timetable thing - it is very important"; to Opus 5.5's question, build all of requirement 4 of the milestone-3 `NOW.md` (`5bd1f853…`) now: "Yes, all of it (Recommended)".
- **Rules:** none changed. Constitution 5.13 (`66b60bd9…`, uncommitted) already states it; `CLAUDE_1.md` `a125c54e…` unchanged. Fable's `NOW.md` amendment should mark requirement 4 as built before the milestone.
- **Code** `e37ee7a..1267b47`:
  - `46fb451`: `sessions.csv`, a fifth list (the four 2026/2027 sessions, checked at start, written once at the first start after the update); on tab 1 the schedule, a choice among sessions dated today or later in Sofia, and the tick, both needed to submit; the student's page, the staff table and page show both, „—“ before; staff correct the session; the nightly copy holds both; schema 6;
  - `1267b47`: fixes from a four-agent read-only verification (staff table fits at 1280 px, „г.“ kept with its year, test gaps from 45 mutations).
- **Checks:** 396 passed and 11 browser tests on Python 3.9.6 and 3.12.14 (after `1267b47`'s last assertion, `tests/test_sessions.py` again on both); the pilot's first start reproduced 10 times with the reminder and the nightly copy starting together: the list written once. Pages in Chromium only (WebKit not installed).
- **Not pushed. Outstanding:** Codex's review; the owner's look at the wording; the push and laptop update; acceptance.

## 2026-10-16 — Sixth task: `1267b47` approved

- **Approvals of `1267b47`** (range `e37ee7a..1267b47`, record `5948c6c`):
  - Codex APPROVED, relayed by the owner (verbatim): "Codex APPROVED `1267b47`, range `e37ee7a..1267b47`, record `5948c6c`. No changes requested."
  - Opus 5.5 (`claude-opus-5-5`), the implementer, APPROVED the same commit.
- **Codex's checks**, as Codex reported them:
  - 396 passed and 11 Chromium browser tests on Python 3.9.6 and 3.12.14, with fake mail;
  - an `e37ee7a` data folder upgraded to schema 6, its records, lists and report file kept; only the three application columns added;
  - first starts concurrent, interrupted, after owner edits and with lists missing; the `sessions list` marker prevents writing the list again;
  - submission, Sofia's date boundaries, the tick's recording, staff corrections, access and earlier records meet requirement 4;
  - no sideways scrolling at 390 px, nor in the staff table at 1280 px;
  - governance hashes match: `CLAUDE_1.md` `a125c54e…`, `CONSTITUTION.md` `66b60bd9…`, `NOW.md` `5bd1f853…`.
- **Not live:** GitHub and the laptop at `e37ee7a`. The update migrates to schema 6 and writes `sessions.csv` at its first start; no unit or setting.
- **Outstanding:**
  - the owner's look at the wording (dates without a leading zero; „график: да“ under the session in the staff table) and acceptance;
  - the push and the laptop update;
  - before 27 January 2027, the next sessions added to `sessions.csv`;
  - before milestone 3, Fable's `NOW.md` amendment marking requirement 4 as built. The governance changes stay uncommitted until then.

## 2026-10-16 — Sixth task: accepted and live on the laptop; COMPLETE

- **Owner** (verbatim): "I accept. Yes, push and update the laptop.", then "Done, I restarted the service."
- **Pushed and pulled:** GitHub and the laptop at `6830e40` (code `1267b47`). A copy of the live database was taken first: `/home/victor/nbu-superassistant-pre-update-20261016-183130.sqlite3`, schema 5, 3 applications (1 in the bin), 1 report, integrity ok. No unit or setting changed.
- **The owner's sudo step:** the restart, 18:32:32 EEST, after the pull.
- **Checks:**
  - `/healthz` ok on the laptop and publicly; the start line in the log, mail mode send;
  - schema 6, integrity ok; the 3 applications and the report kept, the three new columns empty („—“);
  - `sessions.csv` written at that start with the four 2026/2027 sessions, `sessions list` recorded at 15:32:32 UTC;
  - signed out, `/application` leads to `/`; the new staff address answers.
- **The owner's checks:** as a student in Safari on a phone, the schedule, the session choice and the tick on tab 1; as staff, the session in the table and its correction.
- **Status:** accepted by the owner and live: COMPLETE. The owner's live checks, and any fault they find, go in a new entry.
- **Outstanding:** before 27 January 2027, the next sessions in `sessions.csv`; before milestone 3, Fable's `NOW.md` amendment marking requirement 4 as built. The governance changes stay uncommitted until then.

## 2026-10-23 — Seventh task: unsubmitted applications in the nightly copy; for Codex's review

- **Owner** (verbatim): "can you ensure the daily snapshot includes all student's records (eg Заявления)?"; told the copy held all 10 submitted applications but not 4 unsubmitted ones nor the history of checks and corrections, the owner chose "Unsubmitted too (Recommended)". The history was not chosen.
- **Rules:** constitution 6.7 and an amendment row (`8707da35…`, uncommitted); `CLAUDE_1.md` `a125c54e…`, `NOW.md` `5bd1f853…` unchanged.
- **Code** `9a5ac64..2058196`:
  - `fa723a8`: every application is a row; one not submitted says „неподадено“ under „Подадено на“, with the student's entries and both ticks as saved; submitted rows unchanged; the message counts the unsubmitted;
  - `2058196`: fixes from a four-agent read-only verification (fit, break, 25 mutations, the live database read on the laptop): the message's punctuation, a test for its two counts, the size paragraph in `docs/deployment.md`.
- **Checks:** 398 passed and 11 browser tests on Python 3.9.6 and 3.12.14; real Excel on the Mac, opened and imported: unsubmitted rows exact. On the live database, read-only: 14 rows, 4 unsubmitted, the 10 submitted equal to that night's copy cell for cell.
- **DEFERRED:** no length limit per entry, so drafts no page removes could make the copy too large to send; a draft holding a session later taken off the list stops the start (not new).
- **Not pushed. Outstanding:** Codex's review; the owner's acceptance; the push and laptop update (no unit, setting or schema change).

## 2026-10-23 — Seventh task: `2058196` approved

- **Approvals of `2058196`** (range `9a5ac64..2058196`, record `75f7b38`):
  - Codex APPROVED, relayed by the owner (verbatim): "Codex APPROVED `2058196`, range `9a5ac64..2058196`, record `75f7b38`. No changes requested."
  - Opus 5.5 (`claude-opus-5-5`), the implementer, APPROVED the same commit.
- **Codex's checks**, as Codex reported them:
  - submitted rows byte-identical to `9a5ac64`'s, in a 128-record differential comparison;
  - reachable unsubmitted states exported correctly: empty applications, partial entries, retained thesis fields, every combination of ticks; no secret leaks;
  - the message's counts and punctuation and the command's output correct;
  - the tests pin inclusion, the marker, the saved ticks, the distinct counts and the exclusion of deleted records and secrets;
  - 398 passed and 11 browser tests on Python 3.9.6 and 3.12.14, with fake mail;
  - governance hashes match: `CLAUDE_1.md` `a125c54e…`, `CONSTITUTION.md` `8707da35…`, `NOW.md` `5bd1f853…`.
- **Not live:** GitHub and the laptop at `9a5ac64`. The update needs no unit, setting or schema change; the next 00:00 run after the restart uses it.
- **DEFERRED** (owner decisions): a length limit per entry; drafts holding a session later taken off `sessions.csv`.
- **Outstanding:** the owner's acceptance; the push and the laptop update; before milestone 3, Fable's `NOW.md` amendment naming this task. The governance changes stay uncommitted until then.

## 2026-10-23 — Seventh task: accepted and live on the laptop; COMPLETE

- **Owner** (verbatim): "I accept. Yes, push and update the laptop.", then "Done, I restarted the service."
- **Pushed and pulled:** GitHub and the laptop at `e6956fe` (code `2058196`). A copy of the live database was taken first: `/home/victor/nbu-superassistant-pre-update-20261023-102915.sqlite3`, schema 6, 14 applications (10 submitted, none in the bin), no report, integrity ok. Only the nightly copy unit's comment changed; no setting or schema.
- **The owner's sudo step:** the unit copied again, `daemon-reload`, the restart at 10:45:17 EEST.
- **Checks:**
  - before the restart, the laptop's new code read the live database read-only: 14 rows, 4 not submitted (№8, 10, 14, 18), 73,231 bytes;
  - after it, the service active, `/healthz` ok on the laptop and publicly, signed out `/application` leads to `/`; schema 6, integrity ok, the 14 applications kept;
  - the copy's timer next at 00:00 on 24 October, the first nightly copy with unsubmitted applications; the reminders at 09:00.
- **Status:** accepted by the owner and live: COMPLETE. The owner's look at the 24 October email, and any fault, go in a new entry.
- **Outstanding:** DEFERRED, a length limit per entry and drafts holding a session later taken off `sessions.csv`; before milestone 3, Fable's `NOW.md` amendment naming this task. The governance changes stay uncommitted until then.

## 2026-10-23 — Eighth task: the owner page's password forms name their account; for Codex's review

- **Owner** (verbatim): "i tried to login after i tried to change a user password to qwerty; a menu with my username appeared and now i cannot login"; offered the fix, "Yes, add the username field to the owner page's password forms, following the project's usual review process."
- **Cause:** the live database, read-only, holds one password change ever, a staff account's, set on the owner page at 08:17 UTC; the owner's own never changed. Each password form there had two new-password fields and no username, so the browser filed the new password under its one saved sign-in for the site, the owner's.
- **Rules:** none changed; `CLAUDE_1.md` `a125c54e…`, `CONSTITUTION.md` `8707da35…`, `NOW.md` `5bd1f853…`.
- **Code** `05fd12f..96a4aa2`:
  - `80266e9`: each form holds its account's username in a greyed read-only field, `autocomplete="username"`, with no name, so the post is unchanged;
  - `96a4aa2`: test fixes from a three-agent read-only verification (password manager, mutations, fit).
- **Checks:** 399 passed and 11 browser tests on Python 3.9.6 and 3.12.14. Chromium 148's password-manager log, one login saved: the old form updated it; the new one names its row's account and leaves it alone. Pages in Chromium and WebKit at 1280 and 390 px.
- **Not checked:** Safari's own password manager, which needs the owner's keychain.
- **Not pushed. Outstanding:** Codex's review; the owner's acceptance in Safari; the push and laptop update with a restart (no unit, setting or schema change).

## 2026-10-23 — Ninth task: staff see unsubmitted applications; for Codex's review

- **Owner** (verbatim): "can you make all the entries, even the unsubmitted visible to the staff, it was not right for them to stay hidden from staff and visible only to the code itself"; to Opus 5.5's two questions, "Same table, marked" and "See it, remove to bin".
- **Rules:** constitution 2.4, 5.15 and an amendment row (`6a0848ed…`, uncommitted); `CLAUDE_1.md` `a125c54e…`, `NOW.md` `5bd1f853…` unchanged. Fable's `NOW.md` amendment should cover draft rows before milestone 3 adds columns.
- **Code** `ffb1dd9..1bda292`:
  - `a19bbee`: „Заявления“ lists every application not in the bin, drafts after the submitted, marked „неподадено“ and counted; a draft's page read-only, with no check, correction or form; staff may remove it to the bin, where the student can neither save nor submit it;
  - `1bda292`: fixes from a three-agent read-only verification (fit, 32 break attempts, 37 mutations).
- **Tests changed with the rule:** the table and bin tests that kept drafts out.
- **Checks:** 409 passed and 11 browser tests on Python 3.9.6 and 3.12.14; the nightly copy byte-identical to `ffb1dd9`'s; pages in WebKit and Chromium at 1280 and 390 px.
- **Not new:** at 1280 px a long word in a topic pushes „Проверка“ partly out of view.
- **DEFERRED:** a student whose draft staff deleted, pressing an old page, starts a new application untold.
- **Not pushed. Outstanding:** Codex's review; the owner's acceptance; the push and laptop update with a restart (no unit, setting or schema).

## 2026-10-23 — Ninth task: `1bda292` approved

- **Approvals of `1bda292`** (range `ffb1dd9..1bda292`, record `282084c`):
  - Codex APPROVED, relayed by the owner (verbatim): "Codex APPROVED `1bda292`, range `ffb1dd9..1bda292`, record `282084c`. No changes requested."
  - Opus 5.5 (`claude-opus-5-5`), the implementer, APPROVED the same commit.
- **Codex's checks**, as Codex reported them, from an isolated archive with `CONSTITUTION.md` `6a0848ed…`:
  - drafts visible, marked and counted; the order of submitted applications kept;
  - a draft's page read-only; staff changes and document downloads refused;
  - removal to the bin blocks the student's saves and submission, injected races included; putting back allows editing again;
  - the nightly copy byte-identical to `ffb1dd9`'s over 192 invented records;
  - the updated tests keep the protections of submitted applications and cover the new rules;
  - 409 passed and 11 Chromium browser tests on Python 3.9.6 and 3.12.14, with fake mail; pages at 1280 and 390 px. WebKit not repeated, its runtime missing; Opus 5.5's WebKit renders stand.
- **DEFERRED** (owner decisions): a student pressing a stale page after staff deleted the draft; a long word in a topic overflowing the table at 1280 px.
- **Not live:** GitHub and the laptop at `05fd12f`. The eighth task's commits (`80266e9`, `96a4aa2`) lie beneath this range, so the push waits for Codex's verdict on `96a4aa2` as well.
- **Outstanding:** Codex's review of the eighth task; the owner's acceptance of both; the push and laptop update with a restart; before milestone 3, Fable's `NOW.md` amendment naming this task.
