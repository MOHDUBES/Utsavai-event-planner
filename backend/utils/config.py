"""
Backward-compatibility alias pointing to canonical backend.config.
"""

from __future__ import annotations

from backend.config import Settings, get_settings

__all__ = ["Settings", "get_settings"]
