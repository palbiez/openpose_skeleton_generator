#!/usr/bin/env python3
"""Build or clean the OpenPose Manager registry cache."""

import argparse
import sys
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
if str(PLUGIN_ROOT) not in sys.path:
    sys.path.insert(0, str(PLUGIN_ROOT))

from core.pose_registry import CACHE_FILE, PoseRegistry


def clean_cache() -> None:
    if CACHE_FILE.exists():
        CACHE_FILE.unlink()
        print(f"Removed cache file: {CACHE_FILE}")
    else:
        print("No cache file found")


def build_cache() -> None:
    print("Building pose registry cache...")
    temp_cache = CACHE_FILE.with_suffix(".tmp")

    if temp_cache.exists():
        print(f"Found stale temp cache file, removing: {temp_cache}")
        temp_cache.unlink()

    if CACHE_FILE.exists():
        CACHE_FILE.rename(temp_cache)
        print("Temporarily moved existing cache for fresh scan")

    success = False
    try:
        PoseRegistry._instance = None
        registry = PoseRegistry()
        success = True
        print(f"Cache building completed for {len(registry.poses)} poses")
    finally:
        if temp_cache.exists():
            if success:
                temp_cache.unlink()
                print("Removed backup of previous cache")
            else:
                if CACHE_FILE.exists():
                    CACHE_FILE.unlink()
                temp_cache.rename(CACHE_FILE)
                print("Restored original cache after failed build")


def main() -> int:
    parser = argparse.ArgumentParser(description="Build or clean the OpenPose Manager registry cache.")
    parser.add_argument("--clean", action="store_true", help="Remove the cache instead of rebuilding it.")
    args = parser.parse_args()

    if args.clean:
        clean_cache()
    else:
        build_cache()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
