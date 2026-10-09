"""Signing in and out: students by an emailed link or code, staff by a
username or email address and a password (NOW.md requirements 1 and 5;
constitution 5.2, 6.5 and 6.6).

The rules are in superassistant/signin.py and superassistant/accounts.py;
these views only turn their answers into pages. Every refusal is one sentence
that does not say which part was wrong.
"""

from flask import Blueprint, redirect, render_template, request, session

from superassistant import accounts, mail, signin, texts
from superassistant import web

blueprint = Blueprint("auth", __name__)

# The session keys of a sign-in waiting for its code.
PENDING = "signin"
PENDING_EMAIL = "signin_email"


# --- Students --------------------------------------------------------------

@blueprint.route("/")
def start():
    if web.session_student() is not None:
        return redirect("/application")
    if web.session_staff() is not None:
        return redirect("/staff")
    return render_template("signin.html", email="", error="")


@blueprint.route("/sign-in", methods=["POST"])
def ask():
    address = (request.form.get("email") or "").strip()
    try:
        pending = signin.offer(web.connection(), web.settings(), address,
                               web.source())
    except signin.BadAddress:
        return render_template("signin.html", email=address,
                               error=texts.MAIL_BAD_ADDRESS), 400
    except signin.TooMany:
        return render_template("signin.html", email=address,
                               error=texts.SIGNIN_TOO_MANY), 429
    except mail.MailFailed:
        return render_template("signin.html", email=address,
                               error=texts.SIGNIN_NOT_SENT), 502
    session[PENDING] = pending
    session[PENDING_EMAIL] = address
    return redirect("/sign-in/code")


@blueprint.route("/sign-in/code")
def code_page():
    if not session.get(PENDING):
        return redirect("/")
    return render_template("signin_code.html",
                           email=session.get(PENDING_EMAIL) or "", error="")


@blueprint.route("/sign-in/code", methods=["POST"])
def code():
    row = signin.check_code(web.connection(), session.get(PENDING),
                            request.form.get("code"))
    if row is None:
        return render_template("signin_code.html",
                               email=session.get(PENDING_EMAIL) or "",
                               error=texts.SIGNIN_REFUSED), 400
    web.sign_in_student(row["email_key"], row["email"])
    return redirect("/application")


@blueprint.route("/link/<token>")
def link_page(token):
    """Shows the „Влез“ button and spends nothing: mail scanners open links."""
    if signin.open_link(web.connection(), token) is None:
        return render_template("signin_link.html", token="",
                               error=texts.SIGNIN_REFUSED), 400
    return render_template("signin_link.html", token=token, error="")


@blueprint.route("/link/<token>", methods=["POST"])
def link(token):
    row = signin.spend_link(web.connection(), token)
    if row is None:
        return render_template("signin_link.html", token="",
                               error=texts.SIGNIN_REFUSED), 400
    web.sign_in_student(row["email_key"], row["email"])
    return redirect("/application")


@blueprint.route("/sign-out", methods=["POST"])
def sign_out():
    web.sign_out()
    return redirect("/")


# --- Staff -----------------------------------------------------------------

@blueprint.route("/staff/register", methods=["GET", "POST"])
def staff_register():
    form = {"username": "", "email": ""}
    if request.method == "GET":
        return render_template("staff_register.html", form=form, error="",
                               done=None)
    form = {"username": request.form.get("username") or "",
            "email": request.form.get("email") or ""}
    password = request.form.get("password") or ""
    if password and password != (request.form.get("password2") or ""):
        return render_template(
            "staff_register.html", form=form, done=None,
            error=texts.STAFF_REGISTER_ERRORS["mismatch"]), 400
    try:
        record = accounts.create(web.connection(), form["username"],
                                 form["email"], password)
    except accounts.AccountError as exc:
        return render_template(
            "staff_register.html", form=form, done=None,
            error=texts.STAFF_REGISTER_ERRORS[str(exc)]), 400
    owner = accounts.is_owner(record, web.settings())
    return render_template(
        "staff_register.html", form=form, error="",
        done=texts.STAFF_REGISTERED_OWNER if owner
        else texts.STAFF_REGISTERED_WAITING)


@blueprint.route("/staff/sign-in", methods=["GET", "POST"])
def staff_sign_in():
    if request.method == "GET":
        if web.session_staff() is not None:
            return redirect("/staff")
        return render_template("staff_signin.html", login="", error="")
    login = (request.form.get("login") or "").strip()
    record = accounts.by_login(web.connection(), login)
    if not accounts.verify_password(record, request.form.get("password")):
        return render_template("staff_signin.html", login=login,
                               error=texts.STAFF_SIGNIN_FAILED), 400
    if not accounts.approved(record, web.settings()):
        return render_template("staff_signin.html", login=login,
                               error=texts.STAFF_SIGNIN_WAITING), 403
    web.sign_in_staff(record)
    return redirect("/staff")
