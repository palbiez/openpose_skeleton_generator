"""Compatibility import for the relocated nodes.pose_renderer_node module."""

try:
    from .nodes.pose_renderer_node import *  # noqa: F401,F403
except ImportError:
    from nodes.pose_renderer_node import *  # noqa: F401,F403

