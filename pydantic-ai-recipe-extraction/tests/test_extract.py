"""Run the real traced function against a stub model: no keys, no network."""

import os

os.environ["OPIK_TRACK_DISABLE"] = "true"  # @opik.track becomes a pass-through
os.environ["OTEL_SDK_DISABLED"] = "true"  # and the OTel exporter sends nothing to Opik

import recipes  # noqa: E402
from pydantic_ai.models.test import TestModel  # noqa: E402


def stub_card(**extra):
    return {"title": "Dal", "ingredients": [{"name": "red lentils", "quantity": "1 cup"}], "steps": ["boil"], **extra}


def run_with(output: dict, text: str):
    with recipes.agent.override(model=TestModel(custom_output_args=output)):
        return recipes.extract_recipe(text)


def test_traced_function_runs_with_tracking_disabled():
    card = run_with(stub_card(servings=4), "quick dal for 4: red lentils 1 cup")
    assert card["servings"] == 4
    assert card["ingredients"][0]["name"] == "red lentils"


def test_card_schema_defaults_optional_fields_to_null():
    card = run_with(stub_card(), "red lentils 1 cup")
    assert card["oven_temp_c"] is None and card["cook_minutes"] is None
