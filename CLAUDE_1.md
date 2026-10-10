# CLAUDE.md — shared governance for NBU-SuperAssistant

## Authority

The owner must remain able to understand, judge and control NBU-SuperAssistant.

- `CONSTITUTION.md` defines the product, the process, goals and hard constraints.
- `NOW.md` defines the current milestone.
- `docs/domain.md` records facts about the forms, the reports and the reference data. It informs work and adds no requirement unless the constitution or `NOW.md` adopts it.
- `CLAUDE.md` defines shared working rules for Opus 5.5 (`claude-opus-5-5`), Fable (`claude-fable-5-1`) and Codex; `AGENTS.md` is Codex's entry point. Opus 5.5 and Fable are both Claude models, so reviews, handoffs and records name the model, never just "Claude".

The owner decides scope, exceptions, roles and acceptance. Record explicit decisions; never change requirements or governance to make your own work pass review. Older plans, logs, chats and implementations are not requirements unless the owner reintroduces them. Review records document evidence and decisions; they cannot introduce requirements.

Never replace an explicit decision in the owner's prompt or follow-up with your own assumption. If its meaning or effect is uncertain, ask the owner and discuss it before drafting a conflicting requirement or taking dependent action. Do not soften, work around, or present an already stated choice as an open question. Label any alternative you suggest as a proposal until the owner decides. The constitution's "Not yet decided" list names choices that are still open; no code assumes an answer to them.

## Scope

No code creep. Work only on the agreed milestone or a task explicitly authorized by the owner. Stop and report conflicts with the constitution or `NOW.md`. Mark unrelated improvements, hypothetical future needs and unresolved questions `DEFERRED:`.

Deliver the requested behaviour end to end using the simplest sufficient implementation and readable technology. Make necessary design decisions without narrowing the feature into a toy version. Necessary refactoring is allowed; explicitly requested simplification or removal must meet the same regression checks. Do not rename core concepts without explicit approval.

Ask only when ambiguity changes visible behaviour, makes implementation dishonest or conflicts with governance. Otherwise choose the simplest reversible implementation and state the assumption; do not produce a large design document to resolve ambiguity.

## The project

- **What it is.** One Flask application for four kinds of user, as `CONSTITUTION.md` describes:
  - students, who sign in by an emailed link or code;
  - supervisors, who act only by email;
  - staff, who sign in with a username or email address and a password — never an emailed link or code ("no tokens for admin login and development");
  - the owner.
- **Reference implementation.** CourseBench (`quantumjazz/CourseBench`) is the owner's working example of the patterns this project reuses:
  - single-use emailed codes and links, stored hashed, expiring and rate-limited (`coursebench/signup.py`) — here, the pattern for students' sign-in and supervisors' answers;
  - accounts with slow-hashed passwords and usernames that may not contain "@" (`accounts.py`);
  - rate-limited mail through an SMTP relay that reports every failure (`mail.py`);
  - an owner's command-line tool on the host (`admin.py`);
  - running as a systemd service behind the host's Cloudflare Tunnel (`docs/deployment.md`). The pilot runs the same way, on the owner's laptop-server at a visiometrica.com address.

  Before writing any of these, read the CourseBench module that does it and follow its approach. Copy code with a comment naming where it came from. Never import from CourseBench or share its settings or data directory.
- **Names.**
  - Repository: `NBU-SuperAssistant`.
  - Python package: `superassistant`.
  - Settings prefix: `SUPERASSISTANT_`.
  - Host service: `nbu-superassistant`.

  Do not rename these without the owner's approval.
- **Python.** 3.9 on the owner's Mac and 3.12 on the host, and the code runs on both. That rules out `match` statements, `X | Y` unions outside annotations, and anything else newer than 3.9.
- **Running it.**
  - Locally, `python app.py` serves `http://127.0.0.1:5002`. CourseBench uses 5001.
  - On the host, gunicorn listens on `127.0.0.1:8791`. CourseBench's deployment notes list the ports already taken.
- **Records.** SQLite through Python's built-in `sqlite3`, in a data directory outside the clone (`SUPERASSISTANT_DATA_DIR`). Schema changes are migrations that keep existing rows.
- **Documents.** Word templates in `templates/` are filled with docxtpl. A template is an ordinary Word file the owner can open and edit. Logic stays in Python, not in template tags.
- **Mail.**
  - Every message leaves through one module, configured by `SUPERASSISTANT_SMTP_*` settings as in CourseBench.
  - In development, `SUPERASSISTANT_MAIL_MODE=owner` delivers every message to the owner's address, with the intended recipient written at its top. `SUPERASSISTANT_MAIL_MODE=console` prints messages instead of sending them, so a student's sign-in link can be followed from the terminal. Running a development copy needs no tokens or keys.
  - Tests use a fake relay and never send.
- **Language.**
  - Bulgarian: the interface, the emails and the documents. All Bulgarian wording lives in one module, so the owner can read and change it in one place.
  - English: code, identifiers, comments, commit messages and governance files.
- **Data in the repository.** Never commit real students, supervisors' answers, staff records or the owner's sample reports, which contain students' names. Fixtures use invented people. Templates are built from the samples with every student row removed.

## Protect and verify

Inspect relevant existing code and tests before changing code. Preserve owner-accepted behaviour unless the owner explicitly approves a change. Run relevant tests before and after changes that can affect it. Never weaken, delete or rewrite checks merely to make code pass. Stop and report trade-offs that materially worsen accepted behaviour.

Never delete, overwrite or reset what people have entered: students' applications, supervisors' answers, staff checks, the owner's lists or generated reports. A correction keeps what it replaces and records who made it and when. Never delete or replace governance files without explicit owner instruction.

Judge actual behaviour. A student must really be able to finish the application on a phone, a message must really arrive, and a generated report must really open in Word and look like the department's report. Passing unit tests alone is insufficient.

- **Test rules as rules**, over every input they must hold for, not one example. That covers:
  - which dean a report goes to;
  - which title, columns and students it has;
  - what each answer does to an application;
  - who may see what;
  - names, topics and lists of any length and in any characters, including mixed Latin and Cyrillic.

  Property-testing dependencies are development-only and stay out of the server's requirements.
- **Check a generated document twice:**
  - by content: the right text in the right cells, read back from the .docx;
  - by eye: rendered to an image or opened in Word before anyone says it works.
- **Test every role for what it must not see.** A student sees only their own application; an account without staff rights sees no student data.
- **No test or development run emails a real student, supervisor or member of staff.**

## Milestone workflow

Before starting or taking over work, read the constitution and `NOW.md`; identify the phase and review target when applicable. In the current review record, read the latest checkpoint and search for earlier owner decisions, findings and proof relevant to that target. Read older passages as needed for provenance, rather than loading a long record in full by default. Routine support tasks need no invented milestone. Do not request authorization already given.

1. **Plan.** The owner brainstorms the milestone with Opus 5.5. Fable drafts and revises `NOW.md` as "Drafting `NOW.md`" below directs; Opus 5.5 reviews it for completeness, scope and unnecessary repetition against the owner's request and constitution. Iterate until both explicitly approve the same plan version, identified by Git commit or content hash. The owner authorizes implementation.

2. **Freeze.** Once approved and authorized, all of `NOW.md` is frozen, including status and evidence. Put milestone decisions and evidence updates in the milestone record. To amend requirements, record the exact proposal and reason, pause affected work, obtain the owner's decision and Fable's and Opus 5.5's explicit approval of the same amended version before resuming. Never weaken requirements to accommodate code or failing tests. Advance to another milestone only after completion and owner authorization, or an explicit owner decision to replace the current milestone.

3. **Implement and review.** Opus 5.5 implements; Codex independently reviews, reproduces failures and debugs. Only one agent edits the shared checkout at a time; hand off a named revision. Parallel read-only reviews require an unchanged target. The other agent reviews every fix, including test changes and fixes to earlier fixes; author verification does not replace the other agent's review. Review the whole milestone against requirements, tests and scope. Findings need reproducible evidence or a precise explanation. A `CHANGES REQUESTED` verdict on a plan or code names the exact changes that will earn approval; the next review checks only those changes and anything they break. Blockers must concern agreed scope or regressions caused by the milestone; unrelated defects and optional preferences stay deferred unless authorized. Discuss disputed findings in chat and record only their milestone-level resolution; bring persistent disagreements without new evidence to the owner with concrete options. Respect all data, tooling and mail constraints.

4. **Record.** Keep only milestone records in `docs/reviews/`, one `docs/reviews/<milestone>.md` per milestone. The owner's chat is the handoff for consecutive reviews of Opus 5.5's current code: give the owner a complete, copy-paste-ready review here and receive Opus 5.5's reply here. Do not append those detailed code reviews or exchanges to the milestone file, or create a file entry for each review pass. Append only milestone-level plan decisions, authorizations, evidence checkpoints and acceptance. Keep entries short, dated, attributed and append-only; corrections must identify what they supersede. Summarize phase, owner decisions, exact review targets and verdicts (`APPROVED`, `CHANGES REQUESTED`, `BLOCKED`), stable finding IDs and their disposition, key evidence, fix revisions and the other agent's verification. Include relevant commands and results, distinguishing failures, skips and checks not run, plus outstanding acceptance and deferred work; link large logs instead of copying them. A record line stating what the owner decided or authorized quotes the owner or cites the approved plan line. Never fabricate or infer an agent's verdict: silence, a summary by someone else or a subagent is not that agent's approval.

5. **Accept and close.** Every task requires behaviour that works end to end, relevant passing checks, no unapproved regression and compliance with the constitution and authorized scope. A milestone additionally requires all `NOW.md` requirements and proof, no unresolved blockers, Fable's and Opus 5.5's explicit approval of the same plan version, Opus 5.5's and Codex's explicit approval of the same final code commit, and every required owner acceptance check. No uncommitted code, tests or runtime configuration may fall outside the reviewed revision. Later code, test, configuration, requirement or governance changes require review and renewed final approval; evidence-only appends do not invalidate approval of unchanged work. Report `READY FOR OWNER ACCEPTANCE` only when owner inspection is the sole outstanding condition; otherwise report the actual phase. Record `COMPLETE` and its evidence in the review record, leaving `NOW.md` frozen.

## Drafting NOW.md

Opus 5.5 hands a brainstorm to Fable as one self-contained, copy-paste-ready message quoting the owner's request and decisions. Fable writes the initial draft in one chat; revisions and amendments following Opus 5.5's review take place in separate chats. Carry the exact draft hash, review requests and owner decisions into each handoff.

When the owner authorizes milestone planning, Fable drafts and revises `NOW.md` using exactly these five sections:

1. **Goal** — the capability being delivered and its purpose.
2. **Required behaviour** — observable requirements, including any adopted from earlier plans.
3. **Required proof** — how each requirement will be checked.
4. **Constraints and exclusions** — protected behaviour, limits, stop conditions and deferred work.
5. **Completion** — acceptance conditions, including required owner inspection.

Aim for 500–800 words. This is a target, not a reason to omit essential requirements or acceptance criteria. Reference the constitution instead of repeating it; keep milestone requirements explicit and self-contained.

Exclude implementation diaries, review discussions, status updates and accumulated evidence; keep the detailed exchanges in chat and summarize only milestone decisions and evidence in the milestone review record. Check both completeness and unnecessary repetition before submitting the draft for Opus 5.5's review.

Use this structure for new milestone drafts. For an existing frozen plan, change only what an explicitly approved amendment authorizes; do not reformat it to impose the template.

## Bounded work and resource control

For each implementation or review pass, state in chat the approved plan or named revision, requirements or finding IDs, planned checks, expected time/delegation/CPU cost, and handoff condition. The first code review covers the milestone; after `CHANGES REQUESTED`, check only named fixes and direct fallout. Work on a new finding only when a reproducible case or precise mechanism ties it to the authorized task, frozen requirement or accepted behaviour; defer the rest. If a blocker needs a new subsystem, a broad sweep or substantial extra work, give the owner evidence, options and an estimate before expanding. Put new development-only instruments and evidence in purpose-named repository directories, preserving frozen evidence in place.

Use at most four bounded delegated tasks per pass, in one round, each with a fixed question and stop condition; no recursive review waves. Only the named editor changes the shared checkout; assigned delegates may edit isolated worktrees. More delegation or a second exploratory sweep needs the owner's decision. Run at most one CPU-heavy local job at a time unless the owner chooses otherwise. An unplanned check expected to take over 15 minutes locally needs the owner's decision after its evidence gap and cost are stated; frozen-plan proof is exempt. Focused verification of a reproduced blocker remains authorized. Searching for more failure shapes after its reproduction or fix verification is exploratory. Use focused tests while fixing, then the required full checks on the final candidate; repeat them after relevant changes or failures.

The pass clock runs while delegates or background jobs work or the lead waits for them; bound those waits, but exclude waits for owner input and system sleep. Report progress and remaining proof after 60 active minutes. At two hours of exploratory review or unplanned work, finish the safe operation, stop and report the verdict or unfinished work with options. Necessary implementation and required proof may reach a finite checkpoint declared up front, but stop if its scope or cost materially expands. An already-running required check may finish. Before handoff, await or safely stop owned background jobs; an owner-requested persistent service may remain with its status stated. The receiving agent checks target, scope, delegation, heavy checks and job status, reporting breaches without launching a compensating sweep. These bounds never excuse weakened tests, missing proof, deferred genuine blockers or unsupported approval.

Each new milestone-record checkpoint is at most 250 words. Check its added text before committing; link detailed evidence and keep per-pass exchanges in chat. Existing append-only record content remains intact.

## Communication

Use plain language for the non-programmer owner, most important point first. Distinguish **REQUIRED NOW** from **DEFERRED**. Claim behaviour works only after actually running it. Disclose any fakes, stubs, hard-coded behaviour or simulations used to demonstrate the milestone.

Briefly report what changed, what works, how to verify it (exact commands or clicks), and limitations, assumptions or deferred work. Omit empty categories.
