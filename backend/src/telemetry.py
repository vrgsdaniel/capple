"""OpenTelemetry tracing helpers.

``get_trace_context`` and ``setup_telemetry`` are the two public functions
consumed by ``src.main``.  Both are no-ops when ``settings.opentelemetry``
is *False* (the default), so no OTel packages need to be running locally.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from fastapi import FastAPI


def get_trace_context() -> dict[str, str]:
    """Return the active OpenTelemetry trace/span IDs as hex strings.

    Falls back to zeroed IDs when OTel is disabled or no span is active.
    """
    try:
        from opentelemetry import trace

        span = trace.get_current_span()
        ctx = span.get_span_context()
        if ctx.is_valid:
            return {
                "trace_id": format(ctx.trace_id, "032x"),
                "span_id": format(ctx.span_id, "016x"),
            }
    except Exception:
        pass
    return {"trace_id": "0" * 32, "span_id": "0" * 16}


def setup_telemetry(app: FastAPI, ignore_paths: list[str] | None = None) -> None:
    """Configure OTLP tracing for the FastAPI app.

    No-op when ``settings.opentelemetry`` is *False*.
    """
    from src.settings import get_settings

    settings = get_settings()
    if not settings.opentelemetry:
        return

    from opentelemetry import trace
    from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
    from opentelemetry.sdk.resources import SERVICE_NAME, Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor

    resource = Resource(attributes={SERVICE_NAME: settings.service_name})
    provider = TracerProvider(resource=resource)
    provider.add_span_processor(
        BatchSpanProcessor(
            OTLPSpanExporter(endpoint=settings.otel_exporter_endpoint, headers=settings.otel_exporter_headers)
        )
    )
    trace.set_tracer_provider(provider)

    FastAPIInstrumentor.instrument_app(
        app,
        excluded_urls=",".join(ignore_paths or []),
    )
