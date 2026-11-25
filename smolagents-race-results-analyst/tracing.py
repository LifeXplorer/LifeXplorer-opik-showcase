"""Send every smolagents step to Opik as OpenTelemetry spans."""

import os

from openinference.instrumentation.smolagents import SmolagentsInstrumentor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace import SpanProcessor, TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor


class ProviderTagger(SpanProcessor):
    """Stamp model-call spans with the LLM provider so Opik can price them."""

    def __init__(self, provider: str) -> None:
        self.provider = provider

    def on_start(self, span, parent_context=None) -> None:
        # OpenInference sends the model name but no provider, and Opik prices a span only when it
        # knows both: without this attribute the OpenAIModel.generate spans show cost = null.
        # Opik's OTLP mapper reads gen_ai.system as the span's provider.
        if span.name.endswith(".generate"):
            span.set_attribute("gen_ai.system", self.provider)


def setup_tracing(project_name: str, llm_provider: str = "openai") -> TracerProvider | None:
    # Same switch the Opik SDK honours; lets tests and dry runs skip the exporter entirely.
    if os.getenv("OPIK_TRACK_DISABLE", "").lower() == "true":
        return None
    base = (os.getenv("OPIK_URL_OVERRIDE") or os.getenv("OPIK_URL") or "http://localhost:5173/api").rstrip("/")
    # Opik's OTLP ingest endpoint; the projectName header decides which Opik project the
    # traces land in.
    headers = {"Comet-Workspace": os.getenv("OPIK_WORKSPACE", "default"), "projectName": project_name}
    if os.getenv("OPIK_API_KEY"):  # Opik Cloud only; a local Opik needs no Authorization header
        headers["Authorization"] = os.environ["OPIK_API_KEY"]
    exporter = OTLPSpanExporter(endpoint=f"{base}/v1/private/otel/v1/traces", headers=headers)

    provider = TracerProvider()
    provider.add_span_processor(ProviderTagger(llm_provider))
    # SimpleSpanProcessor exports each span as it ends, so nothing is lost if the process dies mid-run.
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    # OpenInference patches smolagents: CodeAgent.run becomes the root of an Opik trace, each
    # step a child span carrying the generated code and its execution log, each model call an llm span.
    SmolagentsInstrumentor().instrument(tracer_provider=provider)
    return provider
