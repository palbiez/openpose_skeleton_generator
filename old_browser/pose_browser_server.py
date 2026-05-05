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
import math
import uvicorn

app = FastAPI(title="PAL Pose Browser")
registry = get_registry()

# Static files
static_dir = Path(__file__).parent / "web" / "pose_browser"
thumbnails_dir = Path(__file__).parent / "web" / "pose_thumbnails"


@app.get("/api/poses")
def get_all_poses(
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=500)
):
    """Get all available poses with metadata and pagination."""
    poses = registry.list_all()
    total = len(poses)
    start = (page - 1) * limit
    end = start + limit
    return {
        "total": total,
        "page": page,
        "limit": limit,
        "poses": poses[start:end]
    }


@app.get("/api/filter")
def filter_poses(
    pose: str = Query(None),
    variant: str = Query(None),
    subpose: str = Query(None),
    search: str = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=500)
):
    """Filter poses by criteria."""
    matching_ids = registry.search(pose=pose, variant=variant, subpose=subpose)
    
    poses = []
    normalized_search = search.strip().lower() if isinstance(search, str) else None
    for pose_id in matching_ids:
        pose_data = registry.get_pose_by_id(pose_id)
        if not pose_data:
            continue

        if normalized_search:
            id_match = normalized_search in str(pose_id)
            text_match = (
                normalized_search in pose_data["pose"].lower() or
                normalized_search in pose_data["variant"].lower() or
                normalized_search in pose_data["subpose"].lower()
            )
            if not (id_match or text_match):
                continue

        # Remove keypoints from response (too large)
        pose_copy = {k: v for k, v in pose_data.items() if k != "keypoints"}
        poses.append(pose_copy)
    
    total = len(poses)
    total_pages = math.ceil(total / limit) if total else 0
    start = (page - 1) * limit
    end = start + limit
    return {
        "count": total,
        "page": page,
        "limit": limit,
        "total_pages": total_pages,
        "poses": poses[start:end]
    }


@app.get("/api/options")
def get_filter_options(
    pose: str = Query(None),
    variant: str = Query(None)
):
    """Get available filter options."""
    
    all_poses = registry.get_all_poses()
    
    variants = []
    subposes = []
    if pose:
        variants = registry.get_available_variants(pose)
        if variant and variant in variants:
            subposes = registry.get_available_subposes(pose, variant)
        elif variants:
            subposes = registry.get_available_subposes(pose, variants[0])
    
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
