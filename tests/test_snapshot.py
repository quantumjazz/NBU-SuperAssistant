"""The nightly copy (constitution 6.7; the owner, 15 October 2026: "every
day, say 00.00 hours the app outputs a csv with all students entries data",
"Email it to you", "30 days").

Rules over generated input: a cell Excel would change shows in Excel as
typed, or, too long or on several lines for Excel's text value, with an
apostrophe before it, and is never a formula; the file holds every submitted application, those
in the bin marked, and nothing of a draft, a deleted application or a
secret, in any characters, mixed scripts, line breaks, quotes and
semicolons included; copies 30 days old or older go and the others stay.
The command, in every mail mode and when the relay refuses. Everyone is
invented.
"""

import csv
import io
import os
import stat
from datetime import date, timedelta

import pytest
from hypothesis import given, settings as hsettings, strategies as st

from superassistant import (accounts, applications, db, lists, mail,
                            snapshot, texts)
from superassistant import __main__ as cli
from tests.conftest import (OWNER_EMAIL, connect, insert_application,
                            insert_check, insert_request, make_account,
                            make_settings)
from tests.test_documents import ANY_CHARACTER, CYRILLIC, SPECIAL, line
from tests.test_reports import Data, add_account
from tests.test_supervision_rules import FAST

OWNER = "owner"
OWNER_ADDRESS = "owner-account@example.org"


def text_formula(written):
    """The pieces of Excel text values a cell joins, ="a"&"b", as Excel
    reads them, or None when the cell is not one."""
    if not written.startswith('="'):
        return None
    pieces, current, i = [], [], 2
    while i < len(written):
        ch = written[i]
        if ch != '"':
            current.append(ch)
            i += 1
        elif written[i + 1:i + 2] == '"':
            current.append('"')
            i += 2
        elif written[i + 1:i + 3] == '&"':
            pieces.append("".join(current))
            current, i = [], i + 3
        elif i == len(written) - 1:
            pieces.append("".join(current))
            return pieces
        else:
            return None
    return None


def excel_shows(written):
    """What Excel shows for a cell as the file writes it: its text values
    joined; any other cell as it is, an apostrophe before it included (seen
    in Excel on the owner's Mac, 15 October 2026)."""
    pieces = text_formula(written)
    return "".join(pieces) if pieces is not None else written


def any_text(max_size=40):
    return st.text(alphabet=st.one_of(
        st.sampled_from(CYRILLIC + "abcXYZ0123456789" + SPECIAL
                        + "=+-@\t\r\n\"';"), ANY_CHARACTER),
        max_size=max_size)


def excel_units(text):
    return len(text.encode("utf-16-le")) // 2


def check_cell(value):
    written = snapshot.cell(value)
    one_line = "\n" not in value and "\r" not in value
    pieces = text_formula(written)
    if value and one_line and pieces is not None:
        # Excel's text values, shown exactly as typed whatever they hold.
        assert "".join(pieces) == value
        assert all(excel_units(piece) + piece.count('"') <= 255
                   for piece in pieces)
        assert excel_units(written) <= 8192
    elif value and one_line:
        # Too long for one formula: kept as text by a letter, or shown with
        # an apostrophe.
        joined = "=" + "&".join('"' + piece.replace('"', '""') + '"'
                                for piece in snapshot._pieces(value))
        assert excel_units(joined) > 8192
        assert written == ("'" + value if not any(ch.isalpha() for ch in value)
                           or value.startswith(snapshot._FORMULA_START)
                           else value)
    elif value.startswith(snapshot._FORMULA_START):
        assert written == "'" + value         # shown with the apostrophe
    else:
        assert written == value               # Excel keeps lines as text
    # Never a formula Excel would run: only joined text values.
    assert not written.startswith(("+", "-", "@", "\t", "\r"))
    assert not written.startswith("=") or pieces is not None
    return written


@hsettings(max_examples=400, deadline=None)
@given(any_text(300))
def test_a_cell_shows_as_typed_and_is_never_a_formula(value):
    check_cell(value)


@pytest.mark.parametrize("value", [
    "1" * 256, "0" * 256, "0." + "1" * 254, "1" * 309, "1." + "0" * 255,
    '"' * 255, '"' * 300, "1" * 5000, "😀" * 200, "=x" + "y" * 300,
    "x" * 255 + '"', "1" * 9000, "a" * 9000, "0888123456\n0999",
])
def test_long_cells_excel_would_convert_stay_as_typed(value):
    """Codex T15-C3: in Excel, 256 ones became 1,11E+255 and 256 zeros 0.
    Each of these was read back exactly in Excel on 15 October 2026, opened
    and imported, apart from the 9,000 digits, too long for a formula, which
    keep their digits behind an apostrophe."""
    written = check_cell(value)
    if value == "1" * 9000:
        assert written == "'" + value
    elif "\n" not in value and value != "a" * 9000:
        assert excel_shows(written) == value


def read(data):
    """The cells as the file writes them."""
    assert data.startswith(b"\xef\xbb\xbf")
    return list(csv.reader(io.StringIO(data.decode("utf-8-sig")),
                           delimiter=";"))


def shown(data):
    """The cells as Excel shows them."""
    return [[excel_shows(value) for value in row] for row in read(data)]


@st.composite
def entries(draw):
    return {
        "grad_type": draw(st.sampled_from(["thesis", "exam"])),
        "name1": draw(line(max_size=20)), "name2": draw(line(max_size=20)),
        "name3": draw(line(max_size=20)),
        "fn": "F" + draw(st.text("0123456789", min_size=1, max_size=8)),
        "phone": draw(st.one_of(st.text("0123456789 +-()", max_size=16),
                                line(max_size=16))),
        "programme": draw(st.sampled_from(["", "BSNADM01", "MSNADM21"])),
        "topic": draw(line(max_size=60)),
        "average_grade": draw(st.sampled_from(["5,50", "6", "4.75", ""])),
        "professor": draw(st.sampled_from(["", "ivanov", "georgieva"])),
        "rationale": draw(any_text(80)), "plan": draw(any_text(80)),
        "submitted": draw(st.booleans()),
        "answer": draw(st.sampled_from([None, "confirm", "decline"])),
        "check": draw(st.sampled_from([None, "passed", "not_passed"])),
        "note": draw(any_text(30)),
        "bin": draw(st.sampled_from([None, "graduated", "other", "deleted"])),
        "bin_note": draw(any_text(20)).strip(),
    }


@FAST
@given(st.lists(entries(), max_size=6))
def test_the_file_holds_every_submitted_application_as_staff_see_it(made):
    with Data() as d:
        expected = {}
        gone = []
        for index, entry in enumerate(made):
            address = "s{}@example.org".format(index)
            stamp = db.now()
            fields = dict((k, entry[k]) for k in (
                "grad_type", "name1", "name2", "name3", "fn", "phone",
                "programme", "topic", "average_grade", "professor",
                "rationale", "plan"))
            cursor = d.connection.execute(
                "INSERT INTO applications (email, email_key, created_at, "
                "updated_at, submitted_at, " + ", ".join(fields)
                + ") VALUES (?,?,?,?,?," + ",".join("?" * len(fields)) + ")",
                [address, address, stamp, stamp,
                 stamp if entry["submitted"] else None]
                + list(fields.values()))
            number = cursor.lastrowid
            if entry["answer"] or entry["grad_type"] == "thesis":
                d.connection.execute(
                    "INSERT INTO requests (application_id, created_at, "
                    "professor, sup_email, token_hash, sent_at, answer, "
                    "comment, answered_at, last_mailed_at) VALUES "
                    "(?,?,?,?,?,?,?,?,?,?)",
                    (number, stamp, "ivanov", "p.ivanov@example.org",
                     "secret-hash-{}".format(number), stamp, entry["answer"],
                     "коментар" if entry["answer"] else "",
                     stamp if entry["answer"] else None, stamp))
            if entry["check"]:
                d.connection.execute(
                    "INSERT INTO checks (application_id, result, note, "
                    "by_account, at) VALUES (?,?,?,?,?)",
                    (number, entry["check"], entry["note"], d.account, stamp))
            if entry["submitted"] and entry["bin"]:
                reason = "other" if entry["bin"] == "deleted" else entry["bin"]
                applications.remove(d.connection, number, reason,
                                    entry["bin_note"], d.account)
                if entry["bin"] == "deleted":
                    applications.delete(d.connection, number, d.account)
                    gone.append(address)
                    continue
            if entry["submitted"]:
                expected[number] = (entry, address)
        # Secrets the records hold, made recognisable.
        d.connection.execute(
            "UPDATE accounts SET salt = 'secret-salt', hash = 'secret-password', "
            "session_tag = 'secret-tag'")
        d.connection.execute(
            "INSERT INTO signins (email, email_key, code_salt, code_hash, "
            "link_hash, created_at, expires_at) VALUES ('s0@example.org', "
            "'s0@example.org', 'secret-code-salt', 'secret-code', "
            "'secret-link', 't', 't')")
        rows, binned = snapshot.table(d.connection, d.lists)
        assert not d.connection.in_transaction
        data = snapshot.to_bytes(rows)
        back = read(data)
        assert back[0] == [snapshot.cell(c) for c in texts.SNAPSHOT_COLUMNS]
        assert shown(data)[0] == list(texts.SNAPSHOT_COLUMNS)
        body = back[1:]
        assert [int(excel_shows(row[0])) for row in body] == sorted(expected)
        assert binned == sum(1 for e, _ in expected.values()
                             if e["bin"] in ("graduated", "other"))
        column = dict((name, i) for i, name in
                      enumerate(texts.SNAPSHOT_COLUMNS))
        cell = snapshot.cell
        for row in body:
            # Each cell is written as cell() writes the value staff see.
            entry, address = expected[int(excel_shows(row[0]))]
            assert len(row) == len(texts.SNAPSHOT_COLUMNS)
            assert row[column["Електронна поща на студента"]] == cell(address)
            for field, name in (("name1", "Собствено име"),
                                ("name2", "Бащино име"),
                                ("name3", "Фамилия"), ("fn", "F№"),
                                ("phone", "Телефон"),
                                ("topic", "Тема на тезата"),
                                ("average_grade",
                                 "Среден успех от следването"),
                                ("programme", "Код на програмата"),
                                ("rationale", "Обосновка на темата"),
                                ("plan", "Примерен план-съдържание")):
                assert row[column[name]] == cell(entry[field]), field
            assert row[column["Вид"]] == cell(
                texts.STAFF_TYPE[entry["grad_type"]])
            thesis = entry["grad_type"] == "thesis"
            answer = (entry["answer"] or "awaited") if thesis else None
            assert row[column["Отговор на научния ръководител"]] == cell(
                texts.STAFF_ANSWER[answer])
            assert row[column["Коментар на научния ръководител"]] == cell(
                "коментар" if thesis and entry["answer"] else "")
            assert row[column["Последна проверка"]] == cell(
                texts.STAFF_CHECK[entry["check"]])
            assert row[column["Бележка към проверката"]] == cell(
                entry["note"] if entry["check"] else "")
            in_bin = entry["bin"] in ("graduated", "other")
            assert row[column["В кошчето"]] == cell(
                texts.BIN_REASON[entry["bin"]] if in_bin
                else texts.SNAPSHOT_NOT_BINNED)
            assert row[column["Бележка при премахване"]] == cell(
                entry["bin_note"] if in_bin else "")
        text = data.decode("utf-8-sig")
        assert "secret" not in text
        for address in gone:
            assert address not in text


@hsettings(max_examples=60, deadline=None)
@given(st.lists(st.integers(-3, 400), unique=True, max_size=12))
def test_copies_30_days_old_or_older_go_and_the_others_stay(ages):
    with Data() as d:
        today = date(2026, 10, 15)
        folder = d.settings.snapshots_dir
        folder.mkdir()
        for age in ages:
            name = snapshot.NAME.format((today - timedelta(days=age))
                                        .isoformat())
            (folder / name).write_bytes(b"x")
        for other in ("notes.txt", "zaiavlenia-2026-01-01.xlsx",
                      "zaiavlenia-2026-13-40.csv"):
            (folder / other).write_bytes(b"keep")
        (folder / "zaiavlenia-2026-10-15.csv.tmp").write_bytes(b"half")
        removed = snapshot.prune(d.settings, today)
        left = set(p.name for p in folder.iterdir())
        for age in ages:
            name = snapshot.NAME.format((today - timedelta(days=age))
                                        .isoformat())
            assert (name in left) == (age < snapshot.KEEP_DAYS), age
        assert {"notes.txt", "zaiavlenia-2026-01-01.xlsx",
                "zaiavlenia-2026-13-40.csv"} <= left
        assert "zaiavlenia-2026-10-15.csv.tmp" in removed
        assert "zaiavlenia-2026-10-15.csv.tmp" not in left


# --- The command -------------------------------------------------------------

def owner_settings(data_dir, **overrides):
    values = dict(owner_username=OWNER)
    values.update(overrides)
    return make_settings(data_dir, **values)


@pytest.fixture
def records(data_dir, clock):
    """An owner, a staff member, a thesis with an answer and a check, a
    state exam in the bin, and a draft."""
    settings = owner_settings(data_dir)
    owner = make_account(settings, OWNER, OWNER_ADDRESS)
    staff = make_account(settings, "staff1")
    thesis = insert_application(settings, "ivan@example.org",
                                grad_type="thesis", name1="Иван",
                                name2="Петров", name3="Тестов", fn="F12345",
                                phone="0888123456", programme="BSNADM01",
                                topic="=HYPERLINK(\"x\")", professor="ivanov",
                                average_grade="5,50")
    insert_request(settings, thesis, answer="confirm")
    insert_check(settings, thesis, "passed", staff["id"], note="+359 1")
    exam = insert_application(settings, "maria@example.org",
                              grad_type="exam", name1="Мария", fn="F7")
    connection = connect(settings)
    applications.remove(connection, exam, "graduated", "сесия", staff["id"])
    connection.close()
    insert_application(settings, "draft@example.org", submitted=False,
                       name1="Чернова")
    return {"owner": owner, "thesis": thesis, "exam": exam}


def run(settings):
    out, err = io.StringIO(), io.StringIO()
    status = snapshot.run(settings, out, err)
    return status, out.getvalue(), err.getvalue()


def attachment_of(sent):
    (part,) = list(sent.envelope.iter_attachments())
    return part.get_filename(), part.get_content_type(), \
        part.get_payload(decode=True)


def test_mode_send_writes_the_file_and_mails_it_to_the_owners_account(
        data_dir, records, outbox, clock):
    settings = owner_settings(data_dir, mail_mode="send", owner_email="",
                              smtp_host="smtp.example.org",
                              mail_from="nbu@example.org")
    status, out, err = run(settings)
    assert status == 0, err
    path = settings.snapshots_dir / "zaiavlenia-2026-10-12.csv"
    assert path.is_file()
    assert stat.S_IMODE(path.stat().st_mode) == 0o600
    assert stat.S_IMODE(settings.snapshots_dir.stat().st_mode) == 0o700
    (sent,) = outbox.messages
    assert sent.envelope_to == OWNER_ADDRESS
    assert sent.subject == texts.SNAPSHOT_SUBJECT.format(date="12.10.2026")
    name, kind, data = attachment_of(sent)
    assert (name, kind) == (path.name, "text/csv")
    assert data == path.read_bytes()
    for part in (path.name, "общо 2", "в кошчето 1", "30 дни"):
        assert part in sent.text, part
    rows = shown(data)              # as Excel shows the cells
    assert [row[0] for row in rows[1:]] == [str(records["thesis"]),
                                           str(records["exam"])]
    thesis, exam = rows[1:]
    column = dict((n, i) for i, n in enumerate(texts.SNAPSHOT_COLUMNS))
    assert thesis[column["Телефон"]] == "0888123456"
    assert thesis[column["Тема на тезата"]] == "=HYPERLINK(\"x\")"
    assert thesis[column["Бележка към проверката"]] == "+359 1"
    assert thesis[column["Среден успех от следването"]] == "5,50"
    assert thesis[column["Научен ръководител"]] == "доц. д-р Петър Иванов"
    assert exam[column["В кошчето"]] == "дипломиран(а)"
    assert exam[column["Бележка при премахване"]] == "сесия"
    assert "Чернова" not in data.decode("utf-8-sig")
    assert str(path) in out


def test_mode_owner_sends_to_the_owners_development_address(
        data_dir, records, outbox):
    settings = owner_settings(data_dir)            # mode owner, OWNER_EMAIL
    status, out, err = run(settings)
    assert status == 0, err
    (sent,) = outbox.messages
    assert sent.envelope_to == OWNER_EMAIL and sent.intended == OWNER_ADDRESS
    assert attachment_of(sent)[2] == (
        settings.snapshots_dir / "zaiavlenia-2026-10-12.csv").read_bytes()


def test_mode_console_prints_and_sends_nothing(data_dir, records, outbox):
    settings = owner_settings(data_dir, mail_mode="console")
    status, out, err = run(settings)
    assert status == 0, err
    assert outbox.messages == []
    assert texts.MAIL_CONSOLE_ATTACHMENT.format(
        "zaiavlenia-2026-10-12.csv",
        (settings.snapshots_dir / "zaiavlenia-2026-10-12.csv").stat().st_size
    ) in out
    assert texts.CLI_SNAPSHOT_PRINTED in out


def test_a_refused_copy_keeps_the_file_and_fails_the_run(data_dir, records,
                                                         outbox):
    settings = owner_settings(data_dir)
    outbox.refuse = True
    status, out, err = run(settings)
    assert status == 1
    assert texts.CLI_SNAPSHOT_NOT_SENT.split("{")[0] in err
    assert (settings.snapshots_dir / "zaiavlenia-2026-10-12.csv").is_file()


def test_without_the_owners_account_the_copy_is_kept_not_sent(
        data_dir, records, outbox):
    settings = make_settings(data_dir)              # no owner username
    status, out, err = run(settings)
    assert status == 1 and texts.CLI_SNAPSHOT_NO_OWNER in err
    assert outbox.messages == []
    assert (settings.snapshots_dir / "zaiavlenia-2026-10-12.csv").is_file()


def test_each_night_writes_its_own_file_and_the_31st_night_removes_the_first(
        data_dir, records, outbox, clock):
    settings = owner_settings(data_dir)
    for night in range(31):
        assert run(settings)[0] == 0
        clock.advance(days=1)
    names = sorted(p.name for p in settings.snapshots_dir.iterdir()
                   if p.name != snapshot.LOCK)
    assert len(names) == snapshot.KEEP_DAYS
    assert names[0] == "zaiavlenia-2026-10-13.csv"
    assert names[-1] == "zaiavlenia-2026-11-11.csv"
    assert len(outbox.messages) == 31
    # A second run on the same day writes that day's file again and sends
    # it again.
    clock.advance(days=-1)
    assert run(settings)[0] == 0
    assert len(outbox.messages) == 32
    assert len([p for p in settings.snapshots_dir.iterdir()
                if p.name != snapshot.LOCK]) == snapshot.KEEP_DAYS


def test_the_date_is_sofias(data_dir, records, outbox, clock):
    """At 00:00 in Sofia it is still yesterday in UTC: the file is named
    for Sofia's day."""
    from datetime import datetime, timezone
    clock.moment = datetime(2026, 10, 14, 21, 0, 30, tzinfo=timezone.utc)
    settings = owner_settings(data_dir)
    assert run(settings)[0] == 0
    assert (settings.snapshots_dir / "zaiavlenia-2026-10-15.csv").is_file()


def test_the_host_command_runs_it(data_dir, records, outbox, monkeypatch):
    monkeypatch.setenv("SUPERASSISTANT_DATA_DIR", str(data_dir))
    monkeypatch.setenv("SUPERASSISTANT_MAIL_MODE", "console")
    monkeypatch.setenv("SUPERASSISTANT_OWNER_USERNAME", OWNER)
    assert cli.main(["snapshot"]) == 0
    assert (data_dir / "snapshots" / "zaiavlenia-2026-10-12.csv").is_file()
    assert "snapshot" in cli.__doc__


def test_the_command_counts_in_words(data_dir, clock, outbox):
    settings = owner_settings(data_dir)
    make_account(settings, OWNER, OWNER_ADDRESS)
    insert_application(settings, "one@example.org", name1="Една")
    status, out, err = run(settings)
    assert status == 0, err
    size = (settings.snapshots_dir / "zaiavlenia-2026-10-12.csv").stat(
        ).st_size
    assert "(1 заявление, {} байта)".format(size) in out


def test_two_runs_at_once_take_turns(data_dir, records, outbox):
    """While one run holds the folder's lock, another waits for it."""
    import fcntl
    import threading
    settings = owner_settings(data_dir)
    settings.snapshots_dir.mkdir(mode=0o700, exist_ok=True)
    lock = os.open(str(settings.snapshots_dir / snapshot.LOCK),
                   os.O_RDWR | os.O_CREAT, 0o600)
    fcntl.flock(lock, fcntl.LOCK_EX)
    results = []
    other = threading.Thread(target=lambda: results.append(run(settings)))
    other.start()
    other.join(1.0)
    assert other.is_alive()          # waiting for the lock
    assert not (settings.snapshots_dir / "zaiavlenia-2026-10-12.csv"
                ).exists()
    os.close(lock)
    other.join(30)
    assert results and results[0][0] == 0
    assert (settings.snapshots_dir / "zaiavlenia-2026-10-12.csv").is_file()
