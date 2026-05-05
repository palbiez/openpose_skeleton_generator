#!/usr/bin/env python3
"""
Pre-build pose registry cache for faster ComfyUI startup.

Usage:
    python build_pose_cache.py          # Build/update cache
    python build_pose_cache.py --clean  # Remove cache file
"""

import argparse
import json
import os
import sys
from pathlib import Path

# Add current directory to path so we can import pose_registry
sys.path.insert(0, os.path.dirname(__file__))

from pose_registry import PoseRegistry

def clean_cache():
    """Remove the cache file."""
    cache_file = Path(__file__).parent / "pose_registry_cache.json"
    if cache_file.exists():
        cache_file.unlink()
        print(f"Removed cache file: {cache_file}")
    else:
        print("No cache file found")

def build_cache():
    """Build the pose registry cache."""
    print("Building pose registry cache...")
    
    # Force fresh scan by temporarily renaming cache file
    cache_file = Path(__file__).parent / "pose_registry_cache.json"
    temp_cache = None
    if cache_file.exists():
        temp_cache = cache_file.with_suffix('.tmp')
        cache_file.rename(temp_cache)
        print("Temporarily moved existing cache for fresh scan")

    try:
        # Create a temporary registry instance to scan poses
        registry = PoseRegistry.__new__(PoseRegistry)
        registry._initialized = False
        registry.poses = []
        registry.poses_by_id = {}
        registry.index_by_filter = {}

        # Initialize and load poses (this will scan all PNG files and save cache)
        registry.__init__()

        print(f"Cache building completed for {len(registry.poses)} poses")
        
    finally:
        # Restore original cache if it existed
        if temp_cache and temp_cache.exists():
            temp_cache.rename(cache_file)
            print("Restored original cache")

def main():
    parser = argparse.ArgumentParser(description="Build pose registry cache")
    parser.add_argument('--clean', action='store_true', help='Remove cache file instead of building')
    
    args = parser.parse_args()
    
    if args.clean:
        clean_cache()
    else:
        build_cache()

if __name__ == "__main__":
    main()