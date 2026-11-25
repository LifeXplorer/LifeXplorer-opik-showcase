"""Index the syllabus PDFs and answer questions with cited sources."""

import pathlib
from dataclasses import dataclass

from llama_index.core import PromptTemplate, Settings, SimpleDirectoryReader, VectorStoreIndex
from llama_index.core.node_parser import SentenceSplitter
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.llms.openai import OpenAI

from syllabus_qa import corpus

TOP_K = 4  # four chunks: enough to compare one policy across the three courses

ANSWER_PROMPT = PromptTemplate(
    "You are a teaching-office assistant answering from course syllabi.\n"
    "Use only the syllabus excerpts below. Name the course code each rule belongs to, "
    "and quote figures exactly (percentages, day counts, times). If the excerpts do not "
    "say, reply that the syllabus does not specify it.\n"
    "---------------------\n{context_str}\n---------------------\n"
    "Question: {query_str}\nAnswer: "
)


@dataclass
class Answer:
    question: str
    text: str
    sources: list[dict]  # [{"file": ..., "score": ..., "text": ...}] in retrieval order


def configure_models() -> None:
    """Pick the cheap models and chunking used everywhere in the app."""
    Settings.llm = OpenAI(model="gpt-4o-mini", temperature=0.0)
    Settings.embed_model = OpenAIEmbedding(model="text-embedding-3-small")
    # Small chunks so one policy section is one chunk, not a whole page.
    Settings.node_parser = SentenceSplitter(chunk_size=128, chunk_overlap=0)


def build_query_engine(syllabi_dir: pathlib.Path = corpus.SYLLABI_DIR):
    """Load the PDFs (generating them if absent), embed them and return a query engine."""
    pdfs = corpus.ensure_corpus(syllabi_dir)
    configure_models()
    # input_files, not input_dir: the directory reader skips any path with a dot-folder in it.
    documents = SimpleDirectoryReader(input_files=[str(p) for p in pdfs]).load_data()
    index = VectorStoreIndex.from_documents(documents)
    return index.as_query_engine(similarity_top_k=TOP_K, text_qa_template=ANSWER_PROMPT)


def format_sources(response) -> list[dict]:
    """Flatten a LlamaIndex response's source nodes into plain dicts."""
    return [
        {
            "file": node.metadata.get("file_name", "?"),
            "score": round(node.score, 3) if node.score is not None else None,
            "text": node.text,
        }
        for node in response.source_nodes
    ]


def ask(query_engine, question: str) -> Answer:
    """Run one question through the engine."""
    response = query_engine.query(question)
    return Answer(question=question, text=str(response).strip(), sources=format_sources(response))
