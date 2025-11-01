"""
Utility functions for mapping condition codes to human-readable descriptions.

Based on the legacy PHP code condition mappings.
"""

from typing import Dict


def get_condition_description(condition_code: str) -> str:
    """
    Convert condition code to human-readable description.

    Based on the legacy PHP code condition mappings:
    - 'Z' -> "" (empty/not logged) -> "Not Logged"
    - 'N' -> "Couldn't find it"
    - 'G' -> "Good"
    - 'S' -> "Slightly damaged"
    - 'C' -> "Converted"
    - 'D' -> "Damaged"
    - 'R' -> "Remains"
    - 'T' -> "Toppled"
    - 'M' -> "Moved"
    - 'Q' -> "Possibly missing"
    - 'X' -> "Destroyed"
    - 'V' -> "Unreachable but visible"
    - 'P' -> "Inaccessible"

    Args:
        condition_code: Single character condition code

    Returns:
        Human-readable condition description
    """
    condition_map = {
        "Z": "Not Logged",  # Default/empty selection in the PHP form
        "N": "Couldn't find it",
        "G": "Good",
        "S": "Slightly damaged",
        "C": "Converted",
        "D": "Damaged",
        "R": "Remains",
        "T": "Toppled",
        "M": "Moved",
        "Q": "Possibly missing",
        "X": "Destroyed",
        "V": "Unreachable but visible",
        "P": "Inaccessible",
    }

    return condition_map.get(str(condition_code).upper(), "Unknown")


def get_condition_counts_by_description(
    condition_counts: Dict[str, int],
) -> Dict[str, int]:
    """
    Convert condition code counts to human-readable description counts.

    Args:
        condition_counts: Dictionary mapping condition codes to counts

    Returns:
        Dictionary mapping human-readable descriptions to counts
    """
    result: Dict[str, int] = {}
    for code, count in condition_counts.items():
        description = get_condition_description(code)
        if description in result:
            result[description] += count
        else:
            result[description] = count

    return result
