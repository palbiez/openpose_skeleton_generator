"""
Pose Browser Server - FastAPI web server for pose browsing and selection.
Run: python pose_browser_server.py
Access: http://localhost:8189
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pathlib import Path
from pose_registry import get_registry
import json
import uvicorn

app = FastAPI(title="PAL Pose Browser")
registry = get_registry()

# Static files
static_dir = Path(__file__).parent / "web" / "pose_browser"
thumbnails_dir = Path(__file__).parent / "web" / "pose_thumbnails"


@app.get("/api/poses")
def get_all_poses():
    """Get all available poses with metadata."""
    poses = registry.list_all()
    return {
        "total": len(poses),
        "poses": poses
    }


@app.get("/api/filter")
def filter_poses(
    pose: str = Query(None),
    variant: str = Query(None),
    subpose: str = Query(None)
):
    """Filter poses by criteria."""
    matching_ids = registry.search(pose=pose, variant=variant, subpose=subpose)
    
    poses = []
    for pose_id in matching_ids:
        pose_data = registry.get_pose_by_id(pose_id)
        if pose_data:
            # Remove keypoints from response (too large)
            pose_copy = {k: v for k, v in pose_data.items() if k != "keypoints"}
            poses.append(pose_copy)
    
    return {
        "count": len(poses),
        "poses": poses
    }


@app.get("/api/options")
def get_filter_options(pose: str = Query(None)):
    """Get available filter options."""
    
    all_poses = registry.get_all_poses()
    
    if pose:
        # Get variants and subposes for this pose
        variants = registry.get_available_variants(pose)
        subposes = registry.get_available_subposes(pose, variants[0]) if variants else []
    else:
        variants = []
        subposes = []
    
    return {
        "poses": all_poses,
        "variants": variants,
        "subposes": subposes
    }


@app.get("/api/pose/{pose_id}")
def get_pose(pose_id: int):
    """Get pose details by ID."""
    pose = registry.get_pose_by_id(pose_id)
    
    if not pose:
        raise HTTPException(status_code=404, detail="Pose not found")
    
    # Remove keypoints (too large)
    return {k: v for k, v in pose.items() if k != "keypoints"}


@app.get("/thumbnails/{pose_id}")
def get_thumbnail(pose_id: int):
    """Get pose thumbnail image."""
    thumb_path = thumbnails_dir / f"pose_{pose_id}.png"
    
    if not thumb_path.exists():
        raise HTTPException(status_code=404, detail="Thumbnail not found")
    
    return FileResponse(str(thumb_path), media_type="image/png")


@app.get("/")
def root():
    """Serve main HTML."""
    index_path = static_dir / "index.html"
    if index_path.exists():
        return FileResponse(str(index_path))
    return {"message": "PAL Pose Browser ready. Access http://localhost:8189"}


# Mount static files
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


if __name__ == "__main__":
    print("Starting PAL Pose Browser on http://localhost:8189")
    print(f"Loaded {len(registry.list_all())} poses")
    uvicorn.run(app, host="127.0.0.1", port=8189)
