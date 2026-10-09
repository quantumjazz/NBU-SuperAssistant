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
