"""
URL utilities for building absolute photo URLs.
"""


def join_url(base: str, path: str) -> str:
    """Join base URL and relative path with exactly one slash.

    If base is empty, returns the path unchanged.
    """
    if not base:
        return path
    if base.endswith("/"):
        return f"{base}{path}"
    return f"{base}/{path}"
