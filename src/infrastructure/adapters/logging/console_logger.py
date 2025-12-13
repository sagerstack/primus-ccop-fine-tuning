"""
Console Logger

Simple console logging implementation.
"""

import logging
from typing import Any

from application.ports.output.i_logger import ILogger, LogLevel


class ConsoleLogger(ILogger):
    """Simple console logger using Python's logging module."""

    def __init__(self, log_level: str = "INFO") -> None:
        self._logger = logging.getLogger("ccop-eval")
        self._logger.setLevel(getattr(logging, log_level.upper()))

        if not self._logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self._logger.addHandler(handler)

    def debug(self, message: str, **kwargs: Any) -> None:
        self._logger.debug(self._format_message(message, kwargs))

    def info(self, message: str, **kwargs: Any) -> None:
        self._logger.info(self._format_message(message, kwargs))

    def warning(self, message: str, **kwargs: Any) -> None:
        self._logger.warning(self._format_message(message, kwargs))

    def error(self, message: str, **kwargs: Any) -> None:
        self._logger.error(self._format_message(message, kwargs))

    def critical(self, message: str, **kwargs: Any) -> None:
        self._logger.critical(self._format_message(message, kwargs))

    def log(self, level: LogLevel, message: str, **kwargs: Any) -> None:
        getattr(self, level.value)(message, **kwargs)

    def bind(self, **kwargs: Any) -> "ILogger":
        return self  # Simple implementation doesn't support binding

    def _format_message(self, message: str, kwargs: dict) -> str:
        if kwargs:
            extras = " ".join(f"{k}={v}" for k, v in kwargs.items())
            return f"{message} [{extras}]"
        return message
