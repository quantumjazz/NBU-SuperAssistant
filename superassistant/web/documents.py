"""The Word files on the web: the student's two forms, and staff's
topic-approval reports (NOW.md requirements 4 and 7).

A student downloads only the forms of their own application, and only once
it is submitted and not in the bin; Приложение 2 only for a thesis.
Anything else is "not found", so a student learns nothing about other
applications. Staff download and print the forms of any submitted
application, also while it is in the bin, until it is deleted (constitution
5.5); each file is built from the record as it stands, corrections
included, and its name carries the application's number and F№.

Staff choose a programme, generate its report, and download any kept
report. Staff may remove a kept report to the bin with one press,
and there download it, put it back, or, after a second page that names it,
delete it (constitution 5.14); the bin lists the deletions. A button for a
report no longer where its page showed it (pressed twice, or another member
of staff acted first, or a page from before the bin) changes nothing, and
staff are taken to the bin with a sentence saying so.
"""

import io

from flask import (Blueprint, abort, flash, redirect, render_template,
                   request, send_file)

from superassistant import applications, documents, reports, texts
from superassistant import web

blueprint = Blueprint("documents", __name__)


def _send(data, filename):
    """A Word file as an attachment, under an ASCII file name."""
    return send_file(io.BytesIO(data), mimetype=documents.MIMETYPE,
                     as_attachment=True, download_name=filename,
                     max_age=0)


def _own_submitted_application():
    application = web.connection().execute(
        "SELECT * FROM applications WHERE email_key = ?",
        (web.session_student(),)).fetchone()
    if (application is None or not application["submitted_at"]
            or application["binned_at"] is not None):
        abort(404)
    return application


@blueprint.route("/application/forms/zaiavlenie.docx")
@web.student_required
def zaiavlenie():
    application = _own_submitted_application()
    return _send(documents.zaiavlenie(application, web.current_lists()),
                 "zaiavlenie-deklaracia.docx")


@blueprint.route("/application/forms/prilozhenie2.docx")
@web.student_required
def prilozhenie2():
    application = _own_submitted_application()
    if application["grad_type"] != "thesis":
        abort(404)
    return _send(documents.prilozhenie2(application, web.current_lists()),
                 "prilozhenie-2.docx")


def _staff_record(application_id):
    """A submitted application, in the bin or not, for staff; else not
    found."""
    record = applications.get(web.connection(), application_id)
    if record is None or record["submitted_at"] is None:
        abort(404)
    return record


def _staff_name(form, record):
    """The form's file name for staff: its application's number, then the
    F№ when it is „F“ and digits (an F№ stored before that rule is left
    out, so the name stays ASCII)."""
    name = "{}-{}".format(form, record["id"])
    digits = applications.fn_digits(record["fn"])
    if digits and digits != record["fn"]:
        name += "-" + applications.FN_LETTER + digits
    return name + ".docx"


@blueprint.route("/staff/application/<int:application_id>/zaiavlenie.docx")
@web.staff_required
def staff_zaiavlenie(application_id):
    record = _staff_record(application_id)
    return _send(documents.zaiavlenie(record, web.current_lists()),
                 _staff_name("zaiavlenie-deklaracia", record))


@blueprint.route("/staff/application/<int:application_id>/prilozhenie2.docx")
@web.staff_required
def staff_prilozhenie2(application_id):
    record = _staff_record(application_id)
    if record["grad_type"] != "thesis":
        abort(404)
    return _send(documents.prilozhenie2(record, web.current_lists()),
                 _staff_name("prilozhenie-2", record))


def _choices(lists, counts):
    """Each listed programme, with its faculty and how many qualify."""
    out = []
    for code, programme in lists.programmes.items():
        out.append({
            "code": code,
            "label": texts.REPORTS_OPTION.format(
                label=documents.programme_label(code, lists),
                faculty=programme["faculty"], count=counts.get(code, 0)),
        })
    return out


@blueprint.route("/staff/reports", methods=["GET", "POST"])
@web.staff_required
def reports_page():
    lists = web.current_lists()
    connection = web.connection()
    if request.method == "POST":
        programme = request.form.get("programme") or ""
        if programme not in lists.programmes:
            flash(texts.REPORTS_CHOOSE, "error")
            return redirect("/staff/reports")
        try:
            reports.generate(connection, web.settings(), lists, programme,
                             web.session_staff()["id"])
        except reports.NothingToReport:
            flash(texts.REPORTS_NOTHING.format(
                documents.programme_label(programme, lists)), "error")
        else:
            flash(texts.REPORTS_MADE, "ok")
        return redirect("/staff/reports")
    kept = [_shown(row, lists) for row in reports.kept(connection)]
    return render_template(
        "reports.html", choices=_choices(lists, reports.counts(connection)),
        kept=kept)


def _shown(row, lists):
    """A report, kept or in the bin, as the pages show it."""
    shown = {"id": row["id"],
             "name": reports.download_name(row["id"], row["generated_at"]),
             "date": documents.local_date(row["generated_at"]),
             "programme": documents.programme_label(row["programme"], lists)
             or row["programme"],
             "faculty": row["faculty"], "students": row["students"]}
    if reports.is_binned(row):
        shown.update(binned_by=row["username"], binned_at=row["binned_at"])
    return shown


def binned(connection, lists):
    """The reports in the bin, as the bin shows them."""
    return [_shown(row, lists) for row in reports.binned(connection)]


def deleted(connection, lists):
    """The deleted reports, as the bin's log shows them."""
    return [{"name": reports.download_name(row["report_id"],
                                           row["generated_at"]),
             "date": documents.local_date(row["generated_at"]),
             "programme": documents.programme_label(row["programme"], lists)
             or row["programme"],
             "students": row["students"],
             "removed_by": row["removed_by"], "removed_at": row["removed_at"],
             "by": row["username"], "at": row["deleted_at"]}
            for row in reports.deletions(connection)]


def _not_in_bin():
    """A bin button for a report not in the bin (never removed, put back or
    deleted, by this press's twin or by someone else): nothing changed."""
    flash(texts.REPORTS_NOT_IN_BIN, "error")
    return redirect("/staff/bin")


@blueprint.route("/staff/reports/<int:report_id>/remove", methods=["POST"])
@web.staff_required
def remove(report_id):
    """The first step: one press moves a kept report to the bin."""
    if not reports.remove(web.connection(), report_id,
                          web.session_staff()["id"]):
        flash(texts.REPORTS_REMOVED_MEANWHILE, "error")
        return redirect("/staff/bin")
    flash(texts.REPORTS_REMOVED, "ok")
    return redirect("/staff/reports")


@blueprint.route("/staff/reports/<int:report_id>/restore", methods=["POST"])
@web.staff_required
def restore(report_id):
    if not reports.restore(web.connection(), report_id,
                           web.session_staff()["id"]):
        return _not_in_bin()
    flash(texts.REPORTS_RESTORED, "ok")
    return redirect("/staff/reports")


@blueprint.route("/staff/reports/<int:report_id>/delete")
@web.staff_required
def delete_page(report_id):
    """The second step: the report in the bin named, and the button that
    deletes it."""
    connection = web.connection()
    report = connection.execute(
        "SELECT r.*, (SELECT COUNT(*) FROM report_students s WHERE "
        "s.report_id = r.id) AS students, a.username FROM reports r "
        "LEFT JOIN accounts a ON a.id = r.binned_by WHERE r.id = ?",
        (report_id,)).fetchone()
    if not reports.is_binned(report):
        return _not_in_bin()
    return render_template("report_delete.html", binned=True,
                           report=_shown(report, web.current_lists()))


@blueprint.route("/staff/reports/<int:report_id>/delete", methods=["POST"])
@web.staff_required
def delete(report_id):
    if not reports.delete(web.connection(), web.settings(), report_id,
                          web.session_staff()["id"]):
        return _not_in_bin()
    flash(texts.REPORTS_DELETED, "ok")
    return redirect("/staff/bin")


@blueprint.route("/staff/reports/<int:report_id>.docx")
@web.staff_required
def report_file(report_id):
    """A report's file, kept or in the bin. One deleted in the moment
    between the look and the reading is not found either."""
    report = reports.get(web.connection(), report_id)
    if report is None:
        abort(404)
    try:
        data = reports.path(web.settings(), report).read_bytes()
    except (FileNotFoundError, IsADirectoryError):
        abort(404)
    return _send(data, reports.download_name(report_id,
                                             report["generated_at"]))
