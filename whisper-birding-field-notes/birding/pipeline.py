"""Voice note -> transcript -> sighting log, one traced function per stage.

One trace per note in the "whisper-birding-field-notes" project:

    field-note-to-log                 <- whole pipeline, MP3 attached to the trace
    |- synthesize-audio               <- only when audio/<id>.mp3 is missing (TTS)
    |  '- audio.speech.create         <- track_openai llm span (gpt-4o-mini-tts, cost)
    |- transcribe                     <- whisper-1; a plain span, no child (see README)
    |- extract-sightings              <- gpt-4o-mini -> raw JSON sightings
    |  '- chat_completion_create      <- track_openai llm span (tokens, cost)
    '- build-log                      <- pure code: merge, checklist check, markdown
"""

import functools
import json
from pathlib import Path

import opik
from openai import OpenAI
from opik import Attachment, opik_context
from opik.integrations.openai import track_openai

from birding.sightings import clean_sightings, load_checklist, render_log

TTS_MODEL = "gpt-4o-mini-tts"
TRANSCRIBE_MODEL = "whisper-1"
EXTRACT_MODEL = "gpt-4o-mini"

AUDIO_DIR = Path(__file__).resolve().parent.parent / "audio"

EXTRACT_PROMPT = """\
You turn a birdwatcher's transcribed voice note into sighting records.
Reply with JSON only, in exactly this shape:

{"sightings": [{"species": "<common name>", "count": <integer>, "note": "<short behaviour note or empty string>"}]}

Rules:
- One record per species; use the full common name (e.g. "Eurasian Jay").
- Count only birds the observer actually saw or heard in this note.
- If the observer retracts an identification ("scratch that", "it was actually
  X"), do not log the retracted species; log the corrected one.
- If the count is approximate, use the number given. If a species is mentioned
  without a number, count it as 1.
"""


@functools.cache
def get_client() -> OpenAI:
    # track_openai wraps the client: every TTS, Whisper and chat call becomes an
    # llm span nested under whichever @opik.track function is running.
    # Built lazily so importing this module (and the tests) needs no API key.
    return track_openai(OpenAI())


# @opik.track opens a span for this function inside the current trace (or a
# new trace if called at top level), logging its arguments and return value.
@opik.track(name="synthesize-audio")
def synthesize_audio(note: dict, audio_path: Path) -> dict:
    audio_path.parent.mkdir(exist_ok=True)
    response = get_client().audio.speech.create(
        model=TTS_MODEL, voice=note["voice"], input=note["text"], response_format="mp3"
    )
    audio_path.write_bytes(response.content)
    return {"audio_path": audio_path.name, "voice": note["voice"], "size_bytes": audio_path.stat().st_size}


@opik.track(name="transcribe")
def transcribe(audio_path: Path) -> str:
    with audio_path.open("rb") as f:
        return get_client().audio.transcriptions.create(
            model=TRANSCRIBE_MODEL, file=f, response_format="text"
        )


@opik.track(name="extract-sightings")
def extract_sightings(transcript: str) -> list[dict]:
    response = get_client().chat.completions.create(
        model=EXTRACT_MODEL,
        messages=[
            {"role": "system", "content": EXTRACT_PROMPT},
            {"role": "user", "content": transcript},
        ],
        response_format={"type": "json_object"},
    )
    return json.loads(response.choices[0].message.content).get("sightings", [])


@opik.track(name="build-log")
def build_log(note: dict, raw_sightings: list[dict]) -> dict:
    sightings = clean_sightings(raw_sightings, load_checklist())
    return {"sightings": sightings, "markdown": render_log(note["title"], note["observer"], sightings)}


@opik.track(name="field-note-to-log")
def field_note_to_log(note: dict) -> dict:
    audio_path = AUDIO_DIR / f"{note['id']}.mp3"
    if not audio_path.exists():
        synthesize_audio(note, audio_path)

    transcript = transcribe(audio_path)
    raw = extract_sightings(transcript)
    log = build_log(note, raw)

    # Attachment uploads the MP3 to the trace: it shows up in the trace's
    # Attachments tab as a player, so you can listen to what Whisper heard.
    opik_context.update_current_trace(
        attachments=[Attachment(data=str(audio_path), content_type="audio/mpeg")],
        metadata={"observer": note["observer"], "note_id": note["id"]},
    )
    return {"note": note["title"], "transcript": transcript, **log}
