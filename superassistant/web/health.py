"""GET /healthz: is the service up, and can it still write its records?

For the host's checks (a monitor, or curl after a deploy); no sign-in. The
approach is CourseBench's (coursebench/web/app.py, healthz and
_can_write_records): a check that only proves Python is running is theatre,
because the failure that happens on a host is a data directory gone missing,
read-only or full. So the check writes a small file in the data directory and
removes it again. It answers ok or not ok and never names a path.
"""

import os
import tempfile

from flask import Blueprint, jsonify

from superassistant import web

blueprint = Blueprint("health", __name__)


@blueprint.route("/healthz")
def healthz():
    if can_write_records(web.settings().data_dir):
        return jsonify(status="ok")
    return jsonify(status="data directory is not writable"), 503


def can_write_records(data_dir):
    """Write a file in the data directory, flush it to disk, remove it.

    Copied from CourseBench (coursebench/web/app.py, _can_write_records):
    not os.access, which reads permission bits and passes a full disk. One
    change: a file that cannot be removed again is a failure too.
    """
    if not os.path.isdir(str(data_dir)):
        return False
    handle = path = None
    try:
        handle, path = tempfile.mkstemp(dir=str(data_dir), prefix=".health-")
        with os.fdopen(handle, "w") as probe:
            handle = None
            probe.write("ok")
            probe.flush()
            os.fsync(probe.fileno())
        os.remove(path)
        path = None
        return True
    except OSError:
        return False
    finally:
        if handle is not None:
            os.close(handle)
        if path is not None:
            try:
                os.remove(path)
            except OSError:
                pass
