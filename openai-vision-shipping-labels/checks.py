"""Pure logic around the ground truth: judge assertions and a field-by-field diff.

Nothing here touches the model or Opik, so it is all unit-tested offline.
"""

from labels import SPECS, LabelFields, LabelSpec

# Format rules every extraction must satisfy; the judge reads the output alone.
GLOBAL_ASSERTIONS = [
    "The output has all seven fields (tracking_number, carrier, recipient_name, "
    "postal_code, weight_kg, service_level, fragile) and none is null or empty",
    "postal_code is a string, not a number, and weight_kg is a number in kilograms",
    "Values are read from the label, never invented: the recipient is a real "
    "person's name, not a placeholder such as 'unknown', 'N/A' or 'customer'",
]


def assertions_for(spec: LabelSpec) -> list[str]:
    """Plain-language assertions that carry this label's expected values.

    The expected values live only here, never in the item's input data, so the
    judge checks the output against them instead of reading answers off the input.
    """
    e = spec.expected
    return [
        f"The tracking_number is exactly '{e.tracking_number}': same spaces, dashes, "
        "and every letter-versus-digit lookalike (O/0, I/1, S/5, B/8) as written. "
        f"The carrier is {e.carrier} (any capitalisation).",
        f"The recipient_name is '{e.recipient_name}' with accents intact, and the "
        f"postal_code is '{e.postal_code}' (text, leading zeros kept).",
        f"weight_kg is {e.weight_kg:g}, the service_level is {e.service_level}, "
        f"and fragile is {str(e.fragile).lower()}.",
    ]


def suite_items() -> list[dict]:
    """One suite item per label: `data` names the image, assertions hold the truth."""
    return [
        {
            "data": {"image": f"labels/{s.file}", "kind": s.kind},
            "assertions": assertions_for(s),
        }
        for s in SPECS
    ]


def field_diff(expected: LabelFields, actual: LabelFields) -> dict[str, tuple]:
    """Fields whose value differs, as {field: (expected, actual)}.

    Strings compare case-insensitively on the carrier only; every other field
    must match exactly, so an O-for-0 swap in a tracking number is a miss.
    """
    diff = {}
    for name in LabelFields.model_fields:
        want, got = getattr(expected, name), getattr(actual, name)
        if name == "carrier":
            want, got = want.casefold(), got.casefold()
        if name == "weight_kg":
            same = abs(want - got) < 0.005
        else:
            same = want == got
        if not same:
            diff[name] = (getattr(expected, name), getattr(actual, name))
    return diff
