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
MODEL = "gpt-4o-mini"

# Keys live in the repo-root .env (a local .env works too).
load_dotenv(HERE.parent / ".env")
load_dotenv(HERE / ".env")
# Always talk to the public OpenAI API, even if a proxy override is inherited.
os.environ.pop("OPENAI_BASE_URL", None)

from openai import OpenAI  # noqa: E402

from labels import LabelFields, generate_labels  # noqa: E402

client = OpenAI()

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


def extract_label(image_path: str) -> LabelFields:
    """One extraction: label image in, validated LabelFields out."""
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


if __name__ == "__main__":
    main()
