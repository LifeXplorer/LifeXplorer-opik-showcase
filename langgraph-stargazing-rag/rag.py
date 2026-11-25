"""Two-node RAG graph over the Brightwater Stargazers' Club handbook.

retrieve -> generate. The graph is built from injected embeddings and chat
model so the same code runs against OpenAI or against offline fakes.
"""

import pathlib

from langchain_core.embeddings import Embeddings
from langchain_core.language_models import BaseChatModel
from langchain_core.vectorstores import InMemoryVectorStore
from langgraph.graph import END, START, StateGraph
from typing_extensions import TypedDict

DOCS_DIR = pathlib.Path(__file__).parent / "docs"

SYSTEM_PROMPT = (
    "You answer questions for members of the Brightwater Stargazers' Club. "
    "Use only the handbook excerpts below. If they do not contain the answer, "
    "reply exactly: \"The handbook doesn't say.\" Keep answers to two sentences.\n\n"
)


class State(TypedDict):
    question: str
    context: list[str]
    answer: str


def load_chunks(docs_dir: pathlib.Path = DOCS_DIR) -> list[str]:
    """One chunk per '##' section, each prefixed with its document title."""
    chunks = []
    for path in sorted(docs_dir.glob("*.md")):
        title, *sections = path.read_text().split("\n## ")
        for section in sections:
            chunks.append(f"{title.lstrip('# ').strip()}\n\n## {section.strip()}")
    return chunks


def format_prompt(question: str, context: list[str]) -> list[tuple[str, str]]:
    """Chat messages: the excerpts go into the system turn, the question stays separate."""
    return [
        ("system", SYSTEM_PROMPT + "\n\n---\n\n".join(context)),
        ("user", question),
    ]


def build_app(embeddings: Embeddings, llm: BaseChatModel, k: int = 3,
              chunks: list[str] | None = None):
    """Compile the retrieve -> generate graph, fetching `k` sections per question."""
    store = InMemoryVectorStore.from_texts(chunks or load_chunks(), embeddings)

    def search_handbook(question: str) -> list[str]:
        return [d.page_content for d in store.similarity_search(question, k=k)]

    def retrieve(state: State) -> dict:
        return {"context": search_handbook(state["question"])}

    def generate(state: State) -> dict:
        reply = llm.invoke(format_prompt(state["question"], state["context"]))
        return {"answer": reply.content}

    graph = StateGraph(State)
    graph.add_node("retrieve", retrieve)
    graph.add_node("generate", generate)
    graph.add_edge(START, "retrieve")
    graph.add_edge("retrieve", "generate")
    graph.add_edge("generate", END)
    return graph.compile()
