"""Staff's work: the table, one application, checks and corrections (req. 5).

The table lists submitted applications; those waiting for the supervisor,
for a check, or, confirmed and passed, for their first report stand out.
Every check and every correction is a new row that keeps what came before.
A staff change of the supervisor sends a new request; an answer already
recorded stays with the earlier request.

Staff see the programme's code beside its name, which students never see
(constitution 5.3), whether the student ticked the declaration that the
credits are covered, the session the student chose and whether the student
ticked knowing the schedule (5.13); an application submitted before shows
„—“. Staff may correct the session to any listed session, passed or not, a
correction like any other. A correction of F№ takes the digits, with or
without „F“ or „f“ before them, and stores „F“ and the digits.

Staff may remove an application to the bin, choosing why, and from the bin
put it back or, after a second page that names it, delete it (constitution
5.15). An application in the bin leaves the table; its own page shows it
read-only, and every change to it is refused, also when the removal comes
between the page and the change (applications.Removed): staff are taken to
the bin with a sentence saying nothing changed, as they are after pressing
a bin button twice, or after another member of staff acted first.
"""

from flask import Blueprint, abort, flash, redirect, render_template, request

from superassistant import applications, db, mail, sessions, supervision
from superassistant import texts
from superassistant import web

blueprint = Blueprint("staff", __name__)


@blueprint.errorhandler(applications.Removed)
def _removed(exc):
    """A change to an application removed or deleted since its page was
    read: nothing changed, and staff are told so in the bin."""
    flash(texts.BIN_REMOVED_MEANWHILE, "error")
    return redirect("/staff/bin")


def _not_in_bin():
    """A bin button for an application no longer in the bin (put back or
    deleted, by this press's twin or by someone else): nothing changed."""
    flash(texts.BIN_NOT_IN_BIN, "error")
    return redirect("/staff/bin")

# Thesis entries a state-exam application may still hold, from before staff
# corrected its type or from the student's draft: shown, never dropped.
RETAINED = ("phone", "programme", "topic", "average_grade", "professor",
            "sup_name", "sup_title", "sup_email") + applications.MULTI_LINE_FIELDS

CORRECTABLE = ("name1", "name2", "name3", "fn", "phone", "programme", "topic",
               "average_grade") + applications.MULTI_LINE_FIELDS


def _row(connection, record, lists):
    standing = applications.standing(connection, record)
    programme = lists.programmes.get(record["programme"])
    return {
        "record": record,
        "standing": standing,
        "name": applications.full_name(record),
        "programme": ("{} {}".format(programme["degree"], programme["name"])
                      + ", " + programme["form"]) if programme else "",
        "code": record["programme"],
        "declared": record["credits_declared_at"] is not None,
        "session": sessions.label(lists, record["grad_session"]),
        "acknowledged": record["schedule_ack_at"] is not None,
        "supervisor": (applications.supervisor_label(record, lists)
                       if record["grad_type"] == "thesis" else ""),
    }


@blueprint.route("/staff")
@web.staff_required
def table():
    connection = web.connection()
    lists = web.current_lists()
    records = connection.execute(
        "SELECT * FROM applications WHERE submitted_at IS NOT NULL "
        "AND binned_at IS NULL ORDER BY submitted_at DESC, id DESC").fetchall()
    rows = [_row(connection, record, lists) for record in records]
    return render_template("staff_table.html", rows=rows)


def _submitted(application_id):
    """A submitted application, in the bin or not; else not found."""
    record = applications.get(web.connection(), application_id)
    if record is None or record["submitted_at"] is None:
        abort(404)
    return record


def _active(application_id):
    """A submitted application not in the bin, which staff may change."""
    record = _submitted(application_id)
    if applications.is_binned(record):
        raise applications.Removed(application_id)
    return record


def _render(record, errors=None, status=200):
    connection = web.connection()
    lists = web.current_lists()
    requests = applications.requests_of(connection, record["id"])
    return render_template(
        "staff_application.html", row=_row(connection, record, lists),
        record=record, lists=lists, errors=errors or {},
        requests=[(r, supervision.request_label(r, lists)) for r in requests],
        retained=any(record[f] for f in RETAINED),
        supervisor_label=applications.supervisor_label(record, lists),
        checks=applications.checks_of(connection, record["id"]),
        corrections=applications.corrections_of(connection, record["id"]),
        correctable=CORRECTABLE,
        schedule=[(code, sessions.label(lists, code),
                   sessions.is_passed(session))
                  for code, session in lists.sessions.items()],
        session_label=lambda code: sessions.label(lists, code),
        programme_label=supervision.programme_label(record, lists),
        fields=texts.FIELD_LABELS, binned=applications.is_binned(record),
        binned_by=_username(connection, record["binned_by"])), status


def _username(connection, account_id):
    if account_id is None:
        return ""
    row = connection.execute("SELECT username FROM accounts WHERE id = ?",
                             (account_id,)).fetchone()
    return row["username"] if row else ""


@blueprint.route("/staff/application/<int:application_id>")
@web.staff_required
def application(application_id):
    return _render(_submitted(application_id))


@blueprint.route("/staff/application/<int:application_id>/check",
                 methods=["POST"])
@web.staff_required
def check(application_id):
    record = _active(application_id)
    result = request.form.get("result", "")
    if result not in ("passed", "not_passed"):
        flash(texts.FIX_BELOW, "error")
        return _render(record, {"result": texts.REFUSED_REQUIRED}, 400)
    applications.record_check(web.connection(), record["id"], result,
                              request.form.get("note", "").strip(),
                              web.session_staff()["id"])
    flash(texts.STAFF_CHECK_RECORDED, "ok")
    return redirect("/staff/application/{}".format(record["id"]))


@blueprint.route("/staff/application/<int:application_id>/correct",
                 methods=["POST"])
@web.staff_required
def correct(application_id):
    from superassistant.web.student import _messages
    record = _active(application_id)
    field = request.form.get("field", "")
    if field not in CORRECTABLE:
        abort(400)
    values, refusals = applications.clean({field: request.form.get("value",
                                                                   "")},
                                          [field], web.current_lists(),
                                          fn_letter=True)
    required = applications.REQUIRED_ALL + (
        applications.REQUIRED_THESIS if record["grad_type"] == "thesis"
        else ())
    if not refusals and not values[field] and field in required:
        refusals = [applications.Refusal(field, "required")]
    if refusals:
        flash(texts.FIX_BELOW, "error")
        return _render(record, {"correction": _messages(refusals)[field]},
                       400)
    connection = web.connection()
    with db.transaction(connection):
        record = applications.require_active(connection, record["id"])
        changed = applications.correct(connection, record, values,
                                       web.session_staff()["id"])
    flash(texts.STAFF_CORRECTED if changed else texts.STAFF_NOTHING_CHANGED,
          "ok")
    return redirect("/staff/application/{}".format(record["id"]))


@blueprint.route("/staff/application/<int:application_id>/session",
                 methods=["POST"])
@web.staff_required
def correct_session(application_id):
    """Correct the session to any listed one, passed or not (5.13)."""
    record = _active(application_id)
    code = request.form.get("grad_session", "")
    if code not in web.current_lists().sessions:
        flash(texts.FIX_BELOW, "error")
        return _render(record, {"session": texts.REFUSED_SESSION}, 400)
    connection = web.connection()
    with db.transaction(connection):
        record = applications.require_active(connection, record["id"])
        changed = applications.correct(connection, record,
                                       {"grad_session": code},
                                       web.session_staff()["id"])
    flash(texts.STAFF_CORRECTED if changed else texts.STAFF_NOTHING_CHANGED,
          "ok")
    return redirect("/staff/application/{}".format(record["id"]))


@blueprint.route("/staff/application/<int:application_id>/supervisor",
                 methods=["POST"])
@web.staff_required
def change_supervisor(application_id):
    from superassistant.web.student import _messages
    record = _active(application_id)
    if record["grad_type"] != "thesis":
        abort(400)
    fields = ("professor", "sup_name", "sup_title", "sup_email")
    values, refusals = applications.clean(request.form, fields,
                                          web.current_lists())
    chosen = supervision.supervisor_values(values)
    if not refusals and all(chosen[f] == record[f] for f in fields):
        flash(texts.STAFF_NOTHING_CHANGED, "ok")
        return redirect("/staff/application/{}".format(record["id"]))
    if not refusals:
        try:
            refusals = supervision.staff_change(
                web.connection(), web.settings(), web.current_lists(),
                record["id"], values, web.session_staff()["id"])
        except mail.MailFailed:
            flash(texts.STAFF_SUPERVISOR_MAIL_FAILED, "error")
            return _render(record, status=503)
    if refusals:
        flash(texts.FIX_BELOW, "error")
        return _render(record, dict(("supervisor_" + k, v) for k, v in
                                    _messages(refusals).items()), 400)
    flash(texts.STAFF_SUPERVISOR_CHANGED, "ok")
    return redirect("/staff/application/{}".format(record["id"]))


@blueprint.route("/staff/application/<int:application_id>/type",
                 methods=["POST"])
@web.staff_required
def change_type(application_id):
    """Correct the graduation type: state exam to thesis, or back."""
    from superassistant.web.student import _messages
    record = _active(application_id)
    new_type = request.form.get("grad_type", "")
    fields = ("professor", "sup_name", "sup_title", "sup_email")
    values, refusals = applications.clean(request.form, fields,
                                          web.current_lists())
    if not refusals:
        try:
            refusals = supervision.staff_change_type(
                web.connection(), web.settings(), web.current_lists(),
                record["id"], new_type, values, web.session_staff()["id"])
        except mail.MailFailed:
            flash(texts.STAFF_SUPERVISOR_MAIL_FAILED, "error")
            return _render(record, status=503)
    if refusals is None:
        flash(texts.STAFF_NOTHING_CHANGED, "ok")
        return redirect("/staff/application/{}".format(record["id"]))
    if refusals:
        flash(texts.FIX_BELOW, "error")
        return _render(record, {"type": _type_errors(refusals)}, 400)
    flash(texts.STAFF_TYPE_CHANGED, "ok")
    return redirect("/staff/application/{}".format(record["id"]))


def _type_errors(refusals):
    """What a refused type change says: the missing fields together, and each
    other refusal in the words the student's form uses for it."""
    from superassistant.web.student import _messages
    label = lambda r: texts.FIELD_LABELS.get(r.field, r.field)
    missing = [label(r) for r in refusals if r.reason == "required"]
    detailed = _messages([r for r in refusals if r.reason != "required"])
    sentences = [label(r) + ": " + detailed[r.field] for r in refusals
                 if r.reason != "required"]
    if missing:
        sentences.insert(0, texts.STAFF_TYPE_MISSING.format(
            ", ".join(missing)))
    return " ".join(sentences)


# --- The bin (constitution 5.15) -------------------------------------------

@blueprint.route("/staff/application/<int:application_id>/remove",
                 methods=["POST"])
@web.staff_required
def remove(application_id):
    """The first step: to the bin, with the reason chosen."""
    record = _active(application_id)
    reason = request.form.get("reason", "")
    if reason not in applications.BIN_REASONS:
        flash(texts.FIX_BELOW, "error")
        return _render(record, {"remove": texts.BIN_CHOOSE_REASON}, 400)
    if not applications.remove(web.connection(), record["id"], reason,
                               request.form.get("note", ""),
                               web.session_staff()["id"]):
        raise applications.Removed(record["id"])
    flash(texts.BIN_REMOVED, "ok")
    return redirect("/staff")


@blueprint.route("/staff/application/<int:application_id>/restore",
                 methods=["POST"])
@web.staff_required
def restore(application_id):
    if not applications.restore(web.connection(), application_id,
                                web.session_staff()["id"]):
        return _not_in_bin()
    flash(texts.BIN_RESTORED, "ok")
    return redirect("/staff/application/{}".format(application_id))


@blueprint.route("/staff/application/<int:application_id>/delete")
@web.staff_required
def delete_page(application_id):
    """The second step: the application named, and the button that
    deletes it."""
    connection = web.connection()
    record = applications.get(connection, application_id)
    if not applications.is_binned(record):
        return _not_in_bin()
    return render_template(
        "application_delete.html", record=record,
        row=_row(connection, record, web.current_lists()),
        binned=True, binned_by=_username(connection, record["binned_by"]))


@blueprint.route("/staff/application/<int:application_id>/delete",
                 methods=["POST"])
@web.staff_required
def delete(application_id):
    if not applications.delete(web.connection(), application_id,
                               web.session_staff()["id"]):
        return _not_in_bin()
    flash(texts.BIN_DELETED, "ok")
    return redirect("/staff/bin")


@blueprint.route("/staff/bin")
@web.staff_required
def bin_page():
    """The applications and the reports in the bin (constitution 5.14 and
    5.15), and the log of each kind's deletions."""
    from superassistant.web import documents as report_pages
    connection = web.connection()
    lists = web.current_lists()
    rows = [dict(_row(connection, record, lists), by=record["username"])
            for record in applications.binned(connection)]
    return render_template(
        "bin.html", rows=rows, deleted=applications.deletions(connection),
        reports=report_pages.binned(connection, lists),
        deleted_reports=report_pages.deleted(connection, lists))
