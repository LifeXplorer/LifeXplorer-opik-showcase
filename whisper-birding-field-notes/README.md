# whisper-birding-field-notes

![Python](https://img.shields.io/badge/python-3.12%2B-3776AB?style=flat&logo=python&logoColor=white)
![OpenAI](https://img.shields.io/badge/OpenAI-TTS%20%2B%20Whisper-412991?style=flat&logo=openai&logoColor=white)
![Opik](https://img.shields.io/badge/Opik-2.3%2B-2f54eb?style=flat)

*Press play on the exact recording that produced a bird count.*

A birder talks into a phone at the edge of a wood, and an hour later a spreadsheet row says "Gray Heron, 2". Was it two herons? Did Whisper mishear the name? Did the extractor invent the number? The audio is long gone by the time anyone asks, and the log looks equally tidy whether it is right or wrong. This example keeps the recording attached to the pipeline run, so the question can be settled by listening.

## What you'll build

A small modular pipeline, one traced function per stage, run over three fictional voice notes (observers Mara, Ibrahim and Tove, at three made-up sites):

1. **synthesize-audio**: OpenAI TTS (`gpt-4o-mini-tts`) speaks each script with its own voice into `audio/<id>.mp3`. This stands in for a real recording and runs only when the MP3 is missing.
2. **transcribe**: Whisper (`whisper-1`) turns the MP3 back into text.
3. **extract-sightings**: `gpt-4o-mini` pulls `{species, count, note}` records out of the transcript.
4. **build-log**: plain Python merges duplicates, rejects bad counts, flags species missing from `data/checklist.json`, and renders a markdown log.

A second script, `evaluate.py`, replays the saved transcripts through the extractor as an Opik test suite with two LLM-judged assertions. Every run is a trace in the `whisper-birding-field-notes` project.

## See it in Opik

Open the **whisper-birding-field-notes** project and the **Traces** tab. After `main.py` there are three `field-note-to-log` traces (metadata holds `observer` and `note_id`). Open one and look at the **Attachments** tab: a playable MP3 (`alder-carr-dawn.mp3`, about 350 KB), the very audio Whisper heard. Beside it, the span tree: `synthesize-audio` containing an `audio.speech.create` llm span (`gpt-4o-mini-tts`, roughly $0.0002), `transcribe`, `extract-sightings` containing a `chat_completion_create` llm span (`gpt-4o-mini`, about $0.0001 with token counts), and `build-log`.

Read the `transcribe` output against the audio. In the Millrace note the script says "Grey Heron" and the transcript comes back "Gray herons", so `build-log` prints `Gray Heron (not on checklist)` and the extractor logged a count of 2 for a bird the observer never numbered. In the Alder Carr note "Alder Carr" became "Alder car". Whisper's mistakes are visible in the span and audible in the attachment.

Then `uv run evaluate.py`. Under **Test suites**, `birding-sighting-log-suite` holds three items (one per transcript) and two assertions. The run is 3 items x 3 runs. In the verified run the suite passed 3/3 items; the species assertion passed 9/9 runs and the count assertion 8/9. One judge or extractor verdict flipped on a single run and the item still passed, because the suite's `execution_policy` is `runs_per_item=3, pass_threshold=2`. Without it, that single flip would have failed an item that is fine. Each of the nine runs shows up as an `evaluation_task` trace in the project, containing the extractor spans and the judge's own spans.

## Run it yourself

1. `cp .env.example .env` and set `OPENAI_API_KEY` (a `.env` in a parent folder also works).
2. `uv sync`
3. `uv run main.py` generates three MP3s on first run, then transcribes and logs all three notes (about $0.01 and 35 s).
4. `uv run evaluate.py` runs the suite (about 10 s).
5. Open the project in Opik, open a `field-note-to-log` trace, and play the attachment.

Local self-hosted Opik needs no key; for Opik Cloud, set `OPIK_API_KEY` and `OPIK_WORKSPACE`. The audio is synthetic and every bird sighting is invented.

## Poke around

- Delete `audio/` and re-run: the `synthesize-audio` span reappears; with cached audio it is absent. Compare the two trace shapes.
- Add "Eurasian Dipper" to a script in `birding/notes.py` and remove it from `data/checklist.json`; watch the `(not on checklist)` marker appear in the log.
- Delete the retraction rule from `EXTRACT_PROMPT` and re-run `evaluate.py`: the first assertion may start failing on the Millrace "scratch that" note (it did not in our run, so try it).
- Set `runs_per_item` to 1 in `evaluate.py` and re-run a few times. Single-run verdicts can flip; three runs with a threshold of two absorb that.

## Gotchas we hit

**The `transcribe` span has no cost or usage and no llm child.**
`track_openai` records chat completions and TTS calls as llm spans, but `audio.transcriptions.create` is not wrapped, so Whisper shows only as the plain span from `@opik.track`. Keep that decorator on the function; it is the only thing that puts the transcript into the trace. Whisper cost does not appear on the trace.

**`openai.OpenAIError: Missing credentials` when importing the pipeline in tests.**
Building the client at import time needs a key. Create it lazily instead (`get_client()` with `functools.cache` in `birding/pipeline.py`) so offline tests can import the module and stub the client.

**A species is flagged "not on checklist" for a correct bird.**
Whisper writes "Gray Heron", the checklist says "Grey Heron". That is the flag doing its job, but decide whether to add an alias table before trusting counts per species.

**`PydanticSerializationUnexpectedValue` warnings during `evaluate.py`.**
They come from the judge's response handling inside the SDK and are harmless; the run and its scores are unaffected.

## How it's put together

- `main.py`: pins the Opik project, runs the three notes, saves each result to `out/`, flushes.
- `birding/notes.py`: three fictional voice-note scripts, each with a TTS voice.
- `birding/pipeline.py`: the traced stages and the `field-note-to-log` parent that attaches the MP3.
- `birding/sightings.py`: pure functions for name normalization, merging, checklist flags and markdown rendering.
- `data/checklist.json`: the site species checklist.
- `evaluate.py`: the Opik test suite with the `execution_policy`.
- `tests/`: offline tests for the pure logic and, with a stubbed client, the traced pipeline.
- `.env.example`: the settings the example reads.

Run the tests with no keys and tracking off: `env -u OPENAI_API_KEY OPIK_TRACK_DISABLE=true uv run pytest`.

---

*built with Opik · inspired by Opik's examples and documentation*
