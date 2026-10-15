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


@pytest.mark.parametrize("round_number", range(2))
def test_processes_upgrading_schema_4_together_keep_the_reports(
        tmp_path, round_number):
    """The live pilot's version when the report bin came (the application
    bin of 15 October 2026): a kept report with its student and an earlier
    deletion upgrade once, from several processes, the report still kept."""
    path = tmp_path / "superassistant.sqlite3"
    connection = sqlite3.connect(str(path))
    connection.executescript(";".join(db.MIGRATIONS[:4])
                             + ";PRAGMA user_version = 4;")
    connection.executescript("""
        INSERT INTO accounts (username, username_key, email, email_key,
            algorithm, salt, iterations, dklen, hash, session_tag,
            created_at, approved_at) VALUES ('staff', 'staff',
            's@example.org', 's@example.org', 'none', '00', 1, 1, '00',
            'tag', 't', 't');
        INSERT INTO applications (email, email_key, created_at, updated_at,
            submitted_at, name1) VALUES ('old@example.org',
            'old@example.org', 'x', 'x', 'x', 'Старо');
        INSERT INTO reports (id, programme, faculty, generated_at,
            generated_by, filename) VALUES (2, 'BSNADM01', 'ФДЕНО', 'x', 1,
            'doklad.docx');
        INSERT INTO report_students (report_id, position, application_id,
            fn, name, topic, supervisor) VALUES (2, 1, 1, 'F1', 'Старо',
            'Тема', 'проф. Иванов');
        INSERT INTO report_deletions (report_id, programme, generated_at,
            students, filename, deleted_by, deleted_at) VALUES (1,
            'BSNADM01', 'x', 1, 'old.docx', 1, 'x');
    """)
    connection.commit()
    connection.close()
    outcomes, exits = _migrate_together(path)
    assert outcomes == ["ok"] * PROCESSES, "\n".join(
        o for o in outcomes if o != "ok")
    assert exits == [0] * PROCESSES
    assert _version(path) == len(db.MIGRATIONS)
    connection = db.connect(path)
    try:
        assert [tuple(r) for r in connection.execute(
            "SELECT id, filename, binned_at, binned_by FROM reports")] == [
            (2, "doklad.docx", None, None)]
        assert connection.execute(
            "SELECT COUNT(*) FROM report_students").fetchone()[0] == 1
        assert connection.execute(
            "SELECT COUNT(*) FROM report_deletions").fetchone()[0] == 1
        assert connection.execute(
            "SELECT COUNT(*) FROM report_bin_events").fetchone()[0] == 0
    finally:
        connection.close()


def test_the_lock_file_lies_beside_the_database(tmp_path):
    path = tmp_path / "superassistant.sqlite3"
    db.migrate(path)
    assert (tmp_path / "superassistant.sqlite3.migrate.lock").exists()
    # Migrating again, with the lock file already there, changes nothing.
    db.migrate(path)
    assert _version(path) == len(db.MIGRATIONS)
