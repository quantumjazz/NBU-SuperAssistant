"""`python -m superassistant owner-password`: a new password for the owner's
own account, typed on the host (constitution 6.5).

Copied in approach from CourseBench (`coursebench/admin.py`, cmd_passwd and
ask_password): the password is read twice with getpass, never from the
command line, and setting it signs every browser on that account out. The
account is the one SUPERASSISTANT_OWNER_USERNAME names; no emailed code or
link exists for it. --stdin reads it once from standard input instead, for
tests and scripted use.
"""

import argparse
import getpass
import sys

from superassistant import accounts, db, texts
from superassistant.settings import from_env


def _fail(line):
    sys.stderr.write(line + "\n")
    return 1


def _read_password(username, from_stdin):
    """The new password, or None after saying why there is none."""
    if from_stdin:
        password = sys.stdin.readline().rstrip("\r\n")
    else:
        password = getpass.getpass(texts.CLI_PASSWORD_PROMPT.format(username))
        if password and password != getpass.getpass(texts.CLI_PASSWORD_AGAIN):
            _fail(texts.CLI_PASSWORD_MISMATCH)
            return None
    if not password:
        _fail(texts.CLI_PASSWORD_EMPTY)
        return None
    return password


def main(argv=None):
    parser = argparse.ArgumentParser(prog="python -m superassistant "
                                          "owner-password")
    parser.add_argument("--stdin", action="store_true",
                        help="read the new password once from standard input")
    args = parser.parse_args(list(sys.argv[1:] if argv is None else argv))
    settings = from_env()
    if not settings.owner_username:
        return _fail(texts.CLI_NO_OWNER_SETTING)
    if not settings.db_path.exists():
        return _fail(texts.CLI_NO_RECORDS.format(settings.data_dir,
                                                 settings.owner_username))
    db.migrate(settings.db_path)
    connection = db.connect(settings.db_path)
    try:
        record = accounts.by_username(connection, settings.owner_username)
        if record is None:
            return _fail(texts.CLI_NO_ACCOUNT.format(settings.data_dir,
                                                     settings.owner_username))
        password = _read_password(record["username"], args.stdin)
        if password is None:
            return 1
        accounts.set_password(connection, record["id"], password,
                              by="host command")
    finally:
        connection.close()
    print(texts.CLI_PASSWORD_SET.format(record["username"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
