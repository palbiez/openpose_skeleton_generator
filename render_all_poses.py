"""
Render all poses as PNG thumbnails for the web browser.
Run once to generate all skeleton images.
"""

import cv2
import numpy as np
from pathlib import Path
from pose_registry import get_registry
import os


def draw_skeleton_wireframe(canvas, keypoints, skeleton):
    """Draw skeleton as wireframe (points and lines only)."""
    height, width = canvas.shape[:2]
    
    # Draw points
    for i in range(0, len(keypoints), 3):
        x, y, v = keypoints[i], keypoints[i+1], keypoints[i+2]
        if v > 0:
            x, y = int(x), int(y)
            if 0 <= x < width and 0 <= y < height:
                cv2.circle(canvas, (x, y), 5, (255, 255, 255), -1)
    
    # Draw bones
    for a, b in skeleton:
        xa, ya, va = keypoints[a*3], keypoints[a*3+1], keypoints[a*3+2]
        xb, yb, vb = keypoints[b*3], keypoints[b*3+1], keypoints[b*3+2]
        
        if va > 0 and vb > 0:
            xa, ya = int(xa), int(ya)
            xb, yb = int(xb), int(yb)
            
            if (0 <= xa < width and 0 <= ya < height and 
                0 <= xb < width and 0 <= yb < height):
                cv2.line(canvas, (xa, ya), (xb, yb), (255, 255, 255), 2)


def place_person_at(keypoints, center_x, center_y, width, height):
    """Center person at given position."""
    # Reference: hip
    hip_x = (keypoints[11*3] + keypoints[12*3]) / 2
    hip_y = (keypoints[11*3+1] + keypoints[12*3+1]) / 2
    
    dx = center_x - hip_x
    dy = center_y - hip_y
    
    new_kp = keypoints.copy()
    
    for i in range(0, len(new_kp), 3):
        x = new_kp[i]
        y = new_kp[i+1]
        v = new_kp[i+2]
        
        if v > 0:
            x += dx
            y += dy
            
            # Clamp to canvas
            x = max(0, min(width-1, x))
            y = max(0, min(height-1, y))
            
            new_kp[i] = x
            new_kp[i+1] = y
    
    return new_kp


def render_pose(pose_id, keypoints, width=256, height=256):
    """Render a single pose as image."""
    
    skeleton = [
        (5, 7), (7, 9),     # left arm
        (6, 8), (8, 10),    # right arm
        (5, 6),             # shoulders
        (5, 11), (6, 12),   # torso
        (11, 12),
        (11, 13), (13, 15), # left leg
        (12, 14), (14, 16)  # right leg
    ]
    
    canvas = np.zeros((height, width, 3), dtype=np.uint8)
    
    # Place person in center
    center_x = width / 2
    center_y = height / 2
    keypoints = place_person_at(keypoints, center_x, center_y, width, height)
    
    # Draw
    draw_skeleton_wireframe(canvas, keypoints, skeleton)
    
    return canvas


def render_all_poses():
    """Render all poses and save as PNG thumbnails."""
    
    registry = get_registry()
    
    # Create thumbnail directory
    thumb_dir = Path(__file__).parent / "web" / "pose_thumbnails"
    thumb_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"[RenderPoses] Saving thumbnails to: {thumb_dir}")
    
    count = 0
    failed = 0
    
    for pose_data in registry.list_all():
        pose_id = pose_data["id"]
        keypoints = registry.get_keypoints_by_id(pose_id)
        
        if not keypoints:
            print(f"[RenderPoses] Skipping {pose_id}: no keypoints")
            failed += 1
            continue
        
        try:
            # Render at 256x256 for thumbnails
            img = render_pose(pose_id, keypoints, width=256, height=256)
            
            # Save
            thumb_path = thumb_dir / f"pose_{pose_id}.png"
            cv2.imwrite(str(thumb_path), img)
            
            count += 1
            if count % 50 == 0:
                print(f"[RenderPoses] Rendered {count} poses...")
        
        except Exception as e:
            print(f"[RenderPoses] Error rendering {pose_id}: {e}")
            failed += 1
    
    print(f"\n[RenderPoses] ✅ Complete!")
    print(f"[RenderPoses]   Rendered: {count}")
    print(f"[RenderPoses]   Failed: {failed}")
    print(f"[RenderPoses]   Path: {thumb_dir}")


if __name__ == "__main__":
    render_all_poses()
