# Milestone 1: from the application to the topic-approval report

## 2026-10-10 — Plan approved and frozen; implementation authorized

- **Owner decisions** (9 October 2026, the owner's selections, verbatim): 8.1 "An owner page in the app", own account "Setting + Terminal reset (Recommended)"; 8.2 "Buttons, then a page (Recommended)"; 8.3 "No, names and F№ only"; 8.4 "3 days, 3 more, max 2 (Recommended)"; 6.7 "Everything in the email"; report sentence "Samples, slip fixed: Студенти"; readings a–j "Yes: a–j as listed, with the check"; Python 3.12 "Only at deployment". On 10 October: "I apply, freeze, and build (Fastest)", the option reading "Fable's approval of the final version is recorded as waived by you".
- **Constitution:** draft 3, SHA-256 `95de9a5dc57cdf3ce8ae48d30129c7b0ab88f3fceccfa2b3b784f6b3c977f83d`, records 6.7 and 8.1–8.4 (Opus 5.5, on the owner's "yes, write it").
- **Plan:** Fable drafted `7c5cd48e…`. Opus 5.5 (`claude-opus-5-5`) requested M1-P1..P20; Fable applied them, giving `6c91a33c…`, in the drafting chat rather than a separate one. Opus 5.5 requested M1-R1 (staff change of supervisor, as reading e) and M1-R2 (owner setting naming no account stops the start) and, on the owner's fast path, applied them itself.
- **Frozen:** `NOW.md` SHA-256 `e94e3a4e561f20f8fd4a73456f90e97376e5d6982128226debd2b5f61a9714b2`, 2,021 words, byte-identical to Opus 5.5's verified scratch copy.
- **Approvals of `e94e3a4e…`:** Opus 5.5 APPROVED. Fable: waived by the owner; no Fable verdict on this hash exists.
- **Next:** Opus 5.5 implements; Codex reviews.

## 2026-10-10 — Amendment: tests on Python 3.12 now

- **Owner decision** (verbatim): "Yes, run on 3.9 and 3.12 (Recommended)", after Opus 5.5 corrected its earlier statement that the Mac had only Python 3.9: a Python 3.12.14 is installed at `~/.local/coursebench-python312`. The earlier choice "Only at deployment" rested on that error.
- **What changes** against `e94e3a4e…`: proof 5 now reads "The whole set of tests passes on Python 3.9 and on Python 3.12."; DEFERRED no longer lists Python 3.12. Nothing else.
- **Frozen:** `NOW.md` SHA-256 `65d0ad16dea2463f9e159eccbdd595a15df461d64a265c3c1e11b848421f0fc5`, 2,017 words. Opus 5.5 APPROVED. Fable: not asked, under the owner's fast-path waiver of 10 October.
- **Repository:** on the owner's "Make this folder a repository", the folder becomes a git repository on `main`. Its history does not match GitHub's `quantumjazz/NBU-SuperAssistant`; joining them is the owner's later step.

## 2026-10-10 — Implemented; final candidate for Codex's review

- **Plan:** `NOW.md` `65d0ad16…`. Implementer: Opus 5.5 (`claude-opus-5-5`), with one round of two delegated builders in isolated worktrees (sign-in, staff and the owner's page; Word templates and reports), merged and reviewed by Opus 5.5.
- **Review target:** `fbaef2c` on `main`. Not pushed; this folder's history does not match GitHub's.
- **Checks on `fbaef2c`** (Opus 5.5): Python 3.9.6, 88 passed and browser 5 passed; Python 3.12.14, 88 passed and browser 5 passed. Documents rendered with Quick Look and looked at; templates scanned for the samples' student text: none.
- **Readings** (implementer's, for Codex and the owner): supervisor links are an HMAC of the session key, so reminders repeat them and only their hash is stored; staff cannot correct the graduation type; report rows are alphabetical by name; a code mistyped five times stops, its email's link still works; dates shown are Sofia's.
- **Disclosure:** staff registration and sign-in have no rate limit; none is required.
- **Outstanding:** Codex's review; the owner's inspection (Completion 1–5).

## 2026-10-10 — Review target superseded: `aa278fc` replaces `fbaef2c`

- **Why:** the owner's first look (verbatim: "note the loop, i cannot create my owner's account"; "it should be 'work mail'"; "it should be 'нямате профил'") found a duplicated wording name that put the student's email label on staff registration, and no way out for the first account before an owner is named.
- **Fix commit:** `aa278fc`; the fixes and their tests are listed in its message. Checks (Opus 5.5): 92 passed and browser 5 passed on Python 3.9 and on 3.12.
- **Outstanding:** Codex's review of the whole milestone at the new target; the owner's inspection.

## 2026-10-10 — Codex's review of `aa278fc`: changes requested, fixed in `bd50873`

- **Review** (Codex, relayed by the owner): CHANGES REQUESTED on `aa278fc`, findings M1-C1..C8 [P2] and M1-C9 [P3]: a refusal losing the graduation choice; hidden thesis fields blocking a state exam; controls trimmed instead of refused; no staff correction of the graduation type; missing lists recreated at start; unprintable list text and shifted line numbers; a spoofable rate-limit source; mail paths without a bound; a 10 pt report header. Codex's checks on `aa278fc`: 92 and 5 passed on Python 3.9 and 3.12.
- **Disposition:** all nine fixed in `bd50873` by Opus 5.5 (`claude-opus-5-5`), with a regression each, shown to fail on `aa278fc` and pass on `bd50873`. Mail bounds chosen: 30 an hour per supervisor, 10 decline notices per student, 300 in all.
- **Checks on `bd50873`** (Opus 5.5): Python 3.9.6 and 3.12.14, 108 passed and browser 7 passed each. The report rendered and looked at; templates rescanned: no student text, no printed year.
- **Outstanding:** Codex's review of the fixes; the owner's inspection.

## 2026-10-10 — Codex's second round on `bd50873`: fixed in `159925f` and `cc688ff`

- **Review** (Codex, relayed by the owner): four points still open, in M1-C4 (retained thesis data and answers hidden after a change to a state exam; type-change refusals called missing), M1-C5 (a removed lists folder recreated) and M1-C9 (the 12 pt header splitting the signature block across pages).
- **Disposition:** all four fixed in `159925f` by Opus 5.5 (`claude-opus-5-5`). An independent read-only check of `159925f` (two delegated agents, one round) confirmed them and found three gaps inside the same points, fixed in `cc688ff`: an upgraded schema-1 installation recreating missing lists; a filled-in invalid address called missing; a retained title alone hidden. Each fix has a regression shown to fail on the commit before it.
- **Checks on `cc688ff`** (Opus 5.5): Python 3.9.6 and 3.12.14, 123 passed and browser 7 passed each. Reports with 1, 3 and 12 invented students exported to PDF by Microsoft Word: the signature block is whole on the last page.
- **Outstanding:** Codex's review of these fixes; the owner's inspection.

## 2026-10-10 — Final code approved: `cc688ff`; ready for owner acceptance

- **Approvals of the final code `cc688ff67d0c71f3fadff087629df85319539cb3`:** Codex APPROVED, relayed by the owner: "Codex approves milestone 1 code at `cc688ff67d0c71f3fadff087629df85319539cb3`." Opus 5.5 (`claude-opus-5-5`), the implementer, APPROVED the same commit. Plan: `NOW.md` `65d0ad16…`, Opus 5.5 APPROVED; Fable's approval waived by the owner (entry of 10 October above).
- **Checks on `cc688ff`:** Codex, Python 3.9 and 3.12, 123 passed and browser 7 passed each, no skips; reports with 1, 3 and 12 invented students checked by content and by eye. Opus 5.5, the same counts.
- **DEFERRED** (Codex, non-blocking): a typed supervisor address entered with name and title empty gets the generic missing-supervisor message; the migration race between simultaneous starts, to the deployment.
- **Phase:** READY FOR OWNER ACCEPTANCE. Outstanding: the owner's inspection, `NOW.md` Completion 1–5, on the Mac with mail mode "owner".
