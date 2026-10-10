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
