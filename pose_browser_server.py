import os
from fastapi import FastAPI, HTTPException, Query
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path
try:
    from .core.pose_registry import get_registry, debug_log
except ImportError:
    from core.pose_registry import get_registry, debug_log
import json
import math
import uvicorn

app = FastAPI(title="PAL OpenPose Browser")
debug_log("[DEBUG] pose_browser_server: Starting server initialization")
registry = get_registry()
debug_log(f"[DEBUG] pose_browser_server: Registry loaded with {len(registry.poses)} poses")
debug_log(f"[DEBUG] pose_browser_server: First pose sample: {registry.poses[0] if registry.poses else 'No poses'}")

static_dir = Path(__file__).parent / "web" / "pose_browser"


def _resolve_image_path(pose_data: dict, image_kind: str = "preview") -> str:
    if image_kind in {"bone", "bone_structure"}:
        return pose_data.get("bone_structure_path") or pose_data.get("bone_structure_full_path") or ""
    if image_kind == "bone_structure_full":
        return pose_data.get("bone_structure_full_path") or pose_data.get("bone_structure_path") or ""
    return (
        pose_data.get("display_image")
        or pose_data.get("bone_structure_path")
        or pose_data.get("bone_structure_full_path")
        or pose_data.get("png_path")
        or ""
    )


@app.get("/api/poses")
def get_all_poses(page: int = Query(1, ge=1), limit: int = Query(50, ge=1, le=500)):
    debug_log(f"[DEBUG] /api/poses: Called with page={page}, limit={limit}")
    poses = registry.list_all()
    debug_log(f"[DEBUG] /api/poses: registry.list_all() returned {len(poses)} poses")
    total = len(poses)
    start = (page - 1) * limit
    end = start + limit
    result = {
        "total": total,
        "page": page,
        "limit": limit,
        "poses": poses[start:end]
    }
    debug_log(f"[DEBUG] /api/poses: Returning {len(result['poses'])} poses for page {page}")
    return result


@app.get("/api/filter")
def filter_poses(
    pose: str = Query(None),
    gender: str = Query(None),
    variant: str = Query(None),
    subpose: str = Query(None),
    search: str = Query(None),
    page: int = Query(1, ge=1),
    limit: int = Query(50, ge=1, le=500)
):
    debug_log(f"[DEBUG] /api/filter: Called with pose={pose}, gender={gender}, variant={variant}, subpose={subpose}, search={search}, page={page}, limit={limit}")
    debug_log(f"[DEBUG] /api/filter: Registry has {len(registry.poses)} poses")
    
    if pose is None and gender is None and variant is None and subpose is None:
        debug_log("[DEBUG] /api/filter: No filters specified, using all poses")
        matching_ids = [p["id"] for p in registry.poses]
    else:
        debug_log(f"[DEBUG] /api/filter: Using registry.search with pose={pose}, gender={gender}, variant={variant}, subpose={subpose}")
        matching_ids = registry.search(pose=pose, gender=gender, variant=variant, subpose=subpose)
    
    debug_log(f"[DEBUG] /api/filter: Found {len(matching_ids)} matching IDs")
    poses = []
    normalized_search = search.strip().lower() if isinstance(search, str) else None

    for pose_id in matching_ids:
        pose_data = registry.get_pose_by_id(pose_id)
        if not pose_data:
            debug_log(f"[DEBUG] /api/filter: Pose ID {pose_id} not found in registry")
            continue

        if normalized_search:
            search_text = " ".join(
                [str(pose_data.get(k, "")).lower() for k in ["pose", "gender", "variant", "subpose", "base_name", "source_file"]]
                + [str(attr).lower() for attr in pose_data.get("attributes", [])]
            )
            if normalized_search not in str(pose_id).lower() and normalized_search not in search_text:
                continue

        image_path = _resolve_image_path(pose_data, "preview")
        bone_image_path = _resolve_image_path(pose_data, "bone_structure")

        pose_copy = {
            "id": pose_data["id"],
            "pose": pose_data["pose"],
            "gender": pose_data.get("gender"),
            "variant": pose_data.get("variant"),
            "subpose": pose_data.get("subpose"),
            "base_name": pose_data.get("base_name"),
            "attributes": pose_data.get("attributes", []),
            "source_file": pose_data.get("source_file"),
            "image_url": f"/api/images/{pose_id}" if image_path else None,
            "hover_image_url": f"/api/images/{pose_id}/bone_structure" if bone_image_path else None,
            "copy_json_url": f"/api/pose/{pose_id}/copy" if pose_data.get("json_path") else None,
            "has_preview": bool(image_path),
            "has_bone_structure": bool(pose_data.get("bone_structure_path")),
            "has_bone_structure_full": bool(pose_data.get("bone_structure_full_path")),
            "has_json": bool(pose_data.get("json_path")),
        }
        poses.append(pose_copy)

    total = len(poses)
    total_pages = math.ceil(total / limit) if total else 0
    start = (page - 1) * limit
    end = start + limit
    result = {
        "count": total,
        "page": page,
        "limit": limit,
        "total_pages": total_pages,
        "poses": poses[start:end]
    }
    debug_log(f"[DEBUG] /api/filter: Returning result with count={result['count']}, poses_in_page={len(result['poses'])}")
    return result


@app.get("/api/options")
def get_filter_options(
    pose: str = Query(None),
    gender: str = Query(None),
    variant: str = Query(None),
):
    all_poses = registry.get_all_poses()
    genders = registry.get_available_genders(pose) if pose else registry.get_available_genders()
    variants = []
    subposes = []
    if pose:
        variants = registry.get_available_variants(pose, gender=gender)
        if variant and variant in variants:
            subposes = registry.get_available_subposes(pose, variant, gender=gender)
        elif variants:
            subposes = registry.get_available_subposes(pose, variants[0], gender=gender)
    return {
        "poses": all_poses,
        "genders": genders,
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
        "json_path": pose_data.get("json_path"),
        "source_file": pose_data.get("source_file"),
        "attributes": pose_data.get("attributes", [])
    }


@app.get("/api/pose/{pose_id}/copy")
def get_pose_copy_json(pose_id: int):
    text = registry.get_pose_json_text_by_id(pose_id)
    if text is None:
        raise HTTPException(status_code=404, detail="Pose JSON not found")

    pose_data = registry.get_pose_by_id(pose_id) or {}
    return {
        "id": pose_id,
        "source": pose_data.get("json_path") or "generated_keypoints",
        "text": text,
    }


@app.get("/api/images/{pose_id}")
def get_pose_image(pose_id: int):
    return get_pose_image_by_kind(pose_id, "preview")


@app.get("/api/images/{pose_id}/{image_kind}")
def get_pose_image_by_kind(pose_id: int, image_kind: str):
    pose_data = registry.get_pose_by_id(pose_id)
    if not pose_data:
        raise HTTPException(status_code=404, detail="Pose not found")

    image_path = _resolve_image_path(pose_data, image_kind)
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
    return {"message": "PAL OpenPose Browser ready. Access http://127.0.0.1:8189 or ComfyUI /poses when route integration is available."}


if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


if __name__ == "__main__":
    host = os.getenv("OPENPOSE_BROWSER_HOST", "0.0.0.0")
    port = int(os.getenv("OPENPOSE_BROWSER_PORT", "8189"))
    debug_log(f"[DEBUG] __main__: Starting PAL OpenPose Browser on http://{host}:{port}")
    debug_log(f"[DEBUG] __main__: Registry has {len(registry.list_all())} poses from list_all()")
    debug_log(f"[DEBUG] __main__: Registry has {len(registry.poses)} poses from direct access")
    uvicorn.run(app, host=host, port=port)
