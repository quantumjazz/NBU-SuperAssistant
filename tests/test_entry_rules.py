"""The entry rules, tested as rules over generated text (NOW.md requirement 2,
proof 1: "what requirement 2 stores and refuses")."""

import re
import unicodedata

from hypothesis import given, settings as hsettings, strategies as st

from superassistant import applications

LATIN = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
CYRILLIC = ("абвгдежзийклмнопрстуфхцчшщъьюяѝАБВГДЕЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЬЮЯ")
SEPARATORS = [" ", "-", " – ", ", ", ". ", "1", "2026", "/", "(", ")", "„", "“"]

any_text = st.text(max_size=300)


def _holdable(ch, multi):
    if ch == "\n" and multi:
        return True
    return (unicodedata.category(ch) not in ("Cc", "Cs")
            and ch not in ("￾", "￿"))


@given(field=st.sampled_from(applications.ONE_LINE_FIELDS
                             + applications.MULTI_LINE_FIELDS),
       value=any_text)
def test_stored_as_typed_trimmed_fn_in_capitals_or_refused(field, value):
    stored = applications.normalise(field, value)
    multi = field in applications.MULTI_LINE_FIELDS
    typed = value.replace("\r\n", "\n").replace("\r", "\n") if multi \
        else value
    expected = typed.strip()
    if field == "fn":
        expected = expected.upper()
    assert stored == expected
    # Refused characters are looked for in what was typed, ends included.
    refusal = applications.check_entry(field, value)
    bad = [ch for ch in typed if not _holdable(ch, multi)]
    if bad:
        assert refusal is not None and refusal.reason == "control"
        assert set(refusal.characters) == set(bad)
    elif refusal is not None:
        assert refusal.reason == "mixed"
        assert field in applications.SCRIPT_CHECKED_FIELDS


controls = st.characters(whitelist_categories=("Cc",)).filter(
    lambda ch: ch != "\n")


@given(field=st.sampled_from(applications.ONE_LINE_FIELDS
                             + applications.MULTI_LINE_FIELDS),
       before=st.lists(controls, max_size=2), after=st.lists(controls,
                                                             max_size=2),
       middle=st.text(alphabet="Иван Петров", min_size=1, max_size=10))
def test_a_control_at_either_end_is_refused_not_trimmed(field, before, after,
                                                        middle):
    if not before and not after:
        return
    value = "".join(before) + middle + "".join(after)
    expected = set(before + after)
    if field in applications.MULTI_LINE_FIELDS:
        expected.discard("\r")         # a line break there, kept as \n
    values, refusals = applications.clean({field: value}, [field])
    if not expected:
        assert refusals == []
        return
    assert values == {}
    (refusal,) = refusals
    assert refusal.reason == "control"
    assert set(refusal.characters) == expected


def test_the_refused_controls_are_shown_by_their_codes(client):
    from tests.test_application_flow import as_student, save
    as_student(client, "codes@example.org")
    response = save(client, 1, {"name1": "\x0bИван\x0c", "name2": "Иванов",
                                "name3": "Петров", "fn": "F1",
                                "grad_type": "exam"}, "submit")
    page = response.get_data(as_text=True)
    assert response.status_code == 400
    assert "U+000B" in page and "U+000C" in page


word = st.text(alphabet=LATIN + CYRILLIC, min_size=1, max_size=12)
phrase = st.lists(st.tuples(word, st.sampled_from(SEPARATORS)), min_size=1,
                  max_size=8).map(lambda pairs: "".join(w + s for w, s in pairs))


def _oracle_mixed_words(text):
    runs = re.findall("[" + LATIN + CYRILLIC + "]+", text)
    return [r for r in runs
            if any(c in LATIN for c in r) and any(c in CYRILLIC for c in r)]


@given(field=st.sampled_from(applications.SCRIPT_CHECKED_FIELDS),
       text=phrase)
def test_a_word_mixing_latin_and_cyrillic_is_refused_with_its_letters(
        field, text):
    value = applications.normalise(field, text)
    refusal = applications.check_entry(field, value)
    mixed = _oracle_mixed_words(value)
    if mixed:
        assert refusal is not None and refusal.reason == "mixed"
        shown = set(refusal.characters)
        letters_in_mixed = set("".join(mixed))
        assert shown and shown <= letters_in_mixed
    else:
        assert refusal is None


@given(text=phrase)
def test_fields_outside_the_rule_keep_mixed_words(text):
    for field in ("phone", "average_grade") + applications.MULTI_LINE_FIELDS:
        refusal = applications.check_entry(field,
                                           applications.normalise(field, text))
        assert refusal is None


def test_the_examples_named_in_the_plan():
    assert applications.check_entry("topic", "Внедряване на CRM-система") \
        is None
    assert applications.check_entry("topic", "SWOT-анализ на е-управлението") \
        is None
    refusal = applications.check_entry("name3", "Иванов".replace("а", "a"))
    assert refusal.reason == "mixed" and refusal.characters == "a"
    refusal = applications.check_entry("name1", "Иvan")
    assert refusal.characters == "И"


@hsettings(max_examples=50)
@given(text=st.text(max_size=80))
def test_a_line_break_is_refused_in_a_one_line_field_and_kept_in_the_proposal(
        text):
    one_line = applications.check_entry("topic",
                                        applications.normalise("topic",
                                                               "a\nb" + text))
    assert one_line is not None and one_line.reason == "control"
    kept = applications.normalise("plan", "Глава 1\r\nГлава 2")
    assert kept == "Глава 1\nГлава 2"
    assert applications.check_entry("plan", kept) is None


def test_choices_must_name_an_entry_of_the_lists(tmp_path):
    from superassistant import lists
    lists.write_starter(tmp_path)
    loaded = lists.load(tmp_path)
    values, refusals = applications.clean(
        {"programme": "НЕМА", "sup_title": "акад."}, ["programme", "sup_title"],
        loaded)
    assert sorted(r.field for r in refusals) == ["programme", "sup_title"]
    values, refusals = applications.clean(
        {"programme": "АУ-РО", "sup_title": "доц. д-р"},
        ["programme", "sup_title"], loaded)
    assert refusals == [] and values["programme"] == "АУ-РО"


def test_dates_people_read_are_sofia_time():
    from superassistant import db
    # 21:30 UTC on 9 October is 00:30 on 10 October in Sofia (UTC+3).
    assert db.local_date("2026-10-09T21:30:00+00:00") == "10.10.2026"
    assert db.local_datetime("2026-10-09T21:30:00+00:00") == "10.10.2026 00:30"
    # And in winter, UTC+2.
    assert db.local_date("2026-12-31T22:30:00+00:00") == "01.01.2027"
