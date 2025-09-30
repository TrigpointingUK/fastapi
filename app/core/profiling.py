"""
Profiling middleware for FastAPI using pyinstrument.

This middleware provides performance profiling for FastAPI endpoints with support for:
- HTML output for quick viewing
- Speedscope JSON output for detailed flamegraph analysis
- Environment-based controls (disabled in production)
"""

import logging
from typing import Callable

from pyinstrument import Profiler
from pyinstrument.renderers import SpeedscopeRenderer
from starlette.middleware.base import BaseHTTPMiddleware

from fastapi import Request, Response

logger = logging.getLogger(__name__)


class ProfilingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for profiling requests with pyinstrument.

    Usage:
        # Enable profiling for a request (HTML output):
        GET /api/v1/trigs?profile=1

        # Enable profiling with speedscope JSON output:
        GET /api/v1/trigs?profile=speedscope

        # Enable profiling with HTML output (explicit):
        GET /api/v1/trigs?profile=html
    """

    def __init__(self, app, default_format: str = "html"):
        """
        Initialise profiling middleware.

        Args:
            app: The FastAPI application
            default_format: Default output format ("html" or "speedscope")
        """
        super().__init__(app)
        self.default_format = default_format

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request and optionally profile it.

        Args:
            request: The incoming request
            call_next: The next middleware or route handler

        Returns:
            Response with profiling data if requested
        """
        # Check if profiling is requested via query parameter
        profile_param = request.query_params.get("profile")

        if not profile_param:
            # No profiling requested, proceed normally
            return await call_next(request)

        # Determine output format
        if profile_param in ("speedscope", "json"):
            output_format = "speedscope"
        elif profile_param in ("html", "1", "true", "yes"):
            output_format = "html"
        else:
            # Default format if parameter value is unrecognised
            output_format = self.default_format

        # Start profiling
        profiler = Profiler()
        profiler.start()

        try:
            # Process the request
            response = await call_next(request)
        finally:
            # Stop profiling
            profiler.stop()

        # Generate profiling output
        try:
            if output_format == "speedscope":
                # Speedscope JSON format for flamegraph visualisation
                renderer = SpeedscopeRenderer()
                profiling_data = profiler.output(renderer=renderer)

                # Replace the response with profiling data
                return Response(
                    content=profiling_data,
                    media_type="application/json",
                    headers={
                        "Content-Disposition": 'attachment; filename="profile.speedscope.json"',
                        "X-Profile-Format": "speedscope",
                    },
                )
            else:
                # HTML format for quick viewing
                profiling_html = profiler.output_html()

                # Replace the response with profiling HTML
                return Response(
                    content=profiling_html,
                    media_type="text/html",
                    headers={
                        "X-Profile-Format": "html",
                    },
                )
        except Exception as e:
            logger.error(f"Error generating profiling output: {e}", exc_info=True)
            # Return the original response if profiling output fails
            return response


def should_enable_profiling(environment: str) -> bool:
    """
    Determine if profiling should be enabled based on environment.

    Args:
        environment: The current environment (development, staging, production)

    Returns:
        True if profiling should be enabled, False otherwise
    """
    # Enable profiling in development and staging only
    return environment.lower() in ("development", "staging", "local")
