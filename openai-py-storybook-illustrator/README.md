# openai-py-storybook-illustrator

*Paint a picture book with `images.generate`, and keep every page's brief and its picture together on one trace.*

![Python](https://img.shields.io/badge/python-3.12%2B-3776AB?style=flat&logo=python&logoColor=white)
![OpenAI SDK](https://img.shields.io/badge/openai-python%20SDK-412991?style=flat&logo=openai&logoColor=white)
![Opik](https://img.shields.io/badge/opik-2.3.4-2f54eb?style=flat)

You can't `grep` a watercolor. When an illustrator's brief changes between page 3 and page 12 and the heroine's coat quietly turns from raincoat to dress, nothing in a folder of PNGs tells you which wording did it. This example is a tiny illustrator for a made-up picture book, *Wren and the Lantern Moths*. Each page goes through a cheap scene-writing step and then an image model, and Opik keeps the evidence: the brief version, the scene sentence, and the finished PNG, all on the same trace.

## What you'll build

- A brief template, `storybook-illustration-brief`, stored in the Opik prompt library in two versions. v1 names the character, scene and mood. v2 adds the editor's rules: watercolor palette, a consistent character, no lettering, space for page text.
- `illustrate-page`, a traced function that runs per page: `gpt-4o-mini` turns the page prose into one paintable sentence (through `track_openai`), the library brief is rendered with it, and `gpt-image-1-mini` paints the picture.
- A run that illustrates two pages with each version, so you end with four traces, four PNGs in `output/`, and a printed diff of v1 against v2.

## See it in Opik

Open the project `openai-py-storybook-illustrator` (local Opik: `http://localhost:5173`, workspace `default`).

- **Traces tab:** four `illustrate-page` traces, tagged `v1` or `v2` plus `page-1` or `page-2`. Open one: the Attachments area holds the generated PNG (for example `v2-page-2.png`) and the image renders inline. Metadata shows `prompt_name`, `prompt_version` and `page`.
- **Spans inside a trace:** `chat_completion_create` (llm, `gpt-4o-mini`, about 70 prompt tokens in and 40-60 out) and `images.generate` (llm, `gpt-image-1-mini`, provider `openai`, a few hundred tokens with an estimated cost). The picture is attached to the `images.generate` span as well, right next to the exact prompt text.
- **Prompt library:** `storybook-illustration-brief` has two versions, `v1` and `v2`. Compare them: the diff is the six lines of "Style rules" v2 added. The traces also carry the version they used, so a trace points back to its brief.
- **What you will see in the pictures:** in our run v2 pages look like paper-grain watercolor with indigo, amber and moss, and moths on page 2, while v1 pages are glossier and warmer. Neither version drew lettering. The "wide landscape" rule did not take: images come back square because we request `1024x1024`. Image models treat briefs as suggestions, so your pictures will differ.

## Run it yourself

1. Install [uv](https://docs.astral.sh/uv/) and have a local Opik running (or point `OPIK_URL_OVERRIDE` / `OPIK_API_KEY` at Opik Cloud).
2. `cp .env.example .env` and set `OPENAI_API_KEY` (a parent-folder `.env` is found too).
3. `uv run --python 3.12 main.py`
4. Open the project in Opik as described above. The PNGs are also in `output/`. A run takes under two minutes and costs a few cents.
5. Offline tests, no keys needed: `env -u OPENAI_API_KEY OPIK_TRACK_DISABLE=true uv run --python 3.12 pytest`

## Poke around

- Add a v3 that fixes the heroine's outfit ("always a mustard raincoat, never a dress"). The scene writer sometimes says "patchwork dress"; look at which versions' pictures follow it.
- Set `IMAGE_MODEL=gpt-image-1` or another image model and compare the `images.generate` span usage.
- Request `size="1536x1024"` in `illustrator.py` so the "landscape" rule can hold (check your model supports it).
- Delete `output/`, re-run, and compare two pictures from the same brief: the traces are how you tell runs apart.

## Gotchas we hit

- **`BadRequestError: The model 'gpt-image-1' does not exist.`** Not every API key can use `gpt-image-1`. Fix: pick a model your key can list. The code reads `IMAGE_MODEL` and defaults to `gpt-image-1-mini` (`IMAGE_MODEL=gpt-image-1 uv run main.py` if yours works).
- **No `images.generate` span after `track_openai`.** In opik 2.3.4 the OpenAI integration traces chat, responses and a few other endpoints, but not image generation. Fix: wrap the call in `@opik.track(type="llm")` and set `model`, `provider` and `usage` with `opik_context.update_current_span(...)`, as `generate_image` does. Without `provider` and `model`, cost stays empty.
- **The picture isn't on the trace.** Passing base64 only works when it is a data URI in the span input or output. Fix: save the PNG and pass `attachments=[Attachment(data=path, file_name=..., content_type="image/png")]` to `update_current_span` / `update_current_trace`.
- **Rendered brief wrapped in stray braces: `{Wren, a seven-year-old...}`.** `{{{var}}}` is not "unescaped" in the Python SDK's template engine; it keeps literal braces. Fix: use `{{var}}` (it does not HTML-escape either).
- **Re-running adds a bogus v3 to the prompt.** `create_prompt` compares against the latest version, so registering v1 after v2 creates a new one. Fix: register only when `get_prompt` returns `None`, as `register_briefs` does.

## How it's put together

- `main.py` registers the brief versions, prints the diff, illustrates every page with each version, flushes.
- `illustrator.py` the traced pipeline: scene writer, brief renderer, `images.generate` span with attachment.
- `storybook.py` the fictional book, the character, and the two brief templates.
- `tests/test_storybook.py` offline tests with a stubbed client, including a call to traced functions with tracking disabled.
- `pyproject.toml` pins `opik==2.3.4`; `.env.example` lists the settings.

---

*built with Opik · inspired by Opik's examples and documentation*
