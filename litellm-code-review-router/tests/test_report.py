from review_router.report import render_table, summarize


def test_summarize_groups_by_model_and_sorts_by_cost():
    rows = summarize([
        ("big", 2.0, 0.010, 400),
        ("small", 1.0, 0.001, 300),
        ("big", 4.0, 0.020, 500),
    ])
    assert [r.model for r in rows] == ["small", "big"]
    big = rows[1]
    assert (big.calls, big.tokens) == (2, 900)
    assert big.cost_usd == 0.030 and big.mean_latency_s == 3.0


def test_render_table_reports_cost_ratio():
    text = render_table(summarize([("a", 1.0, 0.001, 10), ("b", 1.0, 0.004, 10)]))
    assert "b costs 4.0x a" in text
