"""Compatibility import for the relocated nodes.pose_matcher_node module."""

try:
    from .nodes.pose_matcher_node import *  # noqa: F401,F403
except ImportError:
    from nodes.pose_matcher_node import *  # noqa: F401,F403

