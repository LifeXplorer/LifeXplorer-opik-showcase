import hashlib

from langchain_core.embeddings import Embeddings
from langchain_core.language_models.fake_chat_models import FakeListChatModel

from evaluation import DATASET_ITEMS
from rag import build_app, format_prompt, load_chunks


class WordHashEmbeddings(Embeddings):
    """Offline stand-in: a bag-of-words vector, so shared words mean similar vectors."""

    def _vec(self, text: str) -> list[float]:
        v = [0.0] * 64
        for word in text.lower().split():
            v[int(hashlib.md5(word.strip(".,?:").encode()).hexdigest(), 16) % 64] += 1.0
        return v

    def embed_documents(self, texts):
        return [self._vec(t) for t in texts]

    def embed_query(self, text):
        return self._vec(text)


def test_chunks_are_one_per_section_with_title():
    chunks = load_chunks()
    assert len(chunks) == 16
    assert all("\n\n## " in c for c in chunks)
    assert any(c.startswith("Choosing and Setting Up Your First Telescope") for c in chunks)


def test_prompt_puts_context_in_system_turn():
    messages = format_prompt("Q?", ["alpha", "beta"])
    assert messages[0][0] == "system" and "alpha" in messages[0][1] and "beta" in messages[0][1]
    assert messages[1] == ("user", "Q?")


def test_graph_returns_k_sections_and_the_model_answer():
    llm = FakeListChatModel(responses=["60 minutes."])
    app = build_app(WordHashEmbeddings(), llm, k=2)
    result = app.invoke({"question": "mirror cool-down time minutes air temperature"})
    assert result["answer"] == "60 minutes."
    assert len(result["context"]) == 2
    assert any("Cool-down time" in c for c in result["context"])


def test_k_controls_how_many_sections_are_retrieved():
    llm = FakeListChatModel(responses=["x"])
    one = build_app(WordHashEmbeddings(), llm, k=1).invoke({"question": "membership fees"})
    four = build_app(WordHashEmbeddings(), llm, k=4).invoke({"question": "membership fees"})
    assert (len(one["context"]), len(four["context"])) == (1, 4)


def test_dataset_has_references_and_an_unanswerable_question():
    assert all({"question", "expected_output"} <= set(i) for i in DATASET_ITEMS)
    assert any(i["expected_output"] == "The handbook doesn't say." for i in DATASET_ITEMS)
