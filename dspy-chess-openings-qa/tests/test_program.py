import dspy
from dspy.utils import DummyLM

from chess_qa.handbook import HANDBOOK
from chess_qa.program import ask, build_program
from chess_qa.suite import GLOBAL_ASSERTIONS, make_task


def stub_lm(answer="3.Bc4 | card: ITA-1"):
    # DSPy 3.5 names ChainOfThought's thinking field "plan" for a stub model that
    # is not a known reasoning model, and "reasoning" otherwise; fill both.
    return DummyLM([{"plan": "Read the card.", "reasoning": "Read the card.", "answer": answer}] * 4)


def test_every_example_card_exists_in_the_handbook():
    from chess_qa.examples import TEST_ROWS, TRAIN_ROWS
    cards = [row[2] for row in TRAIN_ROWS] + [row[1] for row in TEST_ROWS]
    assert all(f"[{card}]" in HANDBOOK for card in cards)


def test_ask_is_a_tracked_function_that_still_runs_with_tracking_disabled():
    # @opik.track must not get in the way of a plain unit test; the stub LM means no network.
    with dspy.context(lm=stub_lm(), adapter=dspy.ChatAdapter()):
        assert ask(build_program(), HANDBOOK, "Move 3?") == "3.Bc4 | card: ITA-1"


def test_task_returns_run_tests_shape():
    with dspy.context(lm=stub_lm("e6 | card: FRE-1"), adapter=dspy.ChatAdapter()):
        out = make_task(build_program())({"question": "Which pawn?", "card": "FRE-1"})
    assert out == {"input": {"question": "Which pawn?"}, "output": "e6 | card: FRE-1"}


def test_suite_assertions_name_the_house_format():
    assert any("| card:" in a for a in GLOBAL_ASSERTIONS)
