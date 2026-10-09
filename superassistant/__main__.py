"""The command line on the host: `python -m superassistant <command>`.

  remind           send reminders to supervisors who have not answered
                   (NOW.md requirement 3; the host will later run it on a timer)
  owner-password   set a new password for the owner's own account
                   (constitution 6.5; no emailed code exists for it)
"""

import sys

COMMANDS = {
    "remind": "superassistant.reminders:main",
    "owner-password": "superassistant.owner_password:main",
}


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or argv[0] not in COMMANDS:
        sys.stderr.write(__doc__)
        return 2
    module_name, _, function = COMMANDS[argv[0]].partition(":")
    module = __import__(module_name, fromlist=[function])
    return getattr(module, function)(argv[1:])


if __name__ == "__main__":
    sys.exit(main())
