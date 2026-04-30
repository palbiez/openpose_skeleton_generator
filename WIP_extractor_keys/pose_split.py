import json
import os
from collections import defaultdict

INPUT_FILE = r"C:\Users\firew\Documents\ComfyUI\input\openpose2\person_keypoints_custom.json"
OUTPUT_DIR = r"C:\Users\firew\Documents\ComfyUI\input\openpose2\split"

MIN_KEYPOINTS = 10
MIN_AREA = 2000

os.makedirs(OUTPUT_DIR, exist_ok=True)


# -------------------------
# Hilfsfunktionen
# -------------------------
def get_point(kp, i):
    return kp[i*3], kp[i*3+1], kp[i*3+2]


def classify_pose(kp):
    lx, ly, _ = get_point(kp, 11)
    rx, ry, _ = get_point(kp, 12)

    kx_l, ky_l, _ = get_point(kp, 13)
    kx_r, ky_r, _ = get_point(kp, 14)

    ax_l, ay_l, _ = get_point(kp, 15)
    ax_r, ay_r, _ = get_point(kp, 16)

    sx_l, sy_l, _ = get_point(kp, 5)
    sx_r, sy_r, _ = get_point(kp, 6)

    hip_y = (ly + ry) / 2
    knee_y = (ky_l + ky_r) / 2
    ankle_y = (ay_l + ay_r) / 2
    shoulder_y = (sy_l + sy_r) / 2

    hip_x = (lx + rx) / 2
    shoulder_x = (sx_l + sx_r) / 2

    vertical_span = abs(shoulder_y - ankle_y)
    horizontal_span = abs(sx_l - sx_r)

    # lying
    if horizontal_span > vertical_span * 1.3:
        return "lying"

    # sitting
    if abs(hip_y - knee_y) < 30:
        return "sitting"

    # kneeling
    if knee_y > hip_y and abs(knee_y - ankle_y) < 50:
        return "kneeling"

    # crouching
    if hip_y > knee_y - 20 and knee_y > ankle_y - 20:
        return "crouching"

    # reaching
    wx_l, wy_l, _ = get_point(kp, 9)
    wx_r, wy_r, _ = get_point(kp, 10)

    if wy_l < shoulder_y - 80 or wy_r < shoulder_y - 80:
        return "reaching"

    # leaning
    if abs(shoulder_x - hip_x) > 60:
        return "leaning"

    return "standing"

def classify_subpose(kp):
    result = {}

    # Knie
    _, ky_l, _ = get_point(kp, 13)
    _, ky_r, _ = get_point(kp, 14)

    if abs(ky_l - ky_r) < 30:
        result["knees"] = "both"
    else:
        result["knees"] = "one"

    # Beinabstand
    kx_l, _, _ = get_point(kp, 13)
    kx_r, _, _ = get_point(kp, 14)

    if abs(kx_l - kx_r) > 80:
        result["legs"] = "open"
    else:
        result["legs"] = "closed"

    # Torso
    hx_l, hy_l, _ = get_point(kp, 11)
    sx_l, sy_l, _ = get_point(kp, 5)

    if sy_l < hy_l - 40:
        result["torso"] = "upright"
    else:
        result["torso"] = "leaning_forward"

    return result

# -------------------------
# Hauptverarbeitung
# -------------------------
with open(INPUT_FILE, "r") as f:
    data = json.load(f)

grouped = defaultdict(list)
seen = set()  # deduplication

for ann in data["annotations"]:
    if ann["num_keypoints"] < MIN_KEYPOINTS:
        continue

    x, y, w, h = ann["bbox"]
    if w * h < MIN_AREA:
        continue

    keypoints = ann["keypoints"]

    # Dedup (optional aber sinnvoll)
    kp_hash = tuple(keypoints)
    if kp_hash in seen:
        continue
    seen.add(kp_hash)

    pose = classify_pose(keypoints)

    # NSFW Mapping
    if ann["category_id"] == 2:
        variant = "nsfw"
    else:
        variant = "base"
    subpose = classify_subpose(ann["keypoints"])
    grouped[(pose, variant)].append({
    "image_id": ann["image_id"],
    "keypoints": keypoints,
    "bbox": ann["bbox"],
    "subpose": subpose
})


# -------------------------
# Dateien schreiben
# -------------------------
print("\n--- Export ---\n")

for (pose, variant), items in grouped.items():
    filename = os.path.join(OUTPUT_DIR, f"{pose}_{variant}.json")

    with open(filename, "w") as f:
        json.dump(items, f)

    print(f"{pose}_{variant}: {len(items)}")

print("\nFertig.")