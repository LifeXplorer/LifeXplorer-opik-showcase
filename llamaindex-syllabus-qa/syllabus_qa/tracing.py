"""Opik tracing for the syllabus Q&A pipeline."""

from llama_index.core import Settings
from llama_index.core.callbacks import CallbackManager
from opik.integrations.llama_index import LlamaIndexCallbackHandler

PROJECT_NAME = "llamaindex-syllabus-qa"


def enable_tracing() -> LlamaIndexCallbackHandler:
    """Attach Opik's LlamaIndex callback handler to every query engine in the process."""
    # The handler turns each query() into one trace in PROJECT_NAME, with child spans for
    # retrieve (+ its embedding call) and synthesize (+ templating and the llm call, which
    # carries tokens and cost). Without it nothing reaches Opik.
    handler = LlamaIndexCallbackHandler(
        project_name=PROJECT_NAME,
        # Skip the one-off trace for embedding the three PDFs at startup: the project then
        # holds only question traces.
        skip_index_construction_trace=True,
    )
    Settings.callback_manager = CallbackManager([handler])
    return handler
