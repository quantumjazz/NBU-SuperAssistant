"""Staff's work: the table, one application, checks and corrections (req. 5).

The table lists submitted applications; those waiting for the supervisor,
for a check, or, confirmed and passed, for their first report stand out.
Every check and every correction is a new row that keeps what came before.
A staff change of the supervisor sends a new request; an answer already
recorded stays with the earlier request.
"""

from flask import Blueprint, abort, flash, redirect, render_template, request

from superassistant import applications, db, mail, supervision, texts
from superassistant import web

blueprint = Blueprint("staff", __name__)

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
        "ORDER BY submitted_at DESC, id DESC").fetchall()
    rows = [_row(connection, record, lists) for record in records]
    return render_template("staff_table.html", rows=rows)


def _submitted(application_id):
    record = applications.get(web.connection(), application_id)
    if record is None or record["submitted_at"] is None:
        abort(404)
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
        programme_label=supervision.programme_label(record, lists),
        fields=texts.FIELD_LABELS), status


@blueprint.route("/staff/application/<int:application_id>")
@web.staff_required
def application(application_id):
    return _render(_submitted(application_id))


@blueprint.route("/staff/application/<int:application_id>/check",
                 methods=["POST"])
@web.staff_required
def check(application_id):
    record = _submitted(application_id)
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
    record = _submitted(application_id)
    field = request.form.get("field", "")
    if field not in CORRECTABLE:
        abort(400)
    values, refusals = applications.clean({field: request.form.get("value",
                                                                   "")},
                                          [field], web.current_lists())
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
        changed = applications.correct(connection, record, values,
                                       web.session_staff()["id"])
    flash(texts.STAFF_CORRECTED if changed else texts.STAFF_NOTHING_CHANGED,
          "ok")
    return redirect("/staff/application/{}".format(record["id"]))


@blueprint.route("/staff/application/<int:application_id>/supervisor",
                 methods=["POST"])
@web.staff_required
def change_supervisor(application_id):
    from superassistant.web.student import _messages
    record = _submitted(application_id)
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
    record = _submitted(application_id)
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
