"""Offline tests: no provider keys, Opik tracking disabled, model client stubbed."""

from types import SimpleNamespace

from podcast_topics import classifier
from podcast_topics.episodes import EPISODES, TOPICS
from podcast_topics.metric import normalize, topic_accuracy
from podcast_topics.prompts import USER_TEMPLATE, to_library_messages


def test_every_episode_has_a_known_topic():
    assert len(EPISODES) >= 20
    assert {label for _, label in EPISODES} == set(TOPICS)


def test_metric_is_strict_exact_match():
    item = {"label": "science"}
    assert topic_accuracy(item, "Science.") == 1.0
    assert topic_accuracy(item, '"science"') == 1.0
    assert topic_accuracy(item, "This episode is about science.") == 0.0
    assert normalize("  True-Crime! ") == "true-crime"


def test_library_messages_use_mustache_braces():
    out = to_library_messages([{"role": "user", "content": USER_TEMPLATE}])
    assert out == [{"role": "user", "content": "{{episode}}"}]


class _StubCompletions:
    def create(self, **kwargs):
        self.kwargs = kwargs
        message = SimpleNamespace(content="history")
        return SimpleNamespace(choices=[SimpleNamespace(message=message)])


def test_traced_classify_runs_with_tracking_disabled(monkeypatch):
    stub = _StubCompletions()
    fake = SimpleNamespace(chat=SimpleNamespace(completions=stub))
    monkeypatch.setattr(classifier, "get_client", lambda: fake)
    # @opik.track is on classify(); it must behave as a plain function in unit tests.
    assert classifier.classify("A dockworker's diary from 1919.") == "history"
    assert stub.kwargs["messages"][1]["content"] == "A dockworker's diary from 1919."
