import pytest

from analysis import (
    check_answer,
    expected_answers,
    format_time,
    highest_dnf_rate,
    load_rows,
    negative_split_share,
    parse_time,
    women_40_44_winner,
)


@pytest.fixture(scope="module")
def rows():
    return load_rows()


def test_time_round_trip():
    assert parse_time("3:04:18") == 11058
    assert format_time(11058) == "3:04:18"


def test_planted_findings_in_the_fixture(rows):
    assert women_40_44_winner(rows) == ("Odile Fenwick", "3:04:18")
    assert negative_split_share(rows)[0] == "Dune Pacers"
    assert highest_dnf_rate(rows)[0] == "60+"


def test_negative_split_ignores_dnf_and_small_clubs():
    rows = [
        {"status": "FIN", "club": "A", "half_split": "2:00:00", "chip_time": "3:50:00"},
        {"status": "DNF", "club": "A", "half_split": "1:00:00", "chip_time": ""},
        {"status": "FIN", "club": "Tiny", "half_split": "2:00:00", "chip_time": "3:50:00"},
    ]
    assert negative_split_share(rows, min_finishers=1)[1] == 100.0
    with pytest.raises(ValueError):  # nothing reaches 5 finishers
        negative_split_share(rows, min_finishers=5)


def test_check_answer_accepts_correct_and_flags_wrong(rows):
    q1, q2, _ = expected_answers(rows)
    assert check_answer("Odile Fenwick won in 3:04:18.", q1) == []
    assert check_answer("Dune Pacers, 66.7% of finishers", q2) == []
    wrong = check_answer("Harbour Striders at 92.3%", q2)
    assert "missing 'Dune Pacers'" in wrong and len(wrong) == 2
