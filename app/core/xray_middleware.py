"""
Custom X-Ray middleware for FastAPI.
"""

import logging
import time
from typing import Callable, Optional

from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import settings
from fastapi import Request, Response

logger = logging.getLogger(__name__)


class XRayMiddleware(BaseHTTPMiddleware):
    """
    Custom X-Ray middleware for FastAPI that adds detailed tracing information.
    """

    def __init__(self, app, service_name: Optional[str] = None):
        super().__init__(app)
        self.service_name = service_name or settings.XRAY_SERVICE_NAME
        self.xray_enabled = settings.XRAY_ENABLED

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process the request and add X-Ray tracing.

        Uses manual segment management (begin_segment/end_segment) instead of
        capture() context manager because ThreadLocalContext doesn't propagate
        correctly through async/await boundaries with the context manager pattern.
        """
        if not self.xray_enabled:
            return await call_next(request)

        segment = None
        segment_started = False

        try:
            from aws_xray_sdk.core import xray_recorder

            # Start timing
            start_time = time.time()

            # Create segment name from request
            segment_name = self.service_name

            # Manually begin segment for ThreadLocalContext compatibility with async
            segment = xray_recorder.begin_segment(name=segment_name)
            segment_started = True

            # Add request metadata
            if segment:
                try:
                    segment.put_http_meta("method", request.method)
                    segment.put_http_meta("url", str(request.url))
                    if request.client:
                        segment.put_http_meta("client_ip", request.client.host)
                    if request.headers.get("user-agent"):
                        segment.put_http_meta(
                            "user_agent", request.headers.get("user-agent")
                        )
                except Exception as meta_err:
                    logger.debug(f"Failed to add X-Ray request metadata: {meta_err}")

            # Process the request
            response = await call_next(request)

            # Calculate duration
            duration = time.time() - start_time

            # Add response metadata
            if segment:
                try:
                    segment.put_http_meta("status", response.status_code)
                    if response.headers.get("content-length"):
                        segment.put_http_meta(
                            "content_length", response.headers.get("content-length")
                        )

                    # Add custom annotations for better filtering
                    segment.put_annotation("http.method", request.method)
                    segment.put_annotation("http.status_code", response.status_code)
                    segment.put_annotation("http.path", request.url.path)
                    segment.put_annotation("duration_ms", duration * 1000)

                    # Mark errors
                    if response.status_code >= 400:
                        segment.put_annotation("error", True)
                except Exception as meta_err:
                    logger.debug(f"Failed to add X-Ray response metadata: {meta_err}")

            # End segment before returning
            if segment_started:
                try:
                    xray_recorder.end_segment()
                    segment_started = False
                except Exception as e:
                    logger.warning(f"Failed to end X-Ray segment: {e}")

            return response

        except Exception as e:
            # Mark segment as error
            if segment:
                try:
                    import sys
                    import traceback

                    _, _, tb = sys.exc_info()
                    stack = traceback.extract_tb(tb) if tb else None
                    segment.add_exception(e, stack)
                except Exception as add_exc_err:
                    logger.debug(f"Failed to record X-Ray exception: {add_exc_err}")

            # Re-raise the exception
            raise

        finally:
            # Ensure segment is ended in all cases
            if segment_started:
                try:
                    xray_recorder.end_segment()
                except Exception as e:
                    logger.debug(f"Failed to end X-Ray segment in finally: {e}")


def add_xray_headers(response: Response, trace_id: Optional[str] = None) -> Response:
    """
    Add X-Ray trace headers to the response.

    Args:
        response: FastAPI Response object
        trace_id: Optional trace ID to include in headers

    Returns:
        Response with X-Ray headers added
    """
    if not settings.XRAY_ENABLED:
        return response

    try:
        from aws_xray_sdk.core import xray_recorder

        # Get current trace ID
        current_trace_id = trace_id or getattr(xray_recorder, "current_trace_id", None)

        if current_trace_id:
            response.headers[settings.XRAY_TRACE_HEADER] = f"Root={current_trace_id}"

    except Exception as e:
        logger.warning(f"Failed to add X-Ray headers: {e}")

    return response
