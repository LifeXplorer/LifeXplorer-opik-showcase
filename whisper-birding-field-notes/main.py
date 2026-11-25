"""Run the pipeline over the three fictional voice notes."""

import json
import os
from pathlib import Path

from dotenv import find_dotenv, load_dotenv

# Walk up to the nearest .env for provider keys; pin the Opik project before
# opik is imported so every trace lands in the same project.
load_dotenv(find_dotenv(usecwd=True))
os.environ["OPIK_PROJECT_NAME"] = "whisper-birding-field-notes"
os.environ.pop("OPENAI_BASE_URL", None)

import opik

from birding.notes import NOTES
from birding.pipeline import field_note_to_log

OUT_DIR = Path(__file__).resolve().parent / "out"

if __name__ == "__main__":
    OUT_DIR.mkdir(exist_ok=True)
    for note in NOTES:
        result = field_note_to_log(note)
        # evaluate.py replays these transcripts through the extractor.
        (OUT_DIR / f"{note['id']}.json").write_text(json.dumps(result, indent=2))
        print(f"\nTranscript: {result['transcript'].strip()}\n")
        print(result["markdown"])
    # Traces are sent from a background thread; flush so nothing is lost on exit.
    opik.flush_tracker()
    print("\nDone. Open the whisper-birding-field-notes project in Opik.")
