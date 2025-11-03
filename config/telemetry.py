"""
OpenTelemetry configuration helpers.

This module centralises tracer/metrics provider setup so the application
can enable or disable telemetry via environment variables without
scattering instrumentation logic across the codebase.
"""

import logging
from typing import Optional

from fastapi import FastAPI
from opentelemetry import trace
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.trace.export import (
    BatchSpanProcessor,
    ConsoleSpanExporter,
)

_logger = logging.getLogger(__name__)
_TELEMETRY_INITIALISED = False


def _build_span_processor(
    endpoint: Optional[str], insecure: bool
) -> BatchSpanProcessor:
    if endpoint:
        exporter = OTLPSpanExporter(endpoint=endpoint, insecure=insecure)
        _logger.info(
            "Configured OTLP exporter",
            extra={"endpoint": endpoint, "insecure": insecure},
        )
    else:
        exporter = ConsoleSpanExporter()
        _logger.warning(
            "OTLP endpoint not configured; falling back to console span exporter"
        )

    return BatchSpanProcessor(exporter)


def setup_telemetry(app: FastAPI, settings) -> None:
    """
    Configure OpenTelemetry for the FastAPI application.

    Args:
        app: FastAPI instance to instrument.
        settings: Application Settings object.
    """

    global _TELEMETRY_INITIALISED

    if _TELEMETRY_INITIALISED:
        return

    if not getattr(settings, "enable_telemetry", False):
        _logger.info("Telemetry disabled via configuration")
        return

    resource = Resource.create(
        {
            "service.name": settings.telemetry_service_name,
            "service.version": settings.app_version,
            "deployment.environment": settings.env,
        }
    )

    tracer_provider = TracerProvider(resource=resource)
    span_processor = _build_span_processor(
        settings.otel_exporter_otlp_endpoint, settings.otel_exporter_otlp_insecure
    )
    tracer_provider.add_span_processor(span_processor)

    trace.set_tracer_provider(tracer_provider)

    FastAPIInstrumentor.instrument_app(app)
    HTTPXClientInstrumentor().instrument()

    _TELEMETRY_INITIALISED = True
    _logger.info("Telemetry instrumentation initialised")
