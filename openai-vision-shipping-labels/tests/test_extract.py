import json
from types import SimpleNamespace

import main
from labels import SPECS, generate_labels


class StubCompletions:
    """Stands in for client.chat.completions and records the request it got."""

    def __init__(self, payload: dict):
        self.payload, self.calls = payload, []

    def create(self, **kwargs):
        self.calls.append(kwargs)
        message = SimpleNamespace(content=json.dumps(self.payload))
        return SimpleNamespace(choices=[SimpleNamespace(message=message)])


def test_extract_label_is_a_traced_function_that_still_works_untracked(tmp_path, monkeypatch):
    # With OPIK_TRACK_DISABLE=true the @opik.track wrapper is a pass-through:
    # the function runs, validates the stubbed reply and returns typed fields.
    spec = SPECS[0]
    stub = StubCompletions(spec.expected.model_dump())
    fake = SimpleNamespace(chat=SimpleNamespace(completions=stub))
    monkeypatch.setattr(main, "get_client", lambda: fake)
    path = generate_labels(tmp_path)[0]

    fields = main.extract_label(str(path))

    assert fields == spec.expected
    sent = stub.calls[0]
    assert sent["model"] == main.MODEL
    image_part = sent["messages"][1]["content"][1]
    assert image_part["image_url"]["url"].startswith("data:image/png;base64,")
    assert sent["response_format"]["json_schema"]["strict"] is True
