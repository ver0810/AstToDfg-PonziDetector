"""
Utilities module for functional programming helpers.

Provides functional programming utilities and common patterns
used throughout the project.
"""

from .functional_helpers import (
    Result, safe_execute, filter_dict, map_dict, flatten, pluck,
    compose_safety, try_catch
)

__all__ = [
    "Result",
    "safe_execute",
    "filter_dict", 
    "map_dict",
    "flatten",
    "pluck",
    "compose_safety",
    "try_catch",
]
