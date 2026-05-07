import json
import os
import numpy as np
from pathlib import Path

# -------------------------
# PATHS
# -------------------------
INPUT_DIR = Path(os.getenv("OPENPOSE2_DIR", Path.home() / "ComfyUI" / "input" / "openpose2")) / "split"
OUTPUT_DIR = INPUT_DIR / "enriched"

OUTPUT_DIR.mkdir(exist_ok=True)

# -------------------------
# HELPERS
# -------------------------
def to_np(kp):
    return np.array(kp).reshape(-1, 3)


# -------------------------
# SUBPOSE
# -------------------------
def classify_lying(kp):
    shoulder_y = (kp[5][1] + kp[6][1]) / 2
    hip_y = (kp[11][1] + kp[12][1]) / 2

    shoulder_x = (kp[5][0] + kp[6][0]) / 2
    hip_x = (kp[11][0] + kp[12][0]) / 2

    if shoulder_y > hip_y:
        return "prone"

    if abs(shoulder_x - hip_x) > 0.1:
        return "side"

    return "back"


def classify_subpose(pose, kp):
    if pose == "lying":
        return classify_lying(kp)

    if pose == "kneeling":
        knee_diff = abs(kp[13][1] - kp[14][1])
        return "one_knee" if knee_diff > 0.05 else "both_knees"

    if pose == "sitting":
        return "floor" if kp[11][1] > kp[5][1] else "chair"

    if pose == "standing":
        return "neutral"

    return pose


# -------------------------
# ATTRIBUTES
# -------------------------
def extract_attributes(kp):
    attrs = []

    shoulder_y = (kp[5][1] + kp[6][1]) / 2

    # arms up
    wrist_y = min(kp[9][1], kp[10][1])
    if wrist_y < shoulder_y - 0.1:
        attrs.append("arms_up")

    # legs open
    knee_dist = abs(kp[13][0] - kp[14][0])
    hip_width = abs(kp[11][0] - kp[12][0])

    if hip_width > 0 and knee_dist / hip_width > 1.5:
        attrs.append("legs_open")

    # torso twist
    shoulder_x = (kp[5][0] + kp[6][0]) / 2
    hip_x = (kp[11][0] + kp[12][0]) / 2

    if abs(shoulder_x - hip_x) > 0.1:
        attrs.append("torso_twist")

    # head down
    head_y = kp[0][1]
    if head_y > shoulder_y + 0.1:
        attrs.append("head_down")

    return attrs


# -------------------------
# MAIN
# -------------------------
print("=== Subpose Pipeline ===")

for file in INPUT_DIR.glob("*.json"):

    print(f"Processing: {file.name}")

    with open(file, "r", encoding="utf-8") as f:
        data = json.load(f)

    enriched = []

    for item in data:
        kp_raw = item["keypoints"]
        kp = to_np(kp_raw)

        pose = item["pose"]

        subpose = classify_subpose(pose, kp)
        attributes = extract_attributes(kp)

        enriched.append({
            "pose": pose,
            "variant": item["variant"],
            "subpose": subpose,
            "attributes": attributes,
            "keypoints": kp_raw
        })

    out_file = OUTPUT_DIR / file.name

    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(enriched, f)

    print(f"Saved: {out_file.name} ({len(enriched)})")

print("\nDONE.")
