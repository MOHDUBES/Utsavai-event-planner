"""
Application configuration for UtsavAI.
Exposes settings loaded via pydantic-settings.
"""

from __future__ import annotations

from backend.utils.config import Settings, get_settings

__all__ = ["Settings", "get_settings"]
