"""Every setting NBU-SuperAssistant reads, in one place.

All come from SUPERASSISTANT_* environment variables. A development copy runs
with none of them set: the data directory defaults to one outside the clone,
mail is printed rather than sent, and the session key is made on first start
and kept in the data directory, so no token or key is ever needed to run it.
"""

import os
import secrets
from pathlib import Path

PREFIX = "SUPERASSISTANT_"

# Mail modes this milestone knows. Sending to the intended recipient is
# deferred with the deployment (NOW.md, DEFERRED), so there is no such mode.
MAIL_MODES = ("owner", "console")


class Settings(object):
    """The settings one running instance uses.

    Built from the environment by from_env(); tests build one directly with
    keyword arguments, so no test depends on the shell it runs in.
    """

    def __init__(self, data_dir, mail_mode="", owner_email="", owner_username="",
                 base_url="http://127.0.0.1:5002", reminder_days=3,
                 reminder_count=2, smtp_host="", smtp_port="", smtp_security="",
                 smtp_username="", smtp_password="", mail_from="", smtp_ehlo="",
                 secret_key=""):
        self.data_dir = Path(data_dir)
        self.mail_mode = (mail_mode or "").strip().lower()
        self.owner_email = (owner_email or "").strip()
        self.owner_username = (owner_username or "").strip()
        self.base_url = (base_url or "").rstrip("/")
        self.reminder_days = int(reminder_days)
        self.reminder_count = int(reminder_count)
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.smtp_security = smtp_security
        self.smtp_username = smtp_username
        self.smtp_password = smtp_password
        self.mail_from = mail_from
        self.smtp_ehlo = smtp_ehlo
        self.secret_key = secret_key

    @property
    def db_path(self):
        return self.data_dir / "superassistant.sqlite3"

    @property
    def lists_dir(self):
        return self.data_dir / "lists"

    @property
    def reports_dir(self):
        return self.data_dir / "reports"

    def problem(self):
        """Why these settings cannot run, as a sentence, or ""."""
        if self.mail_mode and self.mail_mode not in MAIL_MODES:
            return ("SUPERASSISTANT_MAIL_MODE is " + repr(self.mail_mode)
                    + "; it must be \"owner\", \"console\" or unset.")
        if self.mail_mode == "owner" and not self.owner_email:
            return ("SUPERASSISTANT_MAIL_MODE is \"owner\" but "
                    "SUPERASSISTANT_OWNER_EMAIL is not set.")
        if self.reminder_days < 1 or self.reminder_count < 0:
            return ("SUPERASSISTANT_REMINDER_DAYS must be at least 1 and "
                    "SUPERASSISTANT_REMINDER_COUNT at least 0.")
        return ""

    def effective_mail_mode(self):
        """What happens to a message: "owner" or "console". Unset prints."""
        return self.mail_mode or "console"

    def ensure_secret_key(self):
        """The session key: configured, or made once and kept with the data."""
        if self.secret_key:
            return self.secret_key
        path = self.data_dir / "secret_key"
        if path.exists():
            self.secret_key = path.read_text(encoding="utf-8").strip()
        if not self.secret_key:
            self.secret_key = secrets.token_hex(32)
            path.write_text(self.secret_key, encoding="utf-8")
            try:
                os.chmod(str(path), 0o600)
            except OSError:
                pass
        return self.secret_key


def _env(name, default=""):
    return (os.environ.get(PREFIX + name) or default).strip()


def from_env():
    """The settings the environment gives."""
    data_dir = _env("DATA_DIR") or str(Path.home() / "superassistant-data")
    return Settings(
        data_dir=data_dir,
        mail_mode=_env("MAIL_MODE"),
        owner_email=_env("OWNER_EMAIL"),
        owner_username=_env("OWNER_USERNAME"),
        base_url=_env("BASE_URL", "http://127.0.0.1:5002"),
        reminder_days=_env("REMINDER_DAYS", "3"),
        reminder_count=_env("REMINDER_COUNT", "2"),
        smtp_host=_env("SMTP_HOST"),
        smtp_port=_env("SMTP_PORT"),
        smtp_security=_env("SMTP_SECURITY"),
        smtp_username=_env("SMTP_USERNAME"),
        smtp_password=os.environ.get(PREFIX + "SMTP_PASSWORD") or "",
        mail_from=_env("MAIL_FROM"),
        smtp_ehlo=_env("SMTP_EHLO"),
        secret_key=_env("SECRET_KEY"),
    )
