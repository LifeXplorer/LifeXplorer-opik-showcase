"""Opik tracing for both processes: an OTLP exporter plus Temporal's TracingInterceptor."""
import os

from dotenv import find_dotenv, load_dotenv
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from temporalio.contrib.opentelemetry import TracingInterceptor

load_dotenv(find_dotenv())

PROJECT_NAME = os.environ.get("OPIK_PROJECT_NAME", "temporal-py-grant-review")


def setup_tracing(service_name: str) -> TracerProvider:
    """Register an OTLP exporter pointed at Opik's OpenTelemetry endpoint for this process.

    Call it in the client AND the worker with the same project name: each process exports its
    own spans, and Opik joins them into one trace through the shared trace id.
    """
    base = os.environ.get("OPIK_URL_OVERRIDE", "https://www.comet.com/opik/api").rstrip("/")
    headers = {"projectName": PROJECT_NAME, "Comet-Workspace": os.environ.get("OPIK_WORKSPACE", "default")}
    if api_key := os.environ.get("OPIK_API_KEY"):  # local self-hosted needs no key
        headers["Authorization"] = api_key
    exporter = OTLPSpanExporter(endpoint=f"{base}/v1/private/otel/v1/traces", headers=headers)
    provider = TracerProvider(resource=Resource.create({SERVICE_NAME: service_name}))
    provider.add_span_processor(BatchSpanProcessor(exporter))
    trace.set_tracer_provider(provider)
    return provider


def tracing_interceptor() -> TracingInterceptor:
    # Emits StartWorkflow / RunWorkflow / StartActivity / RunActivity spans (one RunActivity per
    # attempt) and carries the trace context through Temporal's headers from client to worker.
    return TracingInterceptor()
