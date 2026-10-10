"""Migrations from several processes at once (milestone 2, contract item 12).

On the host the service and the reminder timer are separate processes, and
either may be the first to open a new or older database. Each must find the
schema at the latest version, and neither may crash because the other was
applying the same step ("table already exists"). The processes here are
real, separate interpreters (multiprocessing's "spawn"), released together
by a barrier at the moment they call db.migrate.
"""

import multiprocessing
import sqlite3
import traceback

import pytest

from superassistant import db

PROCESSES = 4
ROUNDS = 6


def _migrate_when_released(barrier, path, results):
    """One process: wait for the others, then migrate; report what happened."""
    try:
        barrier.wait(timeout=60)
        db.migrate(path)
        results.put("ok")
    except BaseException:
        results.put(traceback.format_exc())


def _migrate_together(path, processes=PROCESSES):
    context = multiprocessing.get_context("spawn")
    barrier = context.Barrier(processes)
    results = context.Queue()
    workers = [context.Process(target=_migrate_when_released,
                               args=(barrier, str(path), results))
               for _ in range(processes)]
    for worker in workers:
        worker.start()
    outcomes = [results.get(timeout=120) for _ in workers]
    for worker in workers:
        worker.join(timeout=60)
    return outcomes, [worker.exitcode for worker in workers]


def _version(path):
    connection = sqlite3.connect(str(path))
    try:
        return connection.execute("PRAGMA user_version").fetchone()[0]
    finally:
        connection.close()


@pytest.mark.parametrize("round_number", range(ROUNDS))
def test_processes_migrating_a_new_database_together_all_succeed(
        tmp_path, round_number):
    path = tmp_path / "superassistant.sqlite3"
    outcomes, exits = _migrate_together(path)
    assert outcomes == ["ok"] * PROCESSES, "\n".join(
        o for o in outcomes if o != "ok")
    assert exits == [0] * PROCESSES
    assert _version(path) == len(db.MIGRATIONS)
    connection = db.connect(path)
    try:
        tables = set(r[0] for r in connection.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table'"))
        # A new database is a first start: nothing is recorded as installed
        # yet, so the starting lists will be written (web.prepare).
        assert connection.execute(
            "SELECT COUNT(*) FROM installation").fetchone()[0] == 0
    finally:
        connection.close()
    assert {"applications", "requests", "installation"} <= tables


@pytest.mark.parametrize("round_number", range(ROUNDS))
def test_processes_upgrading_schema_1_together_record_it_once(
        tmp_path, round_number):
    """An installation from schema 1 is recorded as installed exactly once,
    whichever process applies step 2, and keeps its rows."""
    path = tmp_path / "superassistant.sqlite3"
    connection = sqlite3.connect(str(path))
    connection.executescript(db.MIGRATIONS[0] + ";PRAGMA user_version = 1;")
    connection.execute(
        "INSERT INTO applications (email, email_key, created_at, updated_at,"
        " name1) VALUES ('old@example.org', 'old@example.org', 'x', 'x', "
        "'Старо')")
    connection.commit()
    connection.close()
    outcomes, exits = _migrate_together(path)
    assert outcomes == ["ok"] * PROCESSES, "\n".join(
        o for o in outcomes if o != "ok")
    assert exits == [0] * PROCESSES
    assert _version(path) == len(db.MIGRATIONS)
    connection = db.connect(path)
    try:
        assert [r[0] for r in connection.execute(
            "SELECT key FROM installation")] == ["lists"]
        assert connection.execute(
            "SELECT name1 FROM applications").fetchone()[0] == "Старо"
    finally:
        connection.close()


def test_the_lock_file_lies_beside_the_database(tmp_path):
    path = tmp_path / "superassistant.sqlite3"
    db.migrate(path)
    assert (tmp_path / "superassistant.sqlite3.migrate.lock").exists()
    # Migrating again, with the lock file already there, changes nothing.
    db.migrate(path)
    assert _version(path) == len(db.MIGRATIONS)
