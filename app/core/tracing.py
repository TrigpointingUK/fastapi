"""
Simple timing utilities for performance monitoring.
"""

import logging
import time
from contextlib import contextmanager
from typing import Iterator, Optional

logger = logging.getLogger(__name__)


@contextmanager
def time_block(name: str, log_level: int = logging.INFO) -> Iterator[None]:
    """
    Context manager for timing code blocks.

    Usage:
        with time_block("image.process"):
            # your code here
            process_image()

    Args:
        name: Name/description of the code block being timed
        log_level: Logging level to use (default: INFO)
    """
    start_time = time.time()
    try:
        yield
    finally:
        duration = time.time() - start_time
        logger.log(log_level, f"{name} took {duration * 1000:.1f}ms")


def trace_function(name: Optional[str] = None):
    """
    Decorator stub for backwards compatibility.

    This is a no-op decorator that allows existing @trace_function
    decorators to remain in code without breaking anything.
    Use time_block() context manager for actual timing when needed.
    """

    def decorator(func):
        return func

    return decorator
