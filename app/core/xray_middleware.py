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
        """
        if not self.xray_enabled:
            return await call_next(request)

        try:
            from aws_xray_sdk.core import xray_recorder

            # Start timing
            start_time = time.time()

            # Create segment for this request
            segment_name = f"{request.method} {request.url.path}"

            with xray_recorder.capture(segment_name) as segment:
                # Add request metadata
                if segment:
                    segment.put_metadata(
                        "request",
                        {
                            "method": request.method,
                            "url": str(request.url),
                            "path": request.url.path,
                            "query_params": dict(request.query_params),
                            "headers": dict(request.headers),
                            "client_ip": (
                                request.client.host if request.client else None
                            ),
                        },
                    )

                # Process the request
                response = await call_next(request)

                # Calculate duration
                duration = time.time() - start_time

                # Add response metadata
                if segment:
                    segment.put_metadata(
                        "response",
                        {
                            "status_code": response.status_code,
                            "headers": dict(response.headers),
                            "duration_ms": duration * 1000,
                        },
                    )

                    # Add custom annotations for better filtering
                    segment.put_annotation("http.method", request.method)
                    segment.put_annotation("http.status_code", response.status_code)
                    segment.put_annotation("http.url", str(request.url))
                    segment.put_annotation("duration_ms", duration * 1000)

                    # Add error information if status code indicates error
                    if response.status_code >= 400:
                        segment.put_annotation("error", True)
                        segment.put_annotation(
                            "error_type", f"HTTP_{response.status_code}"
                        )

                return response

        except Exception as e:
            logger.error(f"X-Ray middleware error: {e}")
            # Fall back to normal processing
            return await call_next(request)


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
