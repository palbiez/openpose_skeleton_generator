#!/usr/bin/env python3

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from pose_selector_node import get_pose_options

if __name__ == "__main__":
    opts = get_pose_options()
    print("Available variants:", opts['variants'])
    print("Available poses:", opts['poses'])
    print("Available subposes:", opts['subposes'])