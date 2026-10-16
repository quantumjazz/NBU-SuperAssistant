"""The student's application: two tabs, saved until submitted (NOW.md req. 2).

The first tab follows the заявление-декларация, the second Приложение 2. A
field both paper forms have (names, F№, topic) is asked once, on the first
tab. A state exam asks only the three names and F№, and has no second tab.
F№ is typed as digits after a fixed „F“. The first tab also carries, for
both types, the form's declaration that the credits are covered: a tick saved
with the draft, without which the application is not submitted. And the
schedule of sessions (constitution 5.13), from which the student chooses a
session, and the tick that the student knows it: both saved with the draft,
both needed to submit. A submitted application's page shows the schedule
again, with the session chosen.
After submission the page shows where the application stands; the student may
change only the supervisor, and only after a decline. An application staff
have removed to the bin (constitution 5.15) shows only that it was removed,
and nothing the student sends changes it.
"""

from flask import Blueprint, flash, redirect, render_template, request

from superassistant import applications, mail, sessions, supervision, texts
from superassistant import web

blueprint = Blueprint("student", __name__)


@blueprint.errorhandler(applications.Removed)
def _removed(exc):
    """A change to an application removed or deleted meanwhile: nothing
    changed; the application page says where it stands."""
    return redirect("/application")

TAB_FIELDS = {
    1: ("name1", "name2", "name3", "fn", "phone", "programme", "topic",
        "average_grade", "professor", "sup_name", "sup_title", "sup_email"),
    2: applications.MULTI_LINE_FIELDS,
}
COMMON_FIELDS = ("name1", "name2", "name3", "fn")
SESSION_FIELDS = ("grad_session",)
FIELD_TAB = dict((field, tab) for tab, fields in TAB_FIELDS.items()
                 for field in fields)
FIELD_TAB["grad_type"] = 1
FIELD_TAB["credits_declared"] = 1
FIELD_TAB["grad_session"] = 1
FIELD_TAB["schedule_ack"] = 1


def _record():
    return applications.get_or_create(web.connection(), web.session_student(),
                                      web.session_student_email() or "")


def _messages(refusals):
    """One sentence per refused field, keyed by field."""
    out = {}
    for refusal in refusals:
        if refusal.reason == "control":
            shown = ", ".join("U+{:04X}".format(ord(ch))
                              for ch in refusal.characters)
            out[refusal.field] = texts.REFUSED_CONTROL.format(shown)
        elif refusal.reason == "mixed":
            out[refusal.field] = texts.REFUSED_MIXED.format(
                " ".join(refusal.characters))
        elif refusal.reason == "address":
            out[refusal.field] = texts.MAIL_BAD_ADDRESS
        elif refusal.reason == "choice":
            out[refusal.field] = texts.REFUSED_CHOICE
        elif refusal.reason == "fn":
            out[refusal.field] = texts.REFUSED_FN
        elif refusal.reason == "tick":
            out[refusal.field] = texts.TICK_REQUIRED
        elif refusal.reason == "session":
            out[refusal.field] = texts.REFUSED_SESSION
        else:
            out[refusal.field] = texts.REFUSED_REQUIRED
    return out


def _render(record, tab, values=None, errors=None, status=200, again=None):
    lists = web.current_lists()
    shown = dict(record)
    shown.update(values or {})
    # The F№ field holds the digits after the fixed „F“; what was typed, when
    # the page comes back with a refusal.
    shown["fn"] = (values["fn"] if values and "fn" in values
                   else applications.fn_digits(record["fn"]))
    standing = applications.standing(web.connection(), record)
    day = sessions.today()
    return render_template(
        "application.html", record=record, values=shown, tab=tab,
        schedule=sessions.schedule(lists, day),
        offered=[(code, sessions.label(lists, code))
                 for code in sessions.offered(lists, day)],
        session_label=sessions.label(lists, record["grad_session"]),
        removed=applications.is_binned(record),
        fn_letter=applications.FN_LETTER,
        errors=errors or {}, lists=lists, standing=standing,
        submitted=record["submitted_at"] is not None,
        current=applications.current_request(web.connection(), record["id"]),
        supervisor_label=applications.supervisor_label(record, lists),
        programme_label=supervision.programme_label(record, lists),
        fields=texts.FIELD_LABELS, again=again or {}), status


@blueprint.route("/application")
@web.student_required
def application():
    record = _record()
    tab = 2 if request.args.get("tab") == "2" else 1
    if tab == 2 and record["grad_type"] != "thesis":
        tab = 1
    return _render(record, tab)


@blueprint.route("/application", methods=["POST"])
@web.student_required
def save():
    record = _record()
    if record["submitted_at"] is not None:
        return redirect("/application")
    tab = 2 if request.form.get("tab") == "2" else 1
    if tab == 1:
        grad_type = request.form.get("grad_type", "")
        grad_type = grad_type if grad_type in applications.GRAD_TYPES else None
        # Only what the chosen type asks is checked and saved: the thesis
        # fields of a state exam are hidden, and entries saved in them
        # earlier are kept as they were.
        fields = (TAB_FIELDS[1] if grad_type == "thesis"
                  else COMMON_FIELDS) + SESSION_FIELDS
    else:
        grad_type = record["grad_type"]
        fields = TAB_FIELDS[2]
    values, refusals = applications.clean(request.form, fields,
                                          web.current_lists())
    if tab == 1:
        values["grad_type"] = grad_type
        values["credits_declared"] = 1 if request.form.get(
            "credits_declared") else 0
        values["schedule_ack"] = 1 if request.form.get("schedule_ack") else 0
        if not refusals and grad_type == "thesis":
            values.update(supervision.supervisor_values(values))
    if refusals:
        typed = dict((f, request.form.get(f, "")) for f in fields)
        typed["grad_type"] = grad_type
        typed["credits_declared"] = values.get("credits_declared",
                                               record["credits_declared"])
        typed["schedule_ack"] = values.get("schedule_ack",
                                           record["schedule_ack"])
        flash(texts.FIX_BELOW, "error")
        return _render(record, tab, typed, _messages(refusals), 400)
    applications.save_draft(web.connection(), record, values)
    record = applications.get(web.connection(), record["id"])
    if record is None:
        raise applications.Removed()
    action = request.form.get("action", "save")
    if action == "next" and record["grad_type"] == "thesis":
        return redirect("/application?tab=2")
    if action == "submit":
        try:
            missing = supervision.submit(web.connection(), web.settings(),
                                         web.current_lists(), record["id"])
        except mail.MailFailed:
            flash(texts.SUBMIT_MAIL_FAILED, "error")
            return _render(record, tab, status=503)
        if missing:
            errors = _messages(missing)
            first = min(FIELD_TAB.get(f, 1) for f in errors)
            flash(texts.FIX_BELOW, "error")
            return _render(record, first, errors=errors, status=400)
        flash(texts.SUBMITTED, "ok")
        return redirect("/application")
    flash(texts.SAVED, "ok")
    return redirect("/application?tab={}".format(tab))


@blueprint.route("/application/supervisor", methods=["POST"])
@web.student_required
def choose_again():
    record = _record()
    fields = ("professor", "sup_name", "sup_title", "sup_email")
    values, refusals = applications.clean(request.form, fields,
                                          web.current_lists())
    if not refusals:
        try:
            refusals = supervision.choose_again(
                web.connection(), web.settings(), web.current_lists(),
                record["id"], values)
        except PermissionError:
            return redirect("/application")
        except mail.MailFailed:
            flash(texts.SUBMIT_MAIL_FAILED, "error")
            return _render(record, 1, status=503)
    if refusals:
        flash(texts.FIX_BELOW, "error")
        typed = dict((f, request.form.get(f, "")) for f in fields)
        return _render(record, 1, None, _messages(refusals), 400, typed)
    flash(texts.CHOSEN_AGAIN, "ok")
    return redirect("/application")
