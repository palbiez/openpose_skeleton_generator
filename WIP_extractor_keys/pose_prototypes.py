import json
import os
from pathlib import Path
import numpy as np
from collections import defaultdict

# -------------------------
# PATHS
# -------------------------
NSFW_ROOT = Path(r"C:\Users\firew\Documents\ComfyUI\input\openpose2\openpose")
COCO_FILE = Path(r"C:\Users\firew\Documents\ComfyUI\input\openpose2\person_keypoints_train2017.json")
STRUCTURE_FILE = Path(r"C:\Users\firew\Documents\ComfyUI\input\openpose2\structure.json")
OUTPUT_DIR = Path(r"C:\Users\firew\Documents\ComfyUI\input\openpose2\split")

OUTPUT_DIR.mkdir(exist_ok=True)

# -------------------------
# CONFIG
# -------------------------
MIN_KEYPOINTS = 10
MIN_AREA = 2000
SIMILARITY_THRESHOLD = 0.02
BATCH_SIZE = 5000

# -------------------------
# LOAD STRUCTURE
# -------------------------
with open(STRUCTURE_FILE, "r") as f:
    structure = json.load(f)

valid_poses = set(structure["poses"].keys())

# -------------------------
# UTILS
# -------------------------
def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def normalize_kp(kp):
    kp = np.array(kp).reshape(-1, 3)

    xs = kp[:, 0]
    ys = kp[:, 1]

    min_x, max_x = xs.min(), xs.max()
    min_y, max_y = ys.min(), ys.max()

    w = max(max_x - min_x, 1e-5)
    h = max(max_y - min_y, 1e-5)

    kp[:, 0] = (kp[:, 0] - min_x) / w
    kp[:, 1] = (kp[:, 1] - min_y) / h

    return kp.flatten()

def is_valid_annotation(ann):
    if ann.get("num_keypoints", 0) < MIN_KEYPOINTS:
        return False

    bbox = ann.get("bbox", [0, 0, 0, 0])
    if bbox[2] * bbox[3] < MIN_AREA:
        return False

    return True

def classify_pose_simple(kp):
    kp = np.array(kp).reshape(-1, 3)

    shoulder_y = (kp[5][1] + kp[6][1]) / 2
    hip_y = (kp[11][1] + kp[12][1]) / 2
    knee_y = (kp[13][1] + kp[14][1]) / 2
    ankle_y = (kp[15][1] + kp[16][1]) / 2

    vertical_span = abs(shoulder_y - ankle_y)
    horizontal_span = abs(kp[5][0] - kp[6][0])

    if horizontal_span > vertical_span * 1.3:
        return "lying"

    if abs(hip_y - knee_y) < 30:
        return "sitting"

    if knee_y > hip_y:
        return "kneeling"

    return "standing"

# -------------------------
# FILE APPEND (NSFW)
# -------------------------
def append_to_file(file_path, item):
    if file_path.exists():
        with open(file_path, "r") as f:
            data = json.load(f)
    else:
        data = []

    data.append(item)

    with open(file_path, "w") as f:
        json.dump(data, f)

# -------------------------
# BUFFER SYSTEM (COCO)
# -------------------------
buffers = defaultdict(list)

def flush_buffer(pose, variant):
    file_path = OUTPUT_DIR / f"{pose}_{variant}.json"

    existing = []
    if file_path.exists():
        with open(file_path, "r") as f:
            existing = json.load(f)

    existing.extend(buffers[(pose, variant)])

    with open(file_path, "w") as f:
        json.dump(existing, f)

    print(f"[FLUSH] {pose}_{variant}: +{len(buffers[(pose, variant)])}")

    buffers[(pose, variant)] = []

# -------------------------
# 1. NSFW TREE
# -------------------------
print("=== NSFW TREE ===")

for json_file in NSFW_ROOT.rglob("*.json"):

    try:
        data = load_json(json_file)
    except:
        continue

    if "people" not in data or len(data["people"]) == 0:
        continue

    kp = data["people"][0].get("pose_keypoints_2d")
    if not kp:
        continue

    folder = json_file.parent.parent.name.lower()

    if "nsfw_" in folder:
        pose = folder.replace("nsfw_", "")
        variant = "nsfw"
    else:
        pose = folder
        variant = "base"

    if pose not in valid_poses:
        pose = classify_pose_simple(kp)

    item = {
        "pose": pose,
        "variant": variant,
        "subpose": pose,
        "attributes": [],
        "keypoints": kp
    }

    file_path = OUTPUT_DIR / f"{pose}_{variant}.json"
    append_to_file(file_path, item)

print("NSFW fertig\n")

# -------------------------
# 2. COCO
# -------------------------
print("=== COCO ===")

coco = load_json(COCO_FILE)

seen_vectors = []

for i, ann in enumerate(coco["annotations"]):

    if not is_valid_annotation(ann):
        continue

    kp = ann["keypoints"]
    norm = normalize_kp(kp)

    # dedup
    duplicate = False
    for prev in seen_vectors:
        if np.linalg.norm(norm - prev) < SIMILARITY_THRESHOLD:
            duplicate = True
            break

    if duplicate:
        continue

    seen_vectors.append(norm)

    pose = classify_pose_simple(kp)

    if pose not in valid_poses:
        continue

    item = {
        "pose": pose,
        "variant": "base",
        "subpose": pose,
        "attributes": [],
        "keypoints": kp
    }

    buffers[(pose, "base")].append(item)

    # Batch flush
    if len(buffers[(pose, "base")]) >= BATCH_SIZE:
        flush_buffer(pose, "base")

    # Progress
    if i % 10000 == 0:
        print(f"{i} processed...")

# Final flush
for (pose, variant) in list(buffers.keys()):
    if buffers[(pose, variant)]:
        flush_buffer(pose, variant)

print("\n=== FERTIG ===")