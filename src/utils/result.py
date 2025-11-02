"""
Result type for functional error handling.
Provides a safer alternative to exceptions for predictable error cases.
"""

from typing import TypeVar, Generic, Callable, Union, Any, Optional
from dataclasses import dataclass

T = TypeVar('T')
E = TypeVar('E')


@dataclass
class Result(Generic[T]):
    """
    Result type that can be either Success or Failure.
    
    Usage:
        result = Result.success(42)
        if result.is_success:
            print(result.value)  # 42
        
        result = Result.failure("Something went wrong")
        if result.is_failure:
            print(result.error)  # "Something went wrong"
    """
    
    _value: Optional[T] = None
    _error: Optional[str] = None
    _is_success: bool = True
    
    @staticmethod
    def success(value: T) -> 'Result[T]':
        """Create a successful result."""
        return Result(_value=value, _is_success=True)
    
    @staticmethod
    def failure(error: str) -> 'Result[T]':
        """Create a failed result."""
        return Result(_error=error, _is_success=False)
    
    @property
    def is_success(self) -> bool:
        """Check if result is successful."""
        return self._is_success
    
    @property
    def is_failure(self) -> bool:
        """Check if result is a failure."""
        return not self._is_success
    
    @property
    def value(self) -> T:
        """Get the value (raises if failure)."""
        if not self._is_success:
            raise ValueError(f"Cannot get value from failure: {self._error}")
        return self._value
    
    @property
    def error(self) -> str:
        """Get the error message (raises if success)."""
        if self._is_success:
            raise ValueError("Cannot get error from success")
        return self._error
    
    def map(self, fn: Callable[[T], Any]) -> 'Result':
        """Map the value if successful."""
        if self.is_failure:
            return self
        try:
            return Result.success(fn(self.value))
        except Exception as e:
            return Result.failure(str(e))
    
    def flat_map(self, fn: Callable[[T], 'Result']) -> 'Result':
        """Flat map the value if successful."""
        if self.is_failure:
            return self
        try:
            return fn(self.value)
        except Exception as e:
            return Result.failure(str(e))
    
    def unwrap_or(self, default: T) -> T:
        """Get value or default if failure."""
        return self.value if self.is_success else default
    
    def unwrap_or_else(self, fn: Callable[[str], T]) -> T:
        """Get value or call function with error if failure."""
        return self.value if self.is_success else fn(self.error)
    
    def __repr__(self) -> str:
        if self.is_success:
            return f"Result.success({self.value!r})"
        else:
            return f"Result.failure({self.error!r})"
