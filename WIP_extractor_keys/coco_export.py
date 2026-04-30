import json
from collections import defaultdict

INPUT_FILE = "person_keypoints_custom.json"
OUTPUT_FILE = "extended_poses2.json"

MIN_KEYPOINTS = 10
MIN_AREA = 2000

def get_point(kp, i):
    return kp[i*3], kp[i*3+1], kp[i*3+2]

def visible(kp, i):
    return kp[i*3+2] > 0

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

    # --- lying (sehr eindeutig zuerst) ---
    if horizontal_span > vertical_span * 1.3:
        return "lying"

    # --- sitting ---
    if abs(hip_y - knee_y) < 30:
        return "sitting"

    # --- kneeling ---
    if knee_y > hip_y and abs(knee_y - ankle_y) < 50:
        return "kneeling"

    # --- crouching (tiefer als sitting) ---
    if hip_y > knee_y - 20 and knee_y > ankle_y - 20:
        return "crouching"

    # --- reaching (nur wenn deutlich) ---
    wx_l, wy_l, _ = get_point(kp, 9)
    wx_r, wy_r, _ = get_point(kp, 10)

    if wy_l < shoulder_y - 80 or wy_r < shoulder_y - 80:
        return "reaching"

    # --- leaning (nur bei starker Verschiebung) ---
    if abs(shoulder_x - hip_x) > 60:
        return "leaning"

    # --- default ---
    return "standing"

with open(INPUT_FILE, "r") as f:
    data = json.load(f)

grouped = defaultdict(list)

for ann in data["annotations"]:
    if ann["num_keypoints"] < MIN_KEYPOINTS:
        continue

    x, y, w, h = ann["bbox"]
    if w * h < MIN_AREA:
        continue

    pose = classify_pose(ann["keypoints"])

    grouped[pose].append({
        "image_id": ann["image_id"],
        "keypoints": ann["keypoints"],
        "bbox": ann["bbox"]
    })

with open(OUTPUT_FILE, "w") as f:
    json.dump(grouped, f, indent=2)

print("Export fertig:")
for k in grouped:
    print(f"{k}: {len(grouped[k])}")