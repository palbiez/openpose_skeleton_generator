#!/usr/bin/env python3
"""Test script for the updated pose registry."""

from pose_registry import get_registry

def main():
    print("Testing Pose Registry...")
    r = get_registry()
    print(f"Loaded {len(r.poses)} poses")

    if r.poses:
        print("First pose:", r.poses[0])
        print("Available poses:", r.get_all_poses()[:5])  # First 5
    else:
        print("No poses loaded!")

if __name__ == "__main__":
    main()