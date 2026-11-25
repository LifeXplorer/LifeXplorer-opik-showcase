from checks import GLOBAL_ASSERTIONS, assertions_for, field_diff, suite_items
from labels import SPECS


def test_every_label_gets_three_assertions_carrying_its_truth():
    items = suite_items()
    assert len(items) == len(SPECS) == 6
    for spec, item in zip(SPECS, items):
        joined = " ".join(item["assertions"])
        assert spec.expected.tracking_number in joined
        assert spec.expected.postal_code in joined
        assert len(item["assertions"]) == 3


def test_expected_values_never_leak_into_item_data():
    for spec, item in zip(SPECS, suite_items()):
        assert spec.expected.tracking_number not in str(item["data"])
        assert spec.expected.recipient_name not in str(item["data"])


def test_struck_weight_assertion_uses_the_rewritten_value():
    struck = next(s for s in SPECS if s.struck_weight)
    assert struck.struck_weight not in " ".join(assertions_for(struck))
    assert f"weight_kg is {struck.expected.weight_kg:g}" in " ".join(assertions_for(struck))


def test_field_diff_flags_lookalike_swap_and_wrong_weight():
    spec = next(s for s in SPECS if s.file == "label_04_faded.png")
    actual = spec.expected.model_copy(update={"tracking_number": "QP-08B1-I100-S5Z2", "weight_kg": 3.5})
    assert set(field_diff(spec.expected, actual)) == {"tracking_number", "weight_kg"}


def test_field_diff_ignores_carrier_case_only():
    spec = SPECS[0]
    shouted = spec.expected.model_copy(update={"carrier": spec.expected.carrier.upper()})
    assert field_diff(spec.expected, shouted) == {}


def test_global_assertions_are_nonempty_strings():
    assert GLOBAL_ASSERTIONS and all(isinstance(a, str) and a for a in GLOBAL_ASSERTIONS)
