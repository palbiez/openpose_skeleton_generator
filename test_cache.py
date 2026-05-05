#!/usr/bin/env python3
"""
Quick test of pose registry cache functionality.
"""

import sys
import os
from pathlib import Path

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

from pose_registry import PoseRegistry

def test_cache():
    print("Testing pose registry cache...")
    
    # Create registry instance
    registry = PoseRegistry()
    
    print(f"Registry has {len(registry.poses)} poses")
    
    # Check if cache file exists
    cache_file = Path(__file__).parent / "pose_registry_cache.json"
    if cache_file.exists():
        print(f"Cache file exists: {cache_file}")
        print(f"Cache file size: {cache_file.stat().st_size} bytes")
    else:
        print("No cache file found")

if __name__ == "__main__":
    test_cache()