<div align="center">

# Parcel Eyes

**`openai-vision-shipping-labels`**

*A vision model that reads a label wrong looks exactly like one that reads it right, until you can see the label.*

![Python](https://img.shields.io/badge/python-3.12%2B-3776AB?style=flat&logo=python&logoColor=white)
![OpenAI](https://img.shields.io/badge/openai-3.57%2B-412991?style=flat&logo=openai&logoColor=white)
![Pillow](https://img.shields.io/badge/pillow-labels%20drawn%20at%20run%20time-3B77A8?style=flat)
[![Opik](https://img.shields.io/badge/Opik-2.3%2B-2f54eb?style=flat)](https://github.com/comet-ml/opik)
[![uv](https://img.shields.io/badge/setup-uv-DE5FE9?style=flat&logo=uv&logoColor=white)](https://docs.astral.sh/uv/)

</div>

---

A warehouse scanner that cannot decode a barcode falls back on a camera and a
vision model: read the tracking number, the recipient, the postal code, the
weight, the service level, whether the parcel is fragile. The output is a typed
record, and when one field is wrong the cause is almost never in the text. It
is in the pixels: a smudged `O` that is really a zero, a weight someone crossed
out and rewrote. You cannot grep an image. This example makes the image part of
the evidence. Every extraction in Opik carries the label PNG it came from, and
a test suite with a deliberately honest set of hard labels tells you which
fields the model still gets wrong.

## What you'll build

`labels.py` draws six fictional shipping labels with Pillow and keeps the true
values for each. Two are easy, one is dense (a weight printed in both kg and
lb, four distractor reference numbers and a FRAGILE stamp), one is rotated 90
degrees, one is a faded noisy thermal print whose tracking number is full of
`O/0`, `I/1`, `S/5` and `B/8` lookalikes, and one has a printed weight crossed
out with the real one written beside it.

`main.py` sends each PNG to `gpt-4o-mini` and validates the reply into a
`LabelFields` pydantic model (tracking number, carrier, recipient, postal code
as text, weight in kg, service level, fragile flag) using strict structured
output. Opik is wired in three places: `track_openai` turns each completion
into an `llm` span, `@opik.track` groups it under one `extract_label` trace,
and `update_current_trace(attachments=[Attachment(...)])` stores the label
image on that trace. `checks.py` turns the ground truth into three plain
sentences per label, such as "The tracking number is exactly `QP-O8B1-I1O0-S5Z2`
with every lookalike as written", and `opik.run_tests` has an LLM judge grade
them. The expected values live only in those assertions, never in the item
data, so the judge cannot read answers off its input.

## See it in Opik

Open the `openai-vision-shipping-labels` project at `http://localhost:5173`
(or your own Opik). After one run it holds **24 traces**: 6 `extract_label`
traces from the plain loop at the top of `main.py`, and 18
`evaluation_task` traces from the suite (6 labels x 3 runs each). Open any of
them and look at the Attachments tab: the PNG sits there, for example
`label_01_clean.png` (36,872 bytes), next to the typed output. All 24 traces
carry their label.

Click into an `extract_label` trace. The tree is an `extract_label` span
(`general`) with a `chat_completion_create` span (`llm`, model
`gpt-4o-mini-2024-07-18`) inside. Look at the token column: about **25,900
tokens per label**, almost all of it image input, at roughly $0.004 per call.
Vision tokens are what make these pipelines expensive, and the cost is tracked
per call.

Now the faded label, `label_04_faded.png`. Its trace output says tracking
number `QP-08B1-I100-S5Z2`; the image says `QP-O8B1-I1O0-S5Z2`. The model
turned two letter O's into zeros, which is a plausible mistake and a wrong
record. Because the image is attached, you see that in seconds instead of
guessing.

Then open **Test Suites > openai-vision-shipping-labels**: 6 items, 3 global
assertions, and an execution policy of 3 runs per item with 2 needed to pass.
The latest run is the experiment `shipping-labels-gpt-4o-mini`, with 18
runs. It passes **4 of 6 labels (67%)**, and the two failures are stable, 0 of
3 runs each:

- `label_04_faded.png`: the tracking-number assertion fails every time, the O-versus-0 swap above.
- `label_05_struck_weight.png`: the model returns `weight_kg` 9.8, the crossed-out printed value, not the handwritten 11.30, even though the prompt says the rewritten value wins.

The rotated label passes, and so does the dense one with its lb/kg pair and
distractor numbers. Your pass rate can differ by a label from run to run (see
Gotchas), but the two hard ones stay hard.

## Run it yourself

1. `cp .env.example .env` and add `OPENAI_API_KEY` (a repo-root `.env` works too). Opik settings come from `~/.opik.config` after `opik configure`, or set `OPIK_URL_OVERRIDE` and `OPIK_WORKSPACE` for a local stack.
2. `uv sync`
3. `uv run main.py`
4. Open the project in Opik, click a trace, open its Attachments tab, then open the suite and the experiment link printed at the end.

A run takes under a minute and costs a few cents (the Opik cost column for the
project summed to about $0.06 including the judge). The labels are redrawn into
`labels/` on every run, so there is nothing to generate by hand. The fonts are
macOS or DejaVu ones with Pillow's built-in fallback, so on a machine with none
of them the pixels (and the model's mistakes) can shift slightly.

## Poke around

- Change `"detail": "high"` to `"low"` in `main.py` and re-run. Compare the token column on the llm spans before and after, and see which labels the suite starts to fail.
- In `labels.py` set the faded label's `ink` from 150 up toward its `paper` value of 226 and find where even the clean fields break.
- Rewrite the struck-weight line in `SYSTEM_PROMPT` (or reorder the label so the new value comes first) and see whether the 9.8 error goes away.
- Add a seventh `LabelSpec`, for instance a label with a pounds-only weight. `suite_items()` picks it up and `suite.insert` leaves the existing six untouched.

## Gotchas we hit

**"One label failed an assertion in the first run and passed in the next, and the extraction looked identical."**
The suite re-extracts every label and an LLM judge grades each assertion, so a single run can flip on one unlucky read or judge call. In an early run with one run per item the rotated label failed its recipient-and-postal-code assertion while the direct extraction of the same label was fully correct. Fix: give the suite an execution policy so a label needs a majority:
`get_or_create_test_suite(..., global_execution_policy={"runs_per_item": 3, "pass_threshold": 2})`. We deleted and recreated our earlier suite to apply it, so do the same if you already have one.

**"The llm span has the image inside its input, but its Attachments list is empty."**
With `track_openai` the label travels as a base64 data URL inside the span input. The Opik SDK only moves an embedded base64 string out into an attachment when it is larger than `min_base64_embedded_attachment_size`, which defaults to 256,000 bytes (env var `OPIK_MIN_BASE64_EMBEDDED_ATTACHMENT_SIZE`); smaller ones stay inline. In our runs only one of six llm spans got an attachment: the 274 KB faded label, whose base64 is over the threshold. Fix: attach explicitly on the trace, which works for every image:
`opik_context.update_current_trace(attachments=[Attachment(data=path, content_type="image/png")])`. Alternatively, lower `OPIK_MIN_BASE64_EMBEDDED_ATTACHMENT_SIZE` so smaller images are extracted from span inputs too.

**"`PydanticSerializationUnexpectedValue` warnings flood the terminal during the suite run."**
They come from the judge call inside `opik.run_tests`, not from this app, and the results are unaffected. If the noise bothers you, filter them with `python -W ignore::UserWarning main.py` (this also hides other `UserWarning`s).

## How it's put together

- `labels.py`: `LabelFields` (the typed record and its strict JSON schema), the six `LabelSpec`s with their ground truth, and the Pillow renderer.
- `main.py`: the traced extraction (`get_client`, `extract_label`), then the suite and `run_tests`.
- `checks.py`: judge assertions built from the ground truth, `suite_items()`, and `field_diff`, an exact local comparison printed next to the judge's verdict.
- `tests/test_labels.py`: labels render byte-identically, the rotated one is landscape, the schema is strict.
- `tests/test_checks.py`: assertions carry the truth, truth never leaks into item data, `field_diff` catches lookalike swaps.
- `tests/test_extract.py`: calls the `@opik.track`-decorated `extract_label` with a stubbed client and tracking disabled, to show decorators do not get in the way of unit tests.
- `.env.example`, `.gitignore`: keys needed, and the generated `labels/` folder is ignored.

Offline tests, no keys and no Opik traffic:
`env -u OPENAI_API_KEY -u ANTHROPIC_API_KEY OPIK_TRACK_DISABLE=true uv run pytest`

---

*built with Opik · inspired by Opik's examples and documentation*
