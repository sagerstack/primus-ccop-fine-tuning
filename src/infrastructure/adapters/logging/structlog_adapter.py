"""
Structlog Adapter

Structured logging implementation using structlog.
"""

from pathlib import Path
from typing import Any, Optional

import structlog
from application.ports.output.i_logger import ILogger, LogLevel


class StructlogAdapter(ILogger):
    """Structured logger using structlog."""

    def __init__(
        self,
        log_level: str = "INFO",
        log_file: Optional[Path] = None,
    ) -> None:
        structlog.configure(
            processors=[
                structlog.processors.TimeStamper(fmt="iso"),
                structlog.processors.add_log_level,
                structlog.processors.JSONRenderer(),
            ],
            logger_factory=structlog.PrintLoggerFactory(),
        )
        self._logger = structlog.get_logger()
        self._log_level = log_level.upper()

    def debug(self, message: str, **kwargs: Any) -> None:
        self._logger.debug(message, **kwargs)

    def info(self, message: str, **kwargs: Any) -> None:
        self._logger.info(message, **kwargs)

    def warning(self, message: str, **kwargs: Any) -> None:
        self._logger.warning(message, **kwargs)

    def error(self, message: str, **kwargs: Any) -> None:
        self._logger.error(message, **kwargs)

    def critical(self, message: str, **kwargs: Any) -> None:
        self._logger.critical(message, **kwargs)

    def log(self, level: LogLevel, message: str, **kwargs: Any) -> None:
        getattr(self, level.value)(message, **kwargs)

    def bind(self, **kwargs: Any) -> "ILogger":
        """Create logger with bound context."""
        bound = StructlogAdapter(self._log_level)
        bound._logger = self._logger.bind(**kwargs)
        return bound
