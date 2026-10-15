"""Every setting NBU-SuperAssistant reads, in one place.

All come from SUPERASSISTANT_* environment variables. A development copy runs
with none of them set: the data directory defaults to one outside the clone,
mail is printed rather than sent, and the session key is made on first start
and kept in the data directory, so no token or key is ever needed to run it.

On the host the same variables come from ".env.production" in the clone,
which systemd's EnvironmentFile reads for the service and load_settings_file
reads for wsgi.py and the host commands (`python -m superassistant ...`).
app.py and the tests never read it.

An installation whose SUPERASSISTANT_BASE_URL is not on this machine is
"hosted", and problem() asks more of it: https, records outside the clone,
and mail that leaves (CourseBench's coursebench/hosting.py,
check_configuration, is the model).
"""

import ipaddress
import os
import re
import secrets
from pathlib import Path

from superassistant import mail

PREFIX = "SUPERASSISTANT_"

# Mail modes. "send" delivers every message to its intended recipient; "owner"
# and "console" are the development modes (CLAUDE.md "Mail"), and unset means
# "console".
MAIL_MODES = ("send", "owner", "console")

# The clone: the folder holding the superassistant package and wsgi.py.
# Records kept under it are records a re-clone or a git clean can destroy.
CLONE_DIR = Path(__file__).resolve().parent.parent

# The host's settings file, in the clone (the form CourseBench's
# .env.production.example prescribes, which systemd's EnvironmentFile reads).
SETTINGS_FILE = CLONE_DIR / ".env.production"

_NAME = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")

# What systemd's EnvironmentFile trims around a name and a value. Not
# str.strip(), which also takes form feeds, NEL and no-break spaces.
_BLANKS = " \t\r"

# Where systemd's EnvironmentFile ends a line: at a line feed and at a
# carriage return alike, so "KEY=a\rb" gives KEY the value "a", and
# "D=x\ry=z" two settings. Checked on the host's systemd 255 with a
# transient unit on 11 October 2026 (Codex's M2-C1); a form feed, NEL or
# line separator ends no line.
_LINE_ENDS = re.compile("\r\n|\r|\n")


class SettingsFileError(Exception):
    """The settings file holds a line systemd would read differently."""


def load_settings_file(path=None, environ=None):
    """Read KEY=VALUE lines from the settings file into the environment.

    The approach of CourseBench's coursebench/hosting.py, load_environment:
    anchored to the clone, not the working directory, so a host command run
    from anywhere opens the records the service opens; and never overriding a
    variable already set, so the service unit's own environment always wins.
    Without python-dotenv: only the subset systemd's EnvironmentFile reads
    exactly as written is accepted. Blank lines and lines starting with "#"
    are skipped; so is a line with no "=" or with no variable name before
    it, as systemd skips them. A name given twice takes its later value, as
    in systemd.

    systemd removes quotes around a value and the backslashes in it, so the
    service would get "re_x" where a reader taking the line as written gets
    '"re_x"', and the host commands (mail-test above all) would test other
    settings than the service runs with. A value starting with a quote or
    holding a backslash is therefore refused, with SettingsFileError naming
    the line and the setting but never the value, and nothing is set.

    A missing file is no error: a development copy has none. Returns the
    names it set.
    """
    path = Path(SETTINGS_FILE if path is None else path)
    environ = os.environ if environ is None else environ
    try:
        text = path.read_bytes().decode("utf-8")
    except FileNotFoundError:
        return []
    values = {}
    for number, line in enumerate(_LINE_ENDS.split(text), start=1):
        line = line.strip(_BLANKS)
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip(_BLANKS)
        if not _NAME.fullmatch(key):
            continue
        value = value.strip(_BLANKS)
        if value[:1] in ("\"", "'") or "\\" in value:
            raise SettingsFileError(
                "{}, line {}: {} is written with quotes or a backslash, "
                "which systemd would remove, so the service and the host "
                "commands would read different values. Write it bare: "
                "KEY=value, no quotes.".format(path, number, key))
        values[key] = value
    loaded = []
    for key, value in values.items():
        if key not in environ:
            environ[key] = value
            loaded.append(key)
    return loaded


# --- The base URL --------------------------------------------------------------

# scheme://netloc then whatever follows; the netloc ends at the first "/", "?"
# or "#". Parsed here rather than with urllib.parse.urlsplit, whose handling
# of ports, stray characters and empty queries differs between Python 3.9 and
# 3.12.
_URL = re.compile(r"(?P<scheme>[^:/?#]*)://(?P<netloc>[^/?#]*)(?P<rest>.*)",
                  re.S)
# A host as a browser could resolve it: a name or an IPv4 address, or an IPv6
# address in brackets. Deliberately loose, as in CourseBench (hosting._HOST):
# the job is to catch what cannot be a host at all.
_HOST = re.compile(r"[A-Za-z0-9._-]+|\[[0-9A-Fa-f:.]+\]")
_PORT = re.compile(r"[0-9]{1,5}")
_LOCAL_ADDRESSES = (ipaddress.ip_address("127.0.0.1"),
                    ipaddress.ip_address("::1"))


def _split_host(netloc):
    """(host, port text or None) of a netloc without userinfo."""
    if netloc.startswith("["):
        end = netloc.find("]")
        if end < 0:
            return netloc, None
        host, after = netloc[:end + 1], netloc[end + 1:]
        if not after:
            return host, None
        if after.startswith(":"):
            return host, after[1:]
        return netloc, None
    host, colon, port = netloc.rpartition(":")
    if not colon:
        return netloc, None
    return host, port


def base_url_host(base_url):
    """The host of a base URL, lower case and unbracketed, or ""."""
    found = _URL.fullmatch(base_url or "")
    if not found or "@" in found.group("netloc"):
        return ""
    host, _ = _split_host(found.group("netloc"))
    return host.strip("[]").lower()


def is_local_host(host):
    """Whether a host is this machine: localhost, 127.0.0.1 or ::1."""
    host = (host or "").lower()
    if host == "localhost":
        return True
    try:
        return ipaddress.ip_address(host) in _LOCAL_ADDRESSES
    except ValueError:
        return False


def base_url_problem(base_url):
    """Why this cannot be the address links are built on, or "".

    A base URL is joined to a path in every link a message carries, so it must
    be exactly scheme://host[:port]: anything after it would break the links,
    and a username or password would be handed to everybody who gets one.
    """
    name = "SUPERASSISTANT_BASE_URL"
    if "@" in base_url:
        # Not repeated here: it may hold a password.
        return (name + " has \"@\" in it, as a username or password would; "
                "every link in every message would hand it out. Use just the "
                "scheme and the host.")
    found = _URL.fullmatch(base_url)
    if not found or found.group("scheme") not in ("http", "https"):
        return (name + " is " + repr(base_url) + "; it must start with "
                "\"https://\" (or \"http://\" on this machine), followed by "
                "the host.")
    if found.group("rest"):
        return (name + " is " + repr(base_url) + ", which has a path, a "
                "query or a \"#\" after the host; every link is this plus a "
                "path, so use just the scheme and the host.")
    host, port = _split_host(found.group("netloc"))
    if not _HOST.fullmatch(host):
        return (name + " is " + repr(base_url) + ", which names no host a "
                "browser could open.")
    if port is not None and not (_PORT.fullmatch(port)
                                 and 1 <= int(port) <= 65535):
        return (name + " is " + repr(base_url) + ", whose port is not a "
                "number from 1 to 65535.")
    return ""


class Settings(object):
    """The settings one running instance uses.

    Built from the environment by from_env(); tests build one directly with
    keyword arguments, so no test depends on the shell it runs in. A data
    directory given that way counts as set explicitly.
    """

    def __init__(self, data_dir, mail_mode="", owner_email="", owner_username="",
                 base_url="http://127.0.0.1:5002", reminder_days=3,
                 reminder_count=2, smtp_host="", smtp_port="", smtp_security="",
                 smtp_username="", smtp_password="", mail_from="", smtp_ehlo="",
                 secret_key="", client_ip_header="", data_dir_explicit=True):
        self.data_dir = Path(data_dir)
        self.data_dir_explicit = bool(data_dir_explicit)
        self.mail_mode = (mail_mode or "").strip().lower()
        self.owner_email = (owner_email or "").strip()
        self.owner_username = (owner_username or "").strip()
        self.base_url = (base_url or "").rstrip("/")
        # Kept as given too, so a value that is no whole number is refused
        # by name (problems) rather than raised as a traceback here.
        self.reminder_numbers = {
            "SUPERASSISTANT_REMINDER_DAYS": reminder_days,
            "SUPERASSISTANT_REMINDER_COUNT": reminder_count}
        self.reminder_days = _whole_number(reminder_days)
        self.reminder_count = _whole_number(reminder_count)
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.smtp_security = smtp_security
        self.smtp_username = smtp_username
        self.smtp_password = smtp_password
        self.mail_from = mail_from
        self.smtp_ehlo = smtp_ehlo
        self.secret_key = secret_key
        self.client_ip_header = (client_ip_header or "").strip()

    @property
    def db_path(self):
        return self.data_dir / "superassistant.sqlite3"

    @property
    def lists_dir(self):
        return self.data_dir / "lists"

    @property
    def reports_dir(self):
        return self.data_dir / "reports"

    @property
    def snapshots_dir(self):
        """The nightly copies of the applications (snapshot.py)."""
        return self.data_dir / "snapshots"

    def is_hosted(self):
        """Whether the base URL is somewhere other than this machine."""
        return not is_local_host(base_url_host(self.base_url))

    def mail_problems(self):
        """Why mail cannot go as the settings say, as sentences."""
        if self.mail_mode and self.mail_mode not in MAIL_MODES:
            return ["SUPERASSISTANT_MAIL_MODE is " + repr(self.mail_mode)
                    + "; it must be \"send\", \"owner\", \"console\" or "
                    "unset."]
        if self.mail_mode == "owner" and not self.owner_email:
            return ["SUPERASSISTANT_MAIL_MODE is \"owner\" but "
                    "SUPERASSISTANT_OWNER_EMAIL is not set."]
        if self.mail_mode == "send":
            stopper = mail.relay_problem(self)
            if stopper:
                return ["SUPERASSISTANT_MAIL_MODE is \"send\", but no message "
                        "could leave: " + stopper]
        return []

    def problems(self):
        """Why these settings cannot run, as sentences; empty if they can."""
        found = self.mail_problems()
        if self.reminder_days is None or self.reminder_count is None:
            for name, given in sorted(self.reminder_numbers.items()):
                if _whole_number(given) is None:
                    found.append(name + " is " + repr(given)
                                 + "; it must be a whole number.")
        elif self.reminder_days < 1 or self.reminder_count < 0:
            found.append("SUPERASSISTANT_REMINDER_DAYS must be at least 1 and "
                         "SUPERASSISTANT_REMINDER_COUNT at least 0.")
        address = base_url_problem(self.base_url)
        if address:
            found.append(address)
        if address or not self.is_hosted():
            return found
        # Hosted: reachable from elsewhere, holding real people's records.
        if not self.base_url.startswith("https://"):
            found.append(
                "SUPERASSISTANT_BASE_URL is " + repr(self.base_url) + ", "
                "which is not https; over plain http sign-in links, codes "
                "and passwords travel in the clear. Plain http is allowed "
                "only for localhost, 127.0.0.1 or ::1.")
        if not self.data_dir_explicit:
            found.append(
                "SUPERASSISTANT_DATA_DIR is not set; a hosted installation "
                "names its records folder explicitly, outside the clone.")
        elif self.records_inside_clone():
            found.append(
                "SUPERASSISTANT_DATA_DIR is " + str(self.data_dir) + ", "
                "which is inside the clone (" + str(CLONE_DIR) + "), where "
                "re-cloning or cleaning the code destroys it. Put the "
                "records beside the clone, not in it.")
        if self.effective_mail_mode() == "console":
            found.append(
                "SUPERASSISTANT_MAIL_MODE is "
                + (repr(self.mail_mode) if self.mail_mode else "not set")
                + ", so mail would only be printed: students' sign-in links "
                "and supervisors' requests would never arrive. Use \"send\" "
                "(or \"owner\" while testing).")
        return found

    def problem(self):
        """Why these settings cannot run, as sentences in one line, or ""."""
        return " ".join(self.problems())

    def records_inside_clone(self):
        """Whether the data directory is the clone or inside it.

        realpath, not abspath, as CourseBench's hosting._inside_application:
        a directory outside the clone can be a symlink into it, and it is
        where the bytes land that a re-clone destroys. A relative path is
        resolved as the application will use it, against the working
        directory.
        """
        resolved = os.path.realpath(str(self.data_dir))
        clone = os.path.realpath(str(CLONE_DIR))
        return resolved == clone or resolved.startswith(clone + os.sep)

    def effective_mail_mode(self):
        """What happens to a message: "send", "owner" or "console".

        Unset prints, as "console" does."""
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


def _whole_number(given):
    """given as an int, or None if it is no whole number."""
    try:
        return int(given)
    except (TypeError, ValueError):
        return None


def _env(name, default=""):
    return (os.environ.get(PREFIX + name) or default).strip()


def from_env():
    """The settings the environment gives."""
    explicit = _env("DATA_DIR")
    data_dir = explicit or str(Path.home() / "superassistant-data")
    return Settings(
        data_dir=data_dir,
        data_dir_explicit=bool(explicit),
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
        client_ip_header=_env("CLIENT_IP_HEADER"),
    )
