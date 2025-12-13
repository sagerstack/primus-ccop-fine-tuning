"""
Infrastructure Layer

Contains adapters, external clients, and configuration.
Implements ports defined in the application layer.
"""

from infrastructure.config.container import Container, get_container
from infrastructure.config.settings import Settings, get_settings

__all__ = [
    "Settings",
    "get_settings",
    "Container",
    "get_container",
]
