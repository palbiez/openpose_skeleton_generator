#!/usr/bin/env python3
"""
Quick start script for PAL Pose Browser
Run this to set up and start the pose browser
"""

import subprocess
import sys
import os
from pathlib import Path


def run_command(cmd, description):
    """Run a command and handle errors."""
    print(f"\n[*] {description}...")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode != 0:
            print(f"[!] Error: {result.stderr}")
            return False
        return True
    except Exception as e:
        print(f"[!] Exception: {e}")
        return False


def main():
    print("""
    ========================================
    PAL Pose Browser - Setup & Start
    ========================================
    """)
    
    # Get current directory
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    
    # Step 1: Install dependencies
    print("[1/3] Installing dependencies...")
    if sys.platform == "win32":
        cmd = f"{sys.executable} -m pip install fastapi uvicorn -q"
    else:
        cmd = f"{sys.executable} -m pip install fastapi uvicorn -q"
    
    result = subprocess.run(cmd, shell=True)
    if result.returncode != 0:
        print("[!] ERROR: Failed to install dependencies")
        sys.exit(1)
    
    # Step 2: Generate thumbnails
    print("\n[2/3] Generating pose thumbnails...")
    print("      (This may take 1-2 minutes on first run)")
    
    cmd = f"{sys.executable} render_all_poses.py"
    result = subprocess.run(cmd, shell=True)
    if result.returncode != 0:
        print("[!] WARNING: Thumbnail generation had issues")
    
    # Step 3: Start server
    print("\n[3/3] Starting Pose Browser server...")
    print("""
    ========================================
    Opening: http://localhost:8189
    ========================================
    
    Press CTRL+C to stop the server
    """)
    
    cmd = f"{sys.executable} pose_browser_server.py"
    subprocess.run(cmd, shell=True)


if __name__ == "__main__":
    main()
