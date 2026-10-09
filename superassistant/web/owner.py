"""The owner's page: approving staff accounts and setting their passwords
(NOW.md requirement 5; constitution 6.5, decision 8.1 "An owner page in the
app").

Only the account SUPERASSISTANT_OWNER_USERNAME names reaches it. A new
password is set here and the owner tells the person; nothing is emailed,
because no staff password is ever reset through mail.
"""

from flask import Blueprint, abort, flash, redirect, render_template, request

from superassistant import accounts, texts
from superassistant import web

blueprint = Blueprint("owner", __name__)


def _account_or_404(account_id):
    record = accounts.get(web.connection(), account_id)
    if record is None:
        abort(404)
    return record


@blueprint.route("/owner")
@web.owner_required
def page():
    settings = web.settings()
    everyone = accounts.all_accounts(web.connection())
    rows = []
    for record in everyone:
        if accounts.is_owner(record, settings):
            state = texts.OWNER_STATE_OWNER
        elif record["approved_at"] is not None:
            state = texts.OWNER_STATE_APPROVED
        else:
            state = texts.OWNER_STATE_WAITING
        rows.append({"record": record, "state": state})
    waiting = [record for record in everyone
               if not accounts.approved(record, settings)]
    return render_template("owner.html", waiting=waiting, rows=rows)


@blueprint.route("/owner/approve/<int:account_id>", methods=["POST"])
@web.owner_required
def approve(account_id):
    record = _account_or_404(account_id)
    accounts.approve(web.connection(), record["id"],
                     web.session_staff()["id"])
    flash(texts.OWNER_APPROVED.format(record["username"]), "ok")
    return redirect("/owner")


@blueprint.route("/owner/password/<int:account_id>", methods=["POST"])
@web.owner_required
def password(account_id):
    record = _account_or_404(account_id)
    new = request.form.get("password") or ""
    if not new:
        flash(texts.OWNER_PASSWORD_EMPTY, "error")
        return redirect("/owner")
    if new != (request.form.get("password2") or ""):
        flash(texts.OWNER_PASSWORD_MISMATCH, "error")
        return redirect("/owner")
    owner = web.session_staff()
    accounts.set_password(web.connection(), record["id"], new,
                          by="owner page")
    if record["id"] == owner["id"]:
        # The new tag signs out every other browser; this one stays in.
        web.sign_in_staff(accounts.get(web.connection(), owner["id"]))
    flash(texts.OWNER_PASSWORD_SET.format(record["username"]), "ok")
    return redirect("/owner")
