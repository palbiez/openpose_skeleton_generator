import json
import numpy as np

# --------------------------------------------------
# CONFIG
# --------------------------------------------------
import os
from pathlib import Path

try:
    from .openpose_io import coerce_keypoints, keypoints_to_canonical17
except ImportError:
    from openpose_io import coerce_keypoints, keypoints_to_canonical17

def _find_comfyui_models_dir() -> Path:
    env_path = os.getenv("OPENPOSE_MODELS_PATH")
    if env_path:
        candidate = Path(env_path)
        if candidate.exists():
            return candidate
        print(f"[PoseMatcher] WARNING: OPENPOSE_MODELS_PATH is set but does not exist: {candidate}")

    models_dir = None
    try:
        import folder_paths
    except (ImportError, ModuleNotFoundError) as exc:
        print(f"[PoseMatcher] INFO: folder_paths module unavailable: {exc}")
        folder_paths = None
    else:
        for attr_name in ["get_models_dir", "get_models_directory", "get_models_path", "get_model_dir"]:
            if hasattr(folder_paths, attr_name):
                try:
                    candidate = Path(getattr(folder_paths, attr_name)())
                    if candidate.exists():
                        models_dir = candidate
                        break
                except Exception:
                    continue

        if models_dir is None and hasattr(folder_paths, "get_input_directory"):
            try:
                input_dir = Path(folder_paths.get_input_directory())
                candidate = input_dir.parent / "models"
                if candidate.exists():
                    models_dir = candidate
                else:
                    candidate = (input_dir / ".." / "models").resolve()
                    if candidate.exists():
                        models_dir = candidate
            except Exception:
                pass

    if models_dir is None:
        search_roots = [Path(__file__).resolve().parent, Path.cwd()]
        for root in search_roots:
            for parent in [root] + list(root.parents):
                candidate = parent / "models"
                if candidate.exists() and (candidate / "openpose").exists():
                    models_dir = candidate
                    break
                candidate = parent / "ComfyUI" / "models"
                if candidate.exists() and (candidate / "openpose").exists():
                    models_dir = candidate
                    break
            if models_dir is not None:
                break

    return models_dir or Path("")

MODELS_DIR = _find_comfyui_models_dir()
REFERENCE_DIR = MODELS_DIR / "openpose" if (MODELS_DIR / "openpose").exists() else MODELS_DIR
if REFERENCE_DIR:
    print("[PoseMatcher] Using OpenPose reference directory")
else:
    print("[PoseMatcher] ERROR: could not resolve ComfyUI models path")

print(f"[PoseMatcher] Using path: {REFERENCE_DIR}")
# --------------------------------------------------
# UTILS
# --------------------------------------------------

def reshape(kp):
    return np.array(kp).reshape(-1, 3)


def normalize(kp):

    keypoints = coerce_keypoints(kp)
    if not keypoints:
        return None

    canonical = keypoints_to_canonical17(keypoints)
    if canonical is None:
        return None

    kp = np.array(canonical, dtype=np.float32).reshape(17, 3)

    valid = kp[:, 2] > 0
    pts = kp[valid][:, :2]

    if len(pts) < 5:
        return None

    min_xy = pts.min(axis=0)
    max_xy = pts.max(axis=0)

    scale = max(max_xy - min_xy)
    if scale < 1e-5:
        return None

    kp[:, :2] = (kp[:, :2] - min_xy) / scale

    return kp.flatten()

# --------------------------------------------------
# LOAD REFERENCE
# --------------------------------------------------

def load_reference():

    vectors = []
    meta = []

    try:
        try:
            from .pose_registry import get_registry
        except ImportError:
            from pose_registry import get_registry

        registry = get_registry()
        for item in registry.poses:
            if not item.get("json_path"):
                continue

            keypoints = registry.get_keypoints_by_id(item["id"])
            if not keypoints:
                continue

            norm = normalize(keypoints)
            if norm is None:
                continue

            vectors.append(norm)
            meta.append({
                "id": item["id"],
                "pose": item["pose"],
                "variant": item["variant"],
                "subpose": item["subpose"],
                "attributes": item.get("attributes", []),
                "keypoints": keypoints,
                "source_file": item.get("json_path") or item.get("source_file")
            })

        if vectors:
            return np.array(vectors), meta
    except Exception as exc:
        print(f"[PoseMatcher] Registry reference load failed: {exc}")

    reference_dir = REFERENCE_DIR / "openpose" if (REFERENCE_DIR / "openpose").exists() else REFERENCE_DIR
    for file in reference_dir.glob("*.json"):

        with open(file, "r", encoding="utf-8") as f:
            data = json.load(f)

        if not isinstance(data, list):
            continue

        for item in data:
            norm = normalize(item["keypoints"])
            if norm is None:
                continue

            vectors.append(norm)
            meta.append({
                "pose": item["pose"],
                "variant": item["variant"],
                "subpose": item["subpose"],
                "attributes": item["attributes"],
                "keypoints": item["keypoints"],
                "source_file": file.name
            })

    return np.array(vectors), meta


# --------------------------------------------------
# POSE MAPPING TABLE
# --------------------------------------------------
POSE_MAPPING = {
    # Invalid combinations -> valid alternatives
    ("standing", "prone"): ("lying", "prone"),
    ("standing", "supine"): ("lying", "supine"),
    ("sitting", "prone"): ("lying", "prone"),
    ("sitting", "supine"): ("lying", "supine"),
    ("kneeling", "prone"): ("lying", "prone"),
    ("kneeling", "supine"): ("lying", "supine"),
    # Add more mappings as needed
}

def map_pose_combination(pose, subpose):
    """Map invalid pose/subpose combinations to valid ones."""
    key = (pose, subpose)
    if key in POSE_MAPPING:
        new_pose, new_subpose = POSE_MAPPING[key]
        print(f"[PoseMapping] Mapped {pose}/{subpose} -> {new_pose}/{new_subpose}")
        return new_pose, new_subpose
    return pose, subpose


# --------------------------------------------------
# MATCHER CLASS
# --------------------------------------------------

class PoseMatcher:

    def __init__(self):
        print("Loading reference poses...")
        self.vectors, self.meta = load_reference()
        print(f"{len(self.vectors)} reference poses loaded")

    # --------------------------------------------------
    # LOW LEVEL (NUMPY)
    # --------------------------------------------------
    def match_indices(self, keypoints, top_k=3):

        query = normalize(keypoints)
        if query is None:
            print("[PoseMatcher] INVALID INPUT - not enough keypoints")
            return None, None

        if self.vectors is None or len(self.vectors) == 0:
            print("[PoseMatcher] ERROR: No reference vectors loaded")
            return None, None

        dists = np.linalg.norm(self.vectors - query, axis=1)
        print(f"[PoseMatcher] Matching against {len(self.vectors)} references")
        idx = np.argsort(dists)[:top_k]

        return idx, dists

    # --------------------------------------------------
    # HIGH LEVEL MATCH
    # --------------------------------------------------
    def match(self, keypoints, top_k=3):

        idx, dists = self.match_indices(keypoints, top_k)
        if idx is None:
            return None

        print(f"[PoseMatcher] Top {top_k} matches:")
        for i in idx:
            print(f"  -> {self.meta[i]['pose']} | {self.meta[i]['subpose']} | score={dists[i]:.4f}")

        results = []
        for i in idx:
            results.append({
                "id": self.meta[i].get("id"),
                "score": float(dists[i]),
                "pose": self.meta[i]["pose"],
                "variant": self.meta[i]["variant"],
                "subpose": self.meta[i]["subpose"],
                "attributes": self.meta[i]["attributes"],
                "keypoints": self.meta[i]["keypoints"],
                "source_file": self.meta[i]["source_file"]
            })

        return results

    # --------------------------------------------------
    # DIRECT SKELETON OUTPUT
    # --------------------------------------------------
    def match_best_keypoints(self, keypoints):

        result = self.match(keypoints, top_k=1)

        if not result:
            return None

        return result[0]["keypoints"]

    # --------------------------------------------------
    # BATCH MATCHER
    # --------------------------------------------------
    def match_batch(self, list_of_keypoints, top_k=1):

        outputs = []

        for kp in list_of_keypoints:
            result = self.match(kp, top_k=top_k)

            if result:
                outputs.append(result[0])  # best match
            else:
                outputs.append(None)

        return outputs

    # --------------------------------------------------
    # BATCH SKELETON ONLY
    # --------------------------------------------------
    def match_batch_keypoints(self, list_of_keypoints):

        outputs = []

        for kp in list_of_keypoints:
            best = self.match_best_keypoints(kp)
            outputs.append(best)

        return outputs


# --------------------------------------------------
# TEST
# --------------------------------------------------

if __name__ == "__main__":

    matcher = PoseMatcher()

    # Replace with real input for manual testing.
    test_kp = [0] * (17 * 3)

    print("\nSingle Match:")
    print(json.dumps(matcher.match(test_kp), indent=2))

    print("\nBest Skeleton:")
    print(matcher.match_best_keypoints(test_kp))

    print("\nBatch Match:")
    batch = [test_kp, test_kp]
    print(json.dumps(matcher.match_batch(batch), indent=2))
