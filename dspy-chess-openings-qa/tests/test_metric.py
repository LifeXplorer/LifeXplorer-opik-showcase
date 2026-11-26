import dspy

from chess_qa.examples import TEST_ROWS, TRAIN_ROWS, testset, trainset
from chess_qa.metric import house_format_metric

EXAMPLE = dspy.Example(card="SIC-2", key_fact="2.Nf3")


def pred(text):
    return dspy.Prediction(answer=text)


def test_house_format_with_right_card_and_fact_passes():
    assert house_format_metric(EXAMPLE, pred("2.Nf3 | card: SIC-2"))


def test_plain_prose_fails():
    assert not house_format_metric(EXAMPLE, pred("White plays 2.Nf3 in the Open Sicilian."))


def test_wrong_card_fails():
    assert not house_format_metric(EXAMPLE, pred("2.Nf3 | card: SIC-1"))


def test_missing_fact_fails():
    assert not house_format_metric(EXAMPLE, pred("2.d4 | card: SIC-2"))


def test_tag_must_be_last():
    assert not house_format_metric(EXAMPLE, pred("2.Nf3 | card: SIC-2 and then more"))


def test_train_answers_pass_their_own_metric():
    for ex in trainset:
        assert house_format_metric(ex, pred(ex.answer)), ex.question


def test_splits_do_not_overlap():
    train_q = {row[0] for row in TRAIN_ROWS}
    assert not train_q & {row[0] for row in TEST_ROWS}
    assert len(testset) == len(TEST_ROWS) == 8
