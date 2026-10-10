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
