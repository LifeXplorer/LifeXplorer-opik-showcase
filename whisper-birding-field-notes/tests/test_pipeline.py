import json
from types import SimpleNamespace

import birding.pipeline as pipeline

NOTE = {"id": "n1", "title": "Test hide", "observer": "Mara", "voice": "nova", "text": "x"}


class FakeOpenAI:
    """Stub for the traced OpenAI client: no keys, no network."""

    def __init__(self):
        speech = SimpleNamespace(create=lambda **kw: SimpleNamespace(content=b"ID3fake"))
        trans = SimpleNamespace(create=lambda **kw: "Two Mallards and one Eurasian Jay.")
        payload = {"sightings": [
            {"species": "mallard", "count": 2},
            {"species": "Eurasian Jay", "count": 1, "note": "caching"},
        ]}
        chat = SimpleNamespace(create=lambda **kw: SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content=json.dumps(payload)))]))
        self.audio = SimpleNamespace(speech=speech, transcriptions=trans)
        self.chat = SimpleNamespace(completions=chat)


def test_traced_stage_runs_with_tracking_disabled(monkeypatch):
    # The @opik.track wrapper must not get in the way of a plain unit test.
    monkeypatch.setattr(pipeline, "get_client", lambda: FakeOpenAI())
    raw = pipeline.extract_sightings("Two Mallards and one Eurasian Jay.")
    assert [r["species"] for r in raw] == ["mallard", "Eurasian Jay"]


def test_full_pipeline_with_stubbed_client(monkeypatch, tmp_path):
    monkeypatch.setattr(pipeline, "get_client", lambda: FakeOpenAI())
    monkeypatch.setattr(pipeline, "AUDIO_DIR", tmp_path)
    result = pipeline.field_note_to_log(NOTE)
    assert (tmp_path / "n1.mp3").read_bytes() == b"ID3fake"
    assert result["transcript"].startswith("Two Mallards")
    assert [s["species"] for s in result["sightings"]] == ["Eurasian Jay", "Mallard"]
    assert "2 species, 3 individuals." in result["markdown"]
