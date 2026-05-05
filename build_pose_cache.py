#!/usr/bin/env python3
"""
Pre-build pose registry cache for faster ComfyUI startup.

This script scans the OpenPose directory and creates a cached registry file
that can be loaded quickly by the pose browser.
"""

import json
import os
import sys
from pathlib import Path

# Add current directory to path so we can import pose_registry
sys.path.insert(0, os.path.dirname(__file__))

from pose_registry import PoseRegistry

def main():
    print("Building pose registry cache...")

    # Create a temporary registry instance to scan poses
    registry = PoseRegistry.__new__(PoseRegistry)
    registry._initialized = False
    registry.poses = []
    registry.poses_by_id = {}
    registry.index_by_filter = {}

    # Initialize and load poses
    registry.__init__()

    # Save to cache file
    cache_file = Path(__file__).parent / "pose_registry_cache.json"

    # Convert poses to serializable format (remove Path objects)
    serializable_poses = []
    for pose in registry.poses:
        pose_copy = pose.copy()
        # Convert any Path objects to strings
        for key, value in pose_copy.items():
            if isinstance(value, Path):
                pose_copy[key] = str(value)
        serializable_poses.append(pose_copy)

    cache_data = {
        "poses": serializable_poses,
        "poses_by_id": registry.poses_by_id,
        "index_by_filter": registry.index_by_filter,
        "total_poses": len(registry.poses)
    }

    with open(cache_file, 'w', encoding='utf-8') as f:
        json.dump(cache_data, f, indent=2, ensure_ascii=False)

    print(f"Cache saved to {cache_file}")
    print(f"Cached {len(registry.poses)} poses")

if __name__ == "__main__":
    main()