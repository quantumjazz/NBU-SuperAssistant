"""The supervisor's answer, through the links in the request (NOW.md req. 3).

GET only shows a page: mail systems open links to scan them, so opening a
link records nothing (8.2). The page's own button records the answer, with an
optional comment that only staff see. After an answer, the links only show
it; a replaced request's links record nothing.
"""

from flask import Blueprint, abort, render_template, request

from superassistant import applications, mail, supervision, texts
from superassistant import web

blueprint = Blueprint("supervisor", __name__)


def _page(request_row, choice, state, notice_failed=False, status=200):
    record = applications.get(web.connection(), request_row["application_id"])
    lists = web.current_lists()
    return render_template(
        "answer.html", state=state, choice=choice, request_row=request_row,
        student=applications.full_name(record), topic=record["topic"],
        programme=supervision.programme_label(record, lists),
        notice_failed=notice_failed), status


@blueprint.route("/answer/<token>/<choice>")
def show(token, choice):
    if choice not in supervision.CHOICES:
        abort(404)
    row = supervision.find(web.connection(), token)
    if row is None:
        return render_template("answer.html", state="unknown"), 404
    if row["answer"] is not None:
        return _page(row, choice, "answered")
    if row["replaced_at"] is not None:
        return _page(row, choice, "replaced")
    return _page(row, choice, "open")


@blueprint.route("/answer/<token>/<choice>", methods=["POST"])
def record(token, choice):
    if choice not in supervision.CHOICES:
        abort(404)
    state, row = supervision.answer(web.connection(), token, choice,
                                    request.form.get("comment", ""))
    if state == "unknown":
        return render_template("answer.html", state="unknown"), 404
    notice_failed = False
    if state == "recorded" and row["answer"] == "decline":
        try:
            supervision.tell_student_of_decline(
                web.connection(), web.settings(), web.current_lists(), row)
        except mail.MailFailed:
            notice_failed = True
    return _page(row, choice, state, notice_failed)
