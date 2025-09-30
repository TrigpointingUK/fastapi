"""
AWS X-Ray tracing configuration and utilities.
"""

import logging
from contextlib import contextmanager
from typing import Iterator, Optional

from app.core.config import settings

logger = logging.getLogger(__name__)


def setup_xray_tracing() -> bool:
    """
    Set up AWS X-Ray tracing if enabled.

    Returns:
        bool: True if tracing was set up successfully, False otherwise
    """
    if not settings.XRAY_ENABLED:
        logger.info("X-Ray tracing is disabled")
        return False

    try:
        # Import X-Ray SDK
        from aws_xray_sdk.core import xray_recorder
        from aws_xray_sdk.core.async_context import AsyncContext

        # Configure X-Ray recorder for AWS Fargate
        # If no daemon address is specified, use the default local daemon address
        # The X-Ray daemon sidecar container will be available at 127.0.0.1:2000
        daemon_address = settings.XRAY_DAEMON_ADDRESS or "127.0.0.1:2000"
        logger.info(f"Using X-Ray daemon address: {daemon_address}")

        # Use AsyncContext so tracing context flows across async boundaries
        # and threadpools used by FastAPI for sync endpoints. This ensures
        # current_segment is available inside decorated functions.
        xray_recorder.configure(
            service=settings.XRAY_SERVICE_NAME,
            sampling=True,  # enable sampling (rules can be configured via daemon or env)
            daemon_address=daemon_address,
            context=AsyncContext(),
            context_missing="LOG_ERROR",  # Log error instead of raising exception
        )

        # Patch selected libraries for automatic instrumentation
        # Avoid patching SQLAlchemy to prevent conflicts with dependency injection
        from aws_xray_sdk.core import patch

        # Patch specific libraries for automatic instrumentation
        # Note: FastAPI is not supported by aws-xray-sdk patching, use middleware instead
        patch(["requests", "boto3", "botocore"])  # Avoid 'sqlalchemy' and 'psycopg2'

        logger.info(f"X-Ray tracing enabled for service: {settings.XRAY_SERVICE_NAME}")
        return True

    except ImportError as e:
        logger.error(f"Failed to import X-Ray SDK: {e}")
        return False
    except Exception as e:
        logger.error(f"Failed to set up X-Ray tracing: {e}")
        return False


def setup_opentelemetry_tracing() -> bool:
    """
    Set up OpenTelemetry tracing with X-Ray exporter.

    NOTE: This is currently disabled to avoid conflicts with AWS X-Ray SDK.
    Use either AWS X-Ray SDK OR OpenTelemetry, not both.

    Returns:
        bool: True if tracing was set up successfully, False otherwise
    """
    # Disabled to avoid conflicts with AWS X-Ray SDK
    logger.info(
        "OpenTelemetry tracing is disabled to avoid conflicts with AWS X-Ray SDK"
    )
    return False

    try:
        from opentelemetry import trace
        from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import (
            OTLPSpanExporter,
        )
        from opentelemetry.instrumentation.boto3 import Boto3Instrumentor
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
        from opentelemetry.instrumentation.requests import RequestsInstrumentor

        # from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor

        # Create resource with service name
        resource = Resource.create(
            {
                "service.name": settings.XRAY_SERVICE_NAME,
                "service.version": "1.0.0",
            }
        )

        # Set up tracer provider
        tracer_provider = TracerProvider(resource=resource)
        trace.set_tracer_provider(tracer_provider)

        # Set up X-Ray OTLP exporter
        otlp_exporter = OTLPSpanExporter(
            endpoint="http://localhost:4317",  # X-Ray daemon OTLP endpoint
        )

        # Add span processor
        span_processor = BatchSpanProcessor(otlp_exporter)
        tracer_provider.add_span_processor(span_processor)

        # Instrument libraries
        FastAPIInstrumentor.instrument()
        # Skip SQLAlchemy instrumentation to avoid conflicts with X-Ray SDK
        # SQLAlchemyInstrumentor().instrument()
        RequestsInstrumentor().instrument()
        Boto3Instrumentor().instrument()

        logger.info(
            f"OpenTelemetry tracing enabled for service: {settings.XRAY_SERVICE_NAME}"
        )
        return True

    except ImportError as e:
        logger.error(f"Failed to import OpenTelemetry packages: {e}")
        return False
    except Exception as e:
        logger.error(f"Failed to set up OpenTelemetry tracing: {e}")
        return False


def get_trace_id() -> Optional[str]:
    """
    Get the current trace ID if tracing is active.

    Returns:
        Optional[str]: Current trace ID or None if not available
    """
    try:
        from aws_xray_sdk.core import xray_recorder

        segment = xray_recorder.current_segment()
        if segment:
            return segment.trace_id
    except (ImportError, AttributeError, Exception) as e:
        # X-Ray not available or not configured
        logger.debug(f"X-Ray trace ID not available: {e}")
    return None


def add_trace_metadata(metadata: dict) -> None:
    """
    Add metadata to the current X-Ray segment.

    Args:
        metadata: Dictionary of metadata to add
    """
    try:
        from aws_xray_sdk.core import xray_recorder

        segment = xray_recorder.current_segment()
        if segment:
            segment.put_metadata("custom", metadata)
    except Exception as e:
        logger.warning(f"Failed to add trace metadata: {e}")


def trace_function(name: Optional[str] = None):
    """
    Decorator to trace a function with X-Ray subsegments.

    Args:
        name: Optional name for the trace subsegment
    """

    def decorator(func):
        import inspect
        from functools import wraps

        if inspect.iscoroutinefunction(func):

            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                if not settings.XRAY_ENABLED:
                    return await func(*args, **kwargs)

                try:
                    from aws_xray_sdk.core import xray_recorder

                    current_segment = xray_recorder.current_segment()
                    if current_segment is None:
                        return await func(*args, **kwargs)

                    subsegment_name = name or f"{func.__module__}.{func.__name__}"
                    with xray_recorder.in_subsegment(subsegment_name):
                        return await func(*args, **kwargs)
                except Exception as e:
                    logger.warning(
                        f"Failed to trace async function {func.__name__}: {e}"
                    )
                    return await func(*args, **kwargs)

            return async_wrapper

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            if not settings.XRAY_ENABLED:
                return func(*args, **kwargs)

            try:
                from aws_xray_sdk.core import xray_recorder

                current_segment = xray_recorder.current_segment()
                if current_segment is None:
                    return func(*args, **kwargs)

                subsegment_name = name or f"{func.__module__}.{func.__name__}"
                with xray_recorder.in_subsegment(subsegment_name):
                    return func(*args, **kwargs)
            except Exception as e:
                logger.warning(f"Failed to trace function {func.__name__}: {e}")
                return func(*args, **kwargs)

        return sync_wrapper

    return decorator


@contextmanager
def in_subsegment_safe(name: str) -> Iterator[None]:
    """
    Context manager that opens an X-Ray subsegment if a current segment exists.

    Falls back to a no-op when X-Ray is disabled or context is missing.
    """
    if not settings.XRAY_ENABLED:
        yield None
        return

    try:
        from aws_xray_sdk.core import xray_recorder

        current_segment = xray_recorder.current_segment()
        if current_segment is None:
            # No active segment, no-op
            yield None
            return

        with xray_recorder.in_subsegment(name):
            yield None
    except Exception as e:
        logger.debug(f"in_subsegment_safe fallback due to: {e}")
        yield None
