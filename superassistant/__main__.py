"""The command line on the host: `python -m superassistant <command>`.

  remind               send reminders to supervisors who have not answered
                       (the host runs it daily on a timer)
  owner-password       set a new password for the owner's own account
                       (constitution 6.5; no emailed code exists for it)
  mail-test <address>  send one test message for <address> the way every
                       message goes, and say whether the relay accepted it

Every command first reads the settings file .env.production in the clone, if
there is one, never overriding a variable already set (settings.py,
load_settings_file), so it opens the records and the mail settings the
service uses.
"""

import sys

COMMANDS = {
    "remind": "superassistant.reminders:main",
    "owner-password": "superassistant.owner_password:main",
    "mail-test": "superassistant.mail_test:main",
}


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or argv[0] not in COMMANDS:
        sys.stderr.write(__doc__)
        return 2
    from superassistant.settings import load_settings_file
    load_settings_file()
    module_name, _, function = COMMANDS[argv[0]].partition(":")
    module = __import__(module_name, fromlist=[function])
    return getattr(module, function)(argv[1:])


if __name__ == "__main__":
    sys.exit(main())
