"""The supervisor's request, answer and reminders (NOW.md requirement 3).

A request is a row in `requests`. It carries two links, one per answer, made
from one token. The token is not stored: it is derived from the session key
and the request (an HMAC), and only its SHA-256 is kept, so the records alone
are not a list of live links (CLAUDE.md: links "stored hashed"); and because
it can be derived again, every reminder carries the same links as the request.

The links work until an answer is recorded or the request is replaced (by the
student choosing again after a decline, or by staff changing the supervisor);
afterwards they only show the answer, if one was recorded. Opening a link
records nothing: the page it opens has the button that does (8.2).

Every message is sent inside the transaction that records it, so a message
the relay refuses leaves nothing recorded as sent.
"""

import base64
import hashlib
import hmac
from datetime import timedelta

from superassistant import applications, db, mail, texts

CHOICES = ("confirm", "decline")


# --- Tokens ----------------------------------------------------------------

def _token(settings, request_id, created_at):
    key = settings.ensure_secret_key().encode("utf-8")
    message = "supervisor-request|{}|{}".format(request_id, created_at)
    digest = hmac.new(key, message.encode("utf-8"), hashlib.sha256).digest()
    return base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")


def token_hash(token):
    return hashlib.sha256((token or "").encode("utf-8")).hexdigest()


def token_for(settings, request):
    return _token(settings, request["id"], request["created_at"])


def find(connection, token):
    return connection.execute("SELECT * FROM requests WHERE token_hash = ?",
                              (token_hash(token),)).fetchone()


def links(settings, token):
    base = settings.base_url + "/answer/" + token + "/"
    return base + "confirm", base + "decline"


# --- The messages ----------------------------------------------------------

def programme_label(record, lists):
    programme = lists.programmes.get(record["programme"])
    if programme is None:
        return ""
    return "{} „{}“, {}".format(programme["degree"], programme["name"],
                                programme["form"])


def thesis_kind(record, lists):
    programme = lists.programmes.get(record["programme"])
    if programme is not None and programme["degree"] == "МП":
        return texts.THESIS_MASTER
    return texts.THESIS_BACHELOR


def _request_message(settings, lists, record, token, reminder):
    confirm, decline = links(settings, token)
    label = applications.supervisor_label(record, lists)
    proposal = "\n\n".join(
        texts.FIELD_LABELS[field] + ":\n" + record[field]
        for field in db.PROPOSAL_FIELDS)
    values = {
        "supervisor": label,
        "student": applications.full_name(record),
        "fn": record["fn"],
        "programme": programme_label(record, lists),
        "kind": thesis_kind(record, lists),
        "topic": record["topic"],
        "proposal": proposal,
        "confirm": confirm,
        "decline": decline,
    }
    subject = (texts.REMINDER_SUBJECT if reminder
               else texts.REQUEST_SUBJECT).format(**values)
    text = texts.REQUEST_TEXT.format(**values)
    escaped = dict((k, texts.escape(v)) for k, v in values.items())
    escaped["proposal"] = "".join(
        "<h3>" + texts.escape(texts.FIELD_LABELS[field]) + "</h3><p>"
        + texts.escape(record[field]).replace("\n", "<br>") + "</p>"
        for field in db.PROPOSAL_FIELDS)
    html = texts.REQUEST_HTML.format(**escaped)
    if reminder:
        text = texts.REMINDER_LEAD + "\n\n" + text
        html = "<p>" + texts.escape(texts.REMINDER_LEAD) + "</p>" + html
    to = applications.supervisor_email(record, lists)
    return mail.Message(to, subject, text, html)


def _decline_message(settings, lists, record, request):
    values = {"student": applications.full_name(record),
              "supervisor": request_label(request, lists),
              "link": settings.base_url + "/application"}
    return mail.Message(record["email"],
                        texts.DECLINE_SUBJECT.format(**values),
                        texts.DECLINE_TEXT.format(**values))


def request_label(request, lists):
    """Who a request went to, as written at the time it was made."""
    if request["professor"] and request["professor"] in lists.professors:
        return lists.professor_label(request["professor"])
    return " ".join(part for part in (request["sup_title"],
                                      request["sup_name"]) if part)


# --- Making a request (always inside the caller's transaction) -------------

def _replace_current(connection, application_id):
    connection.execute(
        "UPDATE requests SET replaced_at = ? WHERE application_id = ? AND "
        "replaced_at IS NULL", (db.now(), application_id))


def _send_new_request(connection, settings, lists, application_id):
    """Insert a request for the application's supervisor and send it.

    The caller holds the transaction: if the relay refuses, the caller rolls
    back and nothing is recorded as sent.
    """
    record = applications.get(connection, application_id)
    stamp = db.now()
    placeholder = "pending:" + token_hash(str(application_id) + stamp
                                          + str(id(record)))
    cursor = connection.execute(
        "INSERT INTO requests (application_id, created_at, professor, "
        "sup_name, sup_title, sup_email, token_hash) VALUES (?,?,?,?,?,?,?)",
        (application_id, stamp, record["professor"], record["sup_name"],
         record["sup_title"], applications.supervisor_email(record, lists),
         placeholder))
    request_id = cursor.lastrowid
    token = _token(settings, request_id, stamp)
    connection.execute("UPDATE requests SET token_hash = ? WHERE id = ?",
                       (token_hash(token), request_id))
    mail.send(settings, _request_message(settings, lists, record, token,
                                         reminder=False))
    connection.execute(
        "UPDATE requests SET sent_at = ?, last_mailed_at = ? WHERE id = ?",
        (db.now(), db.now(), request_id))
    return request_id


def submit(connection, settings, lists, application_id):
    """Submit an application. Returns a list of Refusals, empty on success.

    A thesis is submitted only once its request to the supervisor has gone:
    if the relay refuses it, mail.MailFailed propagates and nothing changes.
    """
    with db.transaction(connection):
        record = applications.get(connection, application_id)
        if record["submitted_at"] is not None:
            return []
        missing = applications.missing_for_submission(record)
        if missing:
            return missing
        connection.execute(
            "UPDATE applications SET submitted_at = ?, updated_at = ? "
            "WHERE id = ?", (db.now(), db.now(), application_id))
        if record["grad_type"] == "thesis":
            _send_new_request(connection, settings, lists, application_id)
    return []


def supervisor_values(values):
    """A supervisor is either a listed professor or a typed one, never both."""
    if values.get("professor"):
        return {"professor": values["professor"], "sup_name": "",
                "sup_title": "", "sup_email": ""}
    return {"professor": "", "sup_name": values.get("sup_name", ""),
            "sup_title": values.get("sup_title", ""),
            "sup_email": values.get("sup_email", "")}


def choose_again(connection, settings, lists, application_id, values):
    """The student names another supervisor after a decline.

    Returns Refusals; raises mail.MailFailed (nothing changed) if the new
    request cannot be sent; raises PermissionError if no decline stands.
    """
    with db.transaction(connection):
        record = applications.get(connection, application_id)
        current = applications.current_request(connection, application_id)
        if (record["submitted_at"] is None or record["grad_type"] != "thesis"
                or current is None or current["answer"] != "decline"):
            raise PermissionError("no decline")
        chosen = supervisor_values(values)
        missing = applications.supervisor_missing(chosen)
        if missing:
            return [applications.Refusal(field, "required")
                    for field in missing]
        connection.execute(
            "UPDATE applications SET professor = ?, sup_name = ?, "
            "sup_title = ?, sup_email = ?, updated_at = ? WHERE id = ?",
            (chosen["professor"], chosen["sup_name"], chosen["sup_title"],
             chosen["sup_email"], db.now(), application_id))
        _replace_current(connection, application_id)
        _send_new_request(connection, settings, lists, application_id)
    return []


def staff_change(connection, settings, lists, application_id, values,
                 account_id):
    """Staff change the supervisor or the supervisor's address.

    The change is a correction (each field keeps the value it replaces); the
    request standing is replaced by a new one, and an answer already recorded
    stays with the earlier request. Returns Refusals; raises mail.MailFailed
    (nothing changed) if the new request cannot be sent.
    """
    with db.transaction(connection):
        record = applications.get(connection, application_id)
        if record["submitted_at"] is None or record["grad_type"] != "thesis":
            raise PermissionError("not a submitted thesis")
        chosen = supervisor_values(values)
        missing = applications.supervisor_missing(chosen)
        if missing:
            return [applications.Refusal(field, "required")
                    for field in missing]
        changed = applications.correct(connection, record, chosen, account_id)
        if not changed:
            return []
        _replace_current(connection, application_id)
        _send_new_request(connection, settings, lists, application_id)
    return []


# --- Answering -------------------------------------------------------------

def answer(connection, token, choice, comment):
    """Record a supervisor's answer through a link.

    Returns (state, request): state is "recorded", "answered" (an answer was
    already recorded; nothing changes), "replaced" (the request is no longer
    standing; nothing changes) or "unknown".
    """
    if choice not in CHOICES:
        return "unknown", None
    with db.transaction(connection):
        request = find(connection, token)
        if request is None:
            return "unknown", None
        if request["answer"] is not None:
            return "answered", request
        if request["replaced_at"] is not None:
            return "replaced", request
        connection.execute(
            "UPDATE requests SET answer = ?, comment = ?, answered_at = ? "
            "WHERE id = ? AND answer IS NULL AND replaced_at IS NULL",
            (choice, (comment or "").strip(), db.now(), request["id"]))
    return "recorded", find(connection, token)


def tell_student_of_decline(connection, settings, lists, request):
    """The decline notice. Raises mail.MailFailed; the answer stays recorded."""
    record = applications.get(connection, request["application_id"])
    mail.send(settings, _decline_message(settings, lists, record, request))


# --- Reminders -------------------------------------------------------------

def due(connection, settings):
    """Requests whose supervisor should be reminded now (8.4).

    Standing, unanswered, sent, fewer reminders than the setting allows, and
    the request or its latest reminder at least the set days old, so a second
    run on the same day finds nothing more.
    """
    cutoff = (db.now_dt() - timedelta(days=settings.reminder_days)).isoformat(
        timespec="seconds")
    return connection.execute(
        "SELECT requests.* FROM requests JOIN applications ON applications.id"
        " = requests.application_id WHERE requests.replaced_at IS NULL AND "
        "requests.answer IS NULL AND requests.sent_at IS NOT NULL AND "
        "requests.reminders_sent < ? AND requests.last_mailed_at <= ? AND "
        "applications.submitted_at IS NOT NULL ORDER BY requests.id",
        (settings.reminder_count, cutoff)).fetchall()


def remind(connection, settings, lists):
    """Send every reminder due. Returns (sent request ids, failures).

    Each reminder is recorded only once the relay has accepted it; a failure
    is returned with its reason and leaves the request as it was.
    """
    sent, failed = [], []
    for request in due(connection, settings):
        try:
            with db.transaction(connection):
                fresh = connection.execute(
                    "SELECT * FROM requests WHERE id = ?",
                    (request["id"],)).fetchone()
                if (fresh["answer"] is not None
                        or fresh["replaced_at"] is not None
                        or fresh["reminders_sent"] != request["reminders_sent"]):
                    continue
                record = applications.get(connection, fresh["application_id"])
                mail.send(settings, _request_message(
                    settings, lists, record, token_for(settings, fresh),
                    reminder=True))
                connection.execute(
                    "UPDATE requests SET reminders_sent = reminders_sent + 1, "
                    "last_mailed_at = ? WHERE id = ?", (db.now(), fresh["id"]))
            sent.append(request["id"])
        except mail.MailFailed as exc:
            failed.append((request, str(exc)))
    return sent, failed
