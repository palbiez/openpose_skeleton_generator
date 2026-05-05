import os
from fastapi import FastAPI, HTTPException, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path
from pose_registry import get_registry
import json
import math
import uvicorn

app = FastAPI(title="PAL OpenPose Browser")
registry = get_registry()
print(f"[Server] Registry loaded with {len(registry.poses)} poses")

static_dir = Path(__file__).parent / "web" / "pose_browser"


@app.get("/api/poses")
def get_all_poses(page: int = Query(1, ge=1), limit: int = Query(50, ge=1, le=500)):
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
    print(f"[API] Filter request: pose={pose}, variant={variant}, subpose={subpose}, search={search}")
    print(f"[API] Registry has {len(registry.poses)} poses")
    
    # Use direct access instead of search method for debugging
    if pose is None and variant is None and subpose is None:
        matching_ids = [p["id"] for p in registry.poses]
    else:
        matching_ids = registry.search(pose=pose, variant=variant, subpose=subpose)
    
    print(f"[API] Found {len(matching_ids)} matching IDs")
    poses = []
    normalized_search = search.strip().lower() if isinstance(search, str) else None

    for pose_id in matching_ids:
        pose_data = registry.get_pose_by_id(pose_id)
        if not pose_data:
            continue

        if normalized_search:
            search_text = " ".join(
                [str(pose_data.get(k, "")).lower() for k in ["pose", "variant", "subpose"]]
            )
            if normalized_search not in str(pose_id).lower() and normalized_search not in search_text:
                continue

        pose_copy = {
            "id": pose_data["id"],
            "pose": pose_data["pose"],
            "gender": pose_data.get("gender"),
            "variant": pose_data.get("variant"),
            "subpose": pose_data.get("subpose"),
            "attributes": pose_data.get("attributes", []),
            "source_file": pose_data.get("source_file"),
            "image_url": f"/api/images/{pose_id}",
            "has_bone_structure": bool(pose_data.get("bone_structure_path")),
            "has_bone_structure_full": bool(pose_data.get("bone_structure_full_path")),
        }
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
def get_filter_options(pose: str = Query(None), variant: str = Query(None)):
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
    pose_data = registry.get_pose_by_id(pose_id)
    if not pose_data:
        raise HTTPException(status_code=404, detail="Pose not found")
    return {k: v for k, v in pose_data.items() if k != "keypoints"}


@app.get("/api/pose/{pose_id}/files")
def get_pose_files(pose_id: int):
    pose_data = registry.get_pose_by_id(pose_id)
    if not pose_data:
        raise HTTPException(status_code=404, detail="Pose not found")
    return {
        "display_image": pose_data.get("display_image"),
        "bone_structure": pose_data.get("bone_structure_path"),
        "bone_structure_full": pose_data.get("bone_structure_full_path"),
        "source_file": pose_data.get("source_file"),
        "attributes": pose_data.get("attributes", [])
    }


@app.get("/api/images/{pose_id}")
def get_pose_image(pose_id: int):
    pose_data = registry.get_pose_by_id(pose_id)
    if not pose_data:
        raise HTTPException(status_code=404, detail="Pose not found")

    image_path = pose_data.get("display_image") or pose_data.get("png_path")
    if not image_path:
        raise HTTPException(status_code=404, detail="Image not found")

    path = Path(image_path)
    if not path.exists():
        raise HTTPException(status_code=404, detail="Image file not found")

    return FileResponse(str(path), media_type="image/png")


@app.get("/")
def root():
    index_path = static_dir / "index.html"
    if index_path.exists():
        return FileResponse(str(index_path))
    return {"message": "PAL OpenPose Browser ready. Access http://localhost:8189"}


if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


if __name__ == "__main__":
    host = os.getenv("OPENPOSE_BROWSER_HOST", "0.0.0.0")
    port = int(os.getenv("OPENPOSE_BROWSER_PORT", "8189"))
    print(f"Starting PAL OpenPose Browser on http://{host}:{port}")
    print(f"Loaded {len(registry.list_all())} poses")
    uvicorn.run(app, host=host, port=port)
