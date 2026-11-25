from review_router.diffs import load_diffs
from review_router.prompts import build_messages


def test_sample_diffs_load_and_filter():
    all_diffs = load_diffs()
    assert len(all_diffs) == 5
    assert [d.name for d in load_diffs(only=["sql"])] == ["03-sql-search"]


def test_messages_carry_the_diff_for_every_model():
    messages = build_messages("+print('hi')")
    assert messages[0]["role"] == "system"
    assert "+print('hi')" in messages[1]["content"]
