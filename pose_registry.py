"""Compatibility import for the relocated core.pose_registry module."""

try:
    from .core.pose_registry import *  # noqa: F401,F403
except ImportError:
    from core.pose_registry import *  # noqa: F401,F403

