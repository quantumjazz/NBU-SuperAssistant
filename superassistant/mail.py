"""Every message NBU-SuperAssistant sends leaves through this module.

The relay code is copied from CourseBench (`coursebench/mail.py`): SMTP with
the standard library, a configured sender, and a failure that is raised and
never swallowed, so the person waiting is always told.

What is new here is the mail mode (CLAUDE.md "Mail"; NOW.md proof 4):

  owner    every message goes to SUPERASSISTANT_OWNER_EMAIL instead, with the
           intended recipient written at its top;
  console  every message is printed, never sent;
  unset    the same as console.

No mode in this milestone sends to the intended recipient: that comes with the
deployment. Tests replace the relay with a fake (set_relay) and never send.
"""

import smtplib
import socket
import ssl
import sys
from email.message import EmailMessage
from email.utils import formataddr, parseaddr

from superassistant import texts

TIMEOUT_SECONDS = 15
FROM_NAME = "NBU-SuperAssistant"
_SECURITIES = ("starttls", "ssl", "none")
_DEFAULT_PORTS = {"starttls": 587, "ssl": 465, "none": 25}


class MailFailed(RuntimeError):
    """The message was not sent. Never raised silently; always shown."""


def valid_address(address):
    """Whether this could be an email address. Deliberately loose."""
    address = (address or "").strip()
    name, addr = parseaddr(address)
    if not addr or addr != address:
        return False
    local, _, domain = addr.partition("@")
    if not local or not domain or "." not in domain or "@" in domain:
        return False
    return not any(ch.isspace() for ch in addr)


class Message(object):
    """One message: who it is for, its subject, its text and optional HTML."""

    def __init__(self, to, subject, text, html=None):
        self.to = (to or "").strip()
        self.subject = subject
        self.text = text
        self.html = html


# --- The relay -------------------------------------------------------------

def _security(settings):
    value = (settings.smtp_security or "").strip().lower() or "starttls"
    return value if value in _SECURITIES else "starttls"


def _port(settings):
    try:
        return int(settings.smtp_port)
    except (TypeError, ValueError):
        return _DEFAULT_PORTS[_security(settings)]


def _ehlo_name(settings):
    if settings.smtp_ehlo:
        return settings.smtp_ehlo
    try:
        return socket.gethostname() or "localhost"
    except OSError:
        return "localhost"


def relay_problem(settings):
    """Why the relay cannot be used, as a sentence, or ""."""
    if not settings.smtp_host:
        return "SUPERASSISTANT_SMTP_HOST is not set."
    if not settings.mail_from:
        return "SUPERASSISTANT_MAIL_FROM is not set."
    if not valid_address(settings.mail_from):
        return ("SUPERASSISTANT_MAIL_FROM is " + repr(settings.mail_from)
                + ", which is not an email address.")
    return ""


def smtp_relay(settings, envelope):
    """Hand one EmailMessage to the configured relay. Raises on failure."""
    stopper = relay_problem(settings)
    if stopper:
        raise MailFailed(stopper)
    how = _security(settings)
    name = _ehlo_name(settings)
    if how == "ssl":
        server = smtplib.SMTP_SSL(settings.smtp_host, _port(settings),
                                  local_hostname=name,
                                  timeout=TIMEOUT_SECONDS,
                                  context=ssl.create_default_context())
    else:
        server = smtplib.SMTP(settings.smtp_host, _port(settings),
                              local_hostname=name, timeout=TIMEOUT_SECONDS)
    with server:
        server.ehlo()
        if how == "starttls":
            server.starttls(context=ssl.create_default_context())
            server.ehlo()
        if settings.smtp_username:
            server.login(settings.smtp_username, settings.smtp_password)
        server.send_message(envelope)


_relay = smtp_relay


def set_relay(fn):
    """Tests put a fake relay here; None restores SMTP."""
    global _relay
    _relay = fn or smtp_relay


# --- Sending ---------------------------------------------------------------

def _envelope(settings, to, subject, text, html):
    envelope = EmailMessage()
    envelope["From"] = formataddr((FROM_NAME, settings.mail_from or
                                   "superassistant@localhost"))
    envelope["To"] = to
    envelope["Subject"] = subject
    envelope.set_content(text)
    if html:
        envelope.add_alternative(html, subtype="html")
    return envelope


def send(settings, message, out=None):
    """Send one message in the configured mode, or raise MailFailed."""
    if not valid_address(message.to):
        raise MailFailed(texts.MAIL_BAD_ADDRESS)
    mode = settings.effective_mail_mode()
    if mode == "console":
        stream = out or sys.stdout
        stream.write("\n".join([
            "----- " + texts.MAIL_CONSOLE_HEADER + " -----",
            "To: " + message.to,
            "Subject: " + message.subject,
            "",
            message.text,
            "----- " + texts.MAIL_CONSOLE_FOOTER + " -----",
            "",
        ]))
        stream.flush()
        return
    # mode == "owner": to the owner, the intended recipient written on top.
    note = texts.MAIL_INTENDED_FOR.format(message.to)
    text = note + "\n\n" + message.text
    html = None
    if message.html:
        html = "<p><strong>" + texts.escape(note) + "</strong></p>" \
            + message.html
    envelope = _envelope(settings, settings.owner_email, message.subject,
                         text, html)
    try:
        _relay(settings, envelope)
    except MailFailed:
        raise
    except (smtplib.SMTPException, ssl.SSLError, OSError) as exc:
        raise MailFailed(texts.MAIL_FAILED + " " + str(exc))
