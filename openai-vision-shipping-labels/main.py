"""Read typed fields off shipping-label images with GPT-4o-mini vision.

Six fictional labels are drawn into labels/ (see labels.py); each goes to the
model as image input and comes back as a LabelFields record: tracking number,
carrier, recipient, postal code, weight in kg, service level, fragile flag.
Opik traces every extraction with the label image attached, then an Opik test
suite grades each label against assertions that carry the true values.
"""

import base64
import os
from functools import lru_cache
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

HERE = Path(__file__).parent
PROJECT_NAME = "openai-vision-shipping-labels"
MODEL = "gpt-4o-mini"

# Keys live in the repo-root .env (a local .env works too).
load_dotenv(HERE.parent / ".env")
load_dotenv(HERE / ".env")
# Always talk to the public OpenAI API, even if a proxy override is inherited.
os.environ.pop("OPENAI_BASE_URL", None)
# Every trace, span and attachment lands in this Opik project.
os.environ["OPIK_PROJECT_NAME"] = PROJECT_NAME

import opik  # noqa: E402
from openai import OpenAI  # noqa: E402
from opik import Attachment, opik_context  # noqa: E402
from opik.integrations.openai import track_openai  # noqa: E402

from checks import GLOBAL_ASSERTIONS, field_diff, suite_items  # noqa: E402
from labels import SPECS, LabelFields, generate_labels  # noqa: E402


@lru_cache
def get_client() -> OpenAI:
    # track_openai wraps the client: each chat completion becomes an `llm` span
    # with token usage and cost (image tokens are what make vision calls pricey).
    # Built lazily so importing this module (e.g. in tests) needs no API key.
    return track_openai(OpenAI(), project_name=PROJECT_NAME)


SYSTEM_PROMPT = """\
You read photos of parcel shipping labels and return seven fields. Copy only
what is printed or written on the label; never guess.

- tracking_number: exactly as printed under the barcode, including spaces,
  dashes and letter/digit lookalikes (O vs 0, I vs 1, S vs 5).
- carrier: the carrier name in the banner, in normal capitalisation.
- recipient_name: the person under SHIP TO, accents included.
- postal_code: the postal code of the delivery address, as text (keep leading zeros).
- weight_kg: the parcel weight in kilograms. If a weight is crossed out and
  rewritten, the rewritten value is the real one. If both kg and lb are
  printed, use kg.
- service_level: Economy, Standard or Express, from the banner box.
- fragile: true only if a FRAGILE stamp is on the label.
The image may be rotated; read it anyway."""


# @opik.track makes each call one trace (a `general` root span) that holds the
# llm span below; without it the completion would show up as a lone, parentless trace.
@opik.track(project_name=PROJECT_NAME, name="extract_label")
def extract_label(image_path: str) -> LabelFields:
    """One extraction: label image in, validated LabelFields out."""
    # Attach the PNG to the trace: the Attachments tab then shows the exact
    # pixels the model saw, next to the fields it returned.
    opik_context.update_current_trace(
        attachments=[Attachment(data=str(image_path), content_type="image/png")]
    )
    image_b64 = base64.b64encode(Path(image_path).read_bytes()).decode()
    response = get_client().chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "Extract the fields from this shipping label."},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/png;base64,{image_b64}", "detail": "high"},
                    },
                ],
            },
        ],
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "label_fields",
                "strict": True,
                "schema": LabelFields.model_json_schema(),
            },
        },
    )
    return LabelFields.model_validate_json(response.choices[0].message.content)


def main() -> None:
    paths = generate_labels()
    print(f"Reading {len(paths)} generated labels with {MODEL}...\n")
    for spec, path in zip(SPECS, paths):
        fields = extract_label(str(path))
        # A local, exact field diff: a cross-check on what the LLM judge will say below.
        wrong = field_diff(spec.expected, fields)
        print(f"  {path.name}: {'all 7 fields match' if not wrong else 'MISMATCH ' + str(wrong)}")

    # A test suite is a versioned set of items with plain-language assertions;
    # get_or_create + insert is idempotent, so re-runs do not duplicate items.
    # Global assertions are applied to every item on top of its own. Each item
    # runs 3 times and passes with 2: one unlucky read or judge call can't flip a label.
    client = opik.Opik()
    suite = client.get_or_create_test_suite(
        name=PROJECT_NAME,
        project_name=PROJECT_NAME,
        global_assertions=GLOBAL_ASSERTIONS,
        global_execution_policy={"runs_per_item": 3, "pass_threshold": 2},
    )
    suite.insert(suite_items())

    def extraction_task(item: dict[str, Any]) -> dict[str, Any]:
        return {"input": item, "output": extract_label(str(HERE / item["image"])).model_dump()}

    # run_tests runs the task on every item and has an LLM judge grade each
    # assertion; the result is an experiment (a suite run) in the Opik UI.
    result = opik.run_tests(
        test_suite=suite,
        task=extraction_task,
        experiment_name="shipping-labels-gpt-4o-mini",
        worker_threads=3,
        generate_report=False,
    )

    print(f"\nSuite pass rate: {result.pass_rate:.0%} ({result.items_passed}/{result.items_total} labels)")
    for item_result in result.item_results.values():
        image = item_result.test_results[0].test_case.task_output["input"]["image"]
        print(f"  [{'PASS' if item_result.passed else 'FAIL'}] {image}")
    print(f"\nExperiment: {result.experiment_name} ({result.experiment_url})")

    # Traces are sent from a background thread; flush so the script can exit safely.
    opik.flush_tracker()
    client.flush()


if __name__ == "__main__":
    main()
