"""Read typed fields off shipping-label images with GPT-4o-mini vision.

Six fictional labels are drawn into labels/ (see labels.py); each goes to the
model as image input and comes back as a LabelFields record: tracking number,
carrier, recipient, postal code, weight in kg, service level, fragile flag.
"""

import base64
import os
from pathlib import Path

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

from labels import LabelFields, generate_labels  # noqa: E402

# track_openai wraps the client: each chat completion becomes an `llm` span
# with token usage and cost (image tokens are what make vision calls pricey).
client = track_openai(OpenAI(), project_name=PROJECT_NAME)

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
    response = client.chat.completions.create(
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
    for path in paths:
        print(f"  {path.name}\n    -> {extract_label(str(path)).model_dump()}\n")

    # Traces are sent from a background thread; flush so the script can exit safely.
    opik.flush_tracker()


if __name__ == "__main__":
    main()
