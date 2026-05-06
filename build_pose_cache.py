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
    
    cache_file = Path(__file__).parent / "pose_registry_cache.json"
    temp_cache = cache_file.with_suffix('.tmp')

    if temp_cache.exists():
        print(f"Found stale temp cache file, removing: {temp_cache}")
        temp_cache.unlink()

    if cache_file.exists():
        cache_file.rename(temp_cache)
        print("Temporarily moved existing cache for fresh scan")

    success = False
    try:
        # Create a temporary registry instance to scan poses
        registry = PoseRegistry.__new__(PoseRegistry)
        registry._initialized = False
        registry.poses = []
        registry.poses_by_id = {}
        registry.index_by_filter = {}

        # Initialize and load poses (this will scan all PNG files and save cache)
        registry.__init__()
        success = True

        print(f"Cache building completed for {len(registry.poses)} poses")
    finally:
        if temp_cache.exists():
            if success:
                temp_cache.unlink()
                print("Removed backup of previous cache")
            else:
                if cache_file.exists():
                    cache_file.unlink()
                temp_cache.rename(cache_file)
                print("Restored original cache after failed build")

if __name__ == "__main__":
    main()