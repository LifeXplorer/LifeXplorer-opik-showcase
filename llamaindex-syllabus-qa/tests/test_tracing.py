"""A real LlamaIndex query with tracking disabled: offline, and nothing is sent to Opik."""

from llama_index.core import Settings, SimpleDirectoryReader, VectorStoreIndex
from llama_index.core.embeddings import MockEmbedding
from llama_index.core.llms import MockLLM
from llama_index.core.node_parser import SentenceSplitter

from syllabus_qa import corpus, tracing


def test_query_runs_with_the_opik_handler_attached_and_tracking_disabled():
    handler = tracing.enable_tracing()  # with tracking disabled it attaches nothing
    Settings.llm = MockLLM()
    Settings.embed_model = MockEmbedding(embed_dim=8)
    Settings.node_parser = SentenceSplitter(chunk_size=128, chunk_overlap=0)
    pdfs = corpus.ensure_corpus()
    index = VectorStoreIndex.from_documents(SimpleDirectoryReader(input_files=[str(p) for p in pdfs]).load_data())
    response = index.as_query_engine(similarity_top_k=2).query("late work?")
    assert handler is None and len(response.source_nodes) == 2
