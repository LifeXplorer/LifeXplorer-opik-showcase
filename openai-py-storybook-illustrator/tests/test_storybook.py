"""Offline tests: no provider keys, no Opik."""

import base64
import types
from pathlib import Path

from opik.api_objects.prompt.text.prompt_template import PromptTemplate

import illustrator
from storybook import BRIEF_V1, BRIEF_V2, CHARACTER, PAGES


class FakeBrief:
    """Stands in for an Opik library prompt, rendering with Opik's own template engine."""

    version = "v2"

    def __init__(self, template: str):
        self.template = PromptTemplate(template)

    def format(self, **kw):
        return self.template.format(**kw)


PNG = base64.b64encode(b"\x89PNG fake bytes").decode()


class FakeClient:
    def __init__(self):
        self.chat = types.SimpleNamespace(completions=types.SimpleNamespace(create=self._chat))
        self.images = types.SimpleNamespace(generate=self._image)
        self.image_prompts = []

    def _chat(self, **kw):
        msg = types.SimpleNamespace(content="  Wren lifts her lantern on a dusky hill.  ")
        return types.SimpleNamespace(choices=[types.SimpleNamespace(message=msg)])

    def _image(self, **kw):
        self.image_prompts.append(kw["prompt"])
        usage = types.SimpleNamespace(input_tokens=10, output_tokens=100, total_tokens=110)
        return types.SimpleNamespace(data=[types.SimpleNamespace(b64_json=PNG)], usage=usage)


def test_v2_adds_rules_and_keeps_placeholders():
    for tpl in (BRIEF_V1, BRIEF_V2):
        assert "{{character}}" in tpl and "{{scene}}" in tpl
    assert "No lettering" in BRIEF_V2 and "No lettering" not in BRIEF_V1


def test_render_brief_fills_variables():
    text = illustrator.render_brief(FakeBrief(BRIEF_V2), "Wren's mossy hill")
    assert CHARACTER in text and "Wren's mossy hill" in text and "{" not in text


def test_describe_scene_strips_whitespace():
    assert illustrator.describe_scene(FakeClient(), PAGES[0]["text"]).startswith("Wren lifts")


def test_generate_image_writes_png_with_tracking_disabled(tmp_path: Path):
    # Runs the @track-decorated function with OPIK_TRACK_DISABLE=true: the
    # decorator must not get in the way of plain unit tests.
    out = illustrator.generate_image(FakeClient(), "prompt", tmp_path / "x.png")
    assert (tmp_path / "x.png").read_bytes() == b"\x89PNG fake bytes"
    assert out["bytes"] == len(b"\x89PNG fake bytes")


def test_illustrate_page_end_to_end_with_stubs(tmp_path: Path):
    client = FakeClient()
    r = illustrator.illustrate_page(client, FakeBrief(BRIEF_V2), PAGES[1], tmp_path)
    assert Path(r["file"]).name == "v2-page-2.png" and Path(r["file"]).exists()
    assert "Wren lifts her lantern" in client.image_prompts[0]
