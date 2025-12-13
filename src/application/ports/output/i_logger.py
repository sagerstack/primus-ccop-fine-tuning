"""
Logger Port (Interface)

Abstract interface for logging operations.
"""

from abc import ABC, abstractmethod
from enum import Enum
from typing import Any, Dict, Optional


class LogLevel(str, Enum):
    """Log levels."""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class ILogger(ABC):
    """
    Port (interface) for logging operations.

    This abstraction allows swapping logging implementations
    (console, file, structured logging, etc.).
    """

    @abstractmethod
    def debug(self, message: str, **kwargs: Any) -> None:
        """Log debug message."""
        pass

    @abstractmethod
    def info(self, message: str, **kwargs: Any) -> None:
        """Log info message."""
        pass

    @abstractmethod
    def warning(self, message: str, **kwargs: Any) -> None:
        """Log warning message."""
        pass

    @abstractmethod
    def error(self, message: str, **kwargs: Any) -> None:
        """Log error message."""
        pass

    @abstractmethod
    def critical(self, message: str, **kwargs: Any) -> None:
        """Log critical message."""
        pass

    @abstractmethod
    def log(self, level: LogLevel, message: str, **kwargs: Any) -> None:
        """Log message at specific level."""
        pass

    @abstractmethod
    def bind(self, **kwargs: Any) -> "ILogger":
        """
        Create a logger with bound context.

        Args:
            **kwargs: Context to bind

        Returns:
            Logger with bound context

        Example:
            logger = logger.bind(request_id="123", user_id="456")
            logger.info("Request processed")  # Includes request_id and user_id
        """
        pass
