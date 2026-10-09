"""The Word files on the web: the student's two forms, and staff's
topic-approval reports (NOW.md requirements 4 and 7).

A student downloads only the forms of their own application, and only once
it is submitted; Приложение 2 only for a thesis. Anything else is "not
found", so a student learns nothing about other applications. Staff choose a
programme, generate its report, and download any kept report.
"""

import io

from flask import (Blueprint, abort, flash, redirect, render_template,
                   request, send_file)

from superassistant import documents, reports, texts
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
    if application is None or not application["submitted_at"]:
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
    kept = [{"id": row["id"],
             "date": documents.local_date(row["generated_at"]),
             "programme": documents.programme_label(row["programme"], lists)
             or row["programme"],
             "faculty": row["faculty"], "students": row["students"]}
            for row in reports.kept(connection)]
    return render_template(
        "reports.html", choices=_choices(lists, reports.counts(connection)),
        kept=kept)


@blueprint.route("/staff/reports/<int:report_id>.docx")
@web.staff_required
def report_file(report_id):
    report = reports.get(web.connection(), report_id)
    if report is None:
        abort(404)
    path = reports.path(web.settings(), report)
    if not path.is_file():
        abort(404)
    return _send(path.read_bytes(), "doklad-temi-{}-{}.docx".format(
        report_id, report["generated_at"][:10]))
