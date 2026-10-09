"""Run NBU-SuperAssistant locally: `python app.py` serves http://127.0.0.1:5002.

Settings come from SUPERASSISTANT_* environment variables; with none set, the
data directory is ~/superassistant-data and mail is printed, not sent.
"""

import sys

from superassistant.web import StartupError, create_app


def main():
    try:
        app = create_app()
    except StartupError as exc:
        sys.stderr.write("NBU-SuperAssistant cannot start: " + str(exc) + "\n")
        return 1
    app.run(host="127.0.0.1", port=5002, debug=False)
    return 0


if __name__ == "__main__":
    sys.exit(main())
