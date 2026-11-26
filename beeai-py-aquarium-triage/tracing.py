"""All Opik wiring lives here: OpenInference instrumentation + an OTLP exporter pointed at Opik."""
import os

from openinference.instrumentation.beeai import BeeAIInstrumentor
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, SpanExportResult


def opik_attributes(attrs: dict) -> dict:
    """Return a copy of an OpenInference span's attributes that Opik prices and types correctly."""
    attrs = dict(attrs)
    kind = attrs.get("openinference.span.kind")
    if kind == "LLM" and "llm.provider" in attrs:
        # Opik prices a span from provider + model + usage; it ignores OpenInference's
        # `llm.provider`/`llm.cost.*`, so without this the llm spans show cost = null.
        attrs["gen_ai.provider.name"] = attrs["llm.provider"]
    elif kind == "TOOL":
        # Opik only types a span `tool` from gen_ai.tool.call.* attributes, so TOOL spans would be
        # `general`. Re-publish the tool's input/output under those keys (they become its input/output).
        for src, dst in (("input.value", "gen_ai.tool.call.arguments"), ("output.value", "gen_ai.tool.call.result")):
            if src in attrs:
                attrs[dst] = attrs.pop(src)
    return attrs


class OpikFriendlyExporter(OTLPSpanExporter):
    """OTLP exporter that tidies BeeAI's OpenInference spans for Opik on the way out."""

    def export(self, spans):
        # BeeAI streams the model and the instrumentation emits one `new_token` span per chunk;
        # dropping them keeps each Opik trace to the agent, llm and tool spans worth reading.
        kept = [s for s in spans if s.name != "new_token"]
        for s in kept:
            s._attributes = opik_attributes(s.attributes or {})  # ReadableSpan has no public setter
        return super().export(kept) if kept else SpanExportResult.SUCCESS


def setup_tracing(project: str):
    """Instrument BeeAI and export to Opik's OTLP endpoint. Returns a flush-and-shutdown callable."""
    if os.getenv("OPIK_TRACK_DISABLE", "").lower() == "true":
        return lambda: None
    base = os.getenv("OPIK_URL_OVERRIDE", "http://localhost:5173/api/").rstrip("/")
    # projectName header routes every trace to this Opik project; Comet-Workspace picks the workspace.
    exporter = OpikFriendlyExporter(
        endpoint=f"{base}/v1/private/otel/v1/traces",
        headers={"projectName": project, "Comet-Workspace": os.getenv("OPIK_WORKSPACE", "default")},
    )
    provider = TracerProvider()
    provider.add_span_processor(BatchSpanProcessor(exporter))
    trace.set_tracer_provider(provider)
    # BeeAIInstrumentor turns each agent run, ReAct iteration, model call and tool call into a span.
    BeeAIInstrumentor().instrument()

    def shutdown() -> None:
        provider.force_flush()
        provider.shutdown()

    return shutdown
