from types import SimpleNamespace

from syllabus_qa import corpus, engine, suite


def test_suite_items_are_well_formed():
    codes = {s.code for s in corpus.SYLLABI}
    questions = [i["question"] for i in suite.SUITE_ITEMS]
    assert len(set(questions)) == len(questions)
    for item in suite.SUITE_ITEMS:
        assert item["assertions"], item["question"]
        mentioned = {c for c in codes if c in item["question"] + " ".join(item["assertions"])}
        assert mentioned or "Which course" in item["question"]


def test_courses_in_keeps_retrieval_order_and_drops_repeats():
    sources = [{"file": "his-101-maritime-history.pdf"}, {"file": "bio-214-marine-ecology.pdf"},
               {"file": "his-101-maritime-history.pdf"}]
    assert suite.courses_in(sources) == ["HIS 101", "BIO 214"]


def test_task_returns_answer_and_excerpts_for_the_judge():
    node = SimpleNamespace(metadata={"file_name": "cs-330-applied-cryptography.pdf"}, score=0.9, text="slip days")
    stub = SimpleNamespace(query=lambda q: _Response("4 slip days", [node]))
    out = suite.make_task(stub)({"question": "slip days?"})
    assert out["output"]["retrieved_courses"] == ["CS 330"]
    assert out["output"]["retrieved_excerpts"] == ["slip days"]
    assert out["output"]["answer"] == "4 slip days"


def test_summarize_lists_failed_assertions():
    run = SimpleNamespace(
        test_case=SimpleNamespace(task_output={"input": {"question": "Q1?"}}),
        score_results=[SimpleNamespace(scoring_failed=False, value=0, name="says 20%", reason="said 10%")],
    )
    item = SimpleNamespace(passed=False, runs_passed=1, runs_total=3, test_results=[run])
    result = SimpleNamespace(pass_rate=0.0, items_passed=0, items_total=1, item_results={"a": item})
    lines = suite.summarize(result)
    assert lines[0].startswith("Pass rate: 0%") and "[FAIL] 1/3 runs  Q1?" in lines[1]
    assert "failed: says 20%: said 10%" in lines[2]


class _Response:
    def __init__(self, text, nodes):
        self._text, self.source_nodes = text, nodes

    def __str__(self):
        return self._text


def test_ask_flattens_sources():
    node = SimpleNamespace(metadata={}, score=None, text="x")
    answer = engine.ask(SimpleNamespace(query=lambda q: _Response(" hi ", [node])), "q")
    assert answer.text == "hi" and answer.sources == [{"file": "?", "score": None, "text": "x"}]
