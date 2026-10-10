"""The host's entry point: gunicorn wsgi:app (listening on 127.0.0.1:8791).

The settings file .env.production in the clone is read first, never
overriding a variable already set (systemd's EnvironmentFile has usually set
them all). A start the settings or the records refuse prints one line,
"NBU-SuperAssistant cannot start: <reason>", and exits with status 3, which
gunicorn reads as a worker that cannot boot, so it stops instead of starting
the worker again and again.
"""

import sys

from superassistant.settings import SettingsFileError, load_settings_file
from superassistant.web import StartupError, create_app

try:
    load_settings_file()
    app = create_app()
except (SettingsFileError, StartupError) as exc:
    sys.stderr.write("NBU-SuperAssistant cannot start: " + str(exc) + "\n")
    sys.stderr.flush()
    sys.exit(3)
