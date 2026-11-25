import json

from birding.notes import NOTES
from birding.sightings import clean_sightings, normalize_species, render_log

CHECKLIST = {"Eurasian Jay", "Long-tailed Tit", "Mallard"}


def test_normalize_species():
    assert normalize_species("  eurasian   JAY ") == "Eurasian Jay"
    assert normalize_species("long-tailed tit") == "Long-tailed Tit"


def test_clean_merges_duplicates_and_drops_bad_counts():
    raw = [
        {"species": "mallard", "count": 2, "note": "drake"},
        {"species": "Mallard", "count": 1},
        {"species": "Eurasian Jay", "count": 0},
        {"species": "Eurasian Jay", "count": "two"},
        {"species": "", "count": 3},
    ]
    out = clean_sightings(raw, CHECKLIST)
    assert out == [{"species": "Mallard", "count": 3, "note": "drake", "on_checklist": True}]


def test_clean_flags_off_checklist_species():
    out = clean_sightings([{"species": "White-throated Dipper", "count": 1}], CHECKLIST)
    assert out[0]["on_checklist"] is False


def test_render_log_marks_unknown_and_totals():
    sightings = clean_sightings(
        [{"species": "Mallard", "count": 4}, {"species": "Dipper", "count": 1}], CHECKLIST
    )
    md = render_log("Millrace", "Ibrahim", sightings)
    assert "Dipper (not on checklist)" in md
    assert "2 species, 5 individuals." in md


def test_notes_are_well_formed():
    assert len({n["id"] for n in NOTES}) == len(NOTES)
    assert all(n["text"] and n["voice"] and n["observer"] for n in NOTES)
