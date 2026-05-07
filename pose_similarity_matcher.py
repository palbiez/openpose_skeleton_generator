"""Compatibility import for the relocated core.pose_similarity_matcher module."""

try:
    from .core.pose_similarity_matcher import *  # noqa: F401,F403
except ImportError:
    from core.pose_similarity_matcher import *  # noqa: F401,F403

