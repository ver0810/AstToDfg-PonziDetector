"""
Functional programming utilities for the project.
Provides pure functions and common functional patterns.
"""

from functools import wraps, partial
from typing import Any, Callable, List, Dict, TypeVar, Union, Optional
from toolz import curry, pipe, compose
import json

T = TypeVar('T')
R = TypeVar('R')


def safe_execute(func: Callable[..., T], default: T) -> Callable[..., T]:
    """
    Safely execute a function, returning default value if exception occurs.
    
    Args:
        func: Function to execute
        default: Default value to return on exception
        
    Returns:
        Wrapped function that returns default on exception
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception:
            return default
    return wrapper


@curry
def filter_dict(predicate: Callable[[str, Any], bool], data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Filter dictionary items based on predicate.
    
    Args:
        predicate: Function that takes key and value, returns boolean
        data: Dictionary to filter
        
    Returns:
        Filtered dictionary
    """
    return {k: v for k, v in data.items() if predicate(k, v)}


@curry
def map_dict(transformer: Callable[[Any], Any], data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Transform dictionary values.
    
    Args:
        transformer: Function to transform values
        data: Dictionary to transform
        
    Returns:
        Dictionary with transformed values
    """
    return {k: transformer(v) for k, v in data.items()}


def flatten(nested_list: List[List[T]]) -> List[T]:
    """
    Flatten a nested list one level deep.
    
    Args:
        nested_list: List of lists to flatten
        
    Returns:
        Flattened list
    """
    return [item for sublist in nested_list for item in sublist]


@curry
def pluck(key: str, list_of_dicts: List[Dict[str, Any]]) -> List[Any]:
    """
    Extract a specific key from a list of dictionaries.
    
    Args:
        key: Key to extract
        list_of_dicts: List of dictionaries
        
    Returns:
        List of values for the specified key
    """
    return [d.get(key) for d in list_of_dicts if key in d]


def compose_safety(*functions):
    """
    Compose functions with safety checks.
    If any function returns None, the chain stops and returns None.
    """
    def composed(x):
        result = x
        for func in functions:
            if result is None:
                return None
            result = func(result)
        return result
    return composed


class Result:
    """
    Result type for functional error handling.
    Either contains a success value or an error.
    """
    
    def __init__(self, value: Any, is_success: bool = True, error: Optional[str] = None):
        self._value = value
        self._is_success = is_success
        self._error = error
    
    @property
    def is_success(self) -> bool:
        return self._is_success
    
    @property
    def is_failure(self) -> bool:
        return not self._is_success
    
    @property
    def value(self) -> Any:
        if self.is_failure:
            raise ValueError("Cannot get value from failed Result")
        return self._value
    
    @property
    def error(self) -> Optional[str]:
        return self._error
    
    @classmethod
    def success(cls, value: Any) -> 'Result':
        return cls(value, True, None)
    
    @classmethod
    def failure(cls, error: str) -> 'Result':
        return cls(None, False, error)
    
    def map(self, func: Callable[[Any], Any]) -> 'Result':
        """Map function over success value."""
        if self.is_failure:
            return self
        try:
            return Result.success(func(self._value))
        except Exception as e:
            return Result.failure(str(e))
    
    def flat_map(self, func: Callable[[Any], 'Result']) -> 'Result':
        """Flat map function that returns Result."""
        if self.is_failure:
            return self
        try:
            return func(self._value)
        except Exception as e:
            return Result.failure(str(e))
    
    def or_else(self, default: Any) -> Any:
        """Get value or return default on failure."""
        return self._value if self.is_success else default
    
    def __repr__(self) -> str:
        if self.is_success:
            return f"Result.success({self._value})"
        return f"Result.failure({self._error})"


def try_catch(func: Callable[..., T]) -> Callable[..., Result]:
    """
    Convert a function that might raise exceptions to return Result.
    
    Args:
        func: Function to wrap
        
    Returns:
        Function that returns Result instead of raising exceptions
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return Result.success(func(*args, **kwargs))
        except Exception as e:
            return Result.failure(str(e))
    return wrapper
