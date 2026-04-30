import json
from pathlib import Path
from collections import defaultdict

ROOT = Path(r"C:\Users\firew\Documents\ComfyUI\input\openpose2\openpose")
OUTPUT_DIR = ROOT / "structured"

OUTPUT_DIR.mkdir(exist_ok=True)

grouped = defaultdict(list)


def parse_folder(folder_name):
    folder_name = folder_name.lower()

    # NSFW erkennen
    if folder_name.startswith("nsfw_"):
        variant = "nsfw"
        name = folder_name.replace("nsfw_", "")
    else:
        variant = "base"
        name = folder_name

    # Pose bestimmen
    if name in ["lying", "kneeling", "standing", "sitting"]:
        pose = name
        subpose = name
    else:
        # alles andere = Subpose
        subpose = name

        # einfache Zuordnung
        if "kneel" in name or "all_fours" in name:
            pose = "kneeling"
        elif "split" in name or "lying" in name:
            pose = "lying"
        elif "sitting" in name:
            pose = "sitting"
        elif "standing" in name or "suspended" in name:
            pose = "standing"
        else:
            pose = "special"

    return pose, variant, subpose


# -------------------------
# Verarbeitung
# -------------------------
for json_file in ROOT.rglob("*.json"):

    try:
        with open(json_file, "r", encoding="utf-8") as f:
            data = json.load(f)
    except:
        continue

    if "people" not in data or len(data["people"]) == 0:
        continue

    person = data["people"][0]

    if "pose_keypoints_2d" not in person:
        continue

    keypoints = person["pose_keypoints_2d"]

    # Ordner analysieren
    folder = json_file.parent.parent.name  # z.B. NSFW_Kneeling
    pose, variant, subpose = parse_folder(folder)

    grouped[(pose, variant)].append({
        "keypoints": keypoints,
        "pose": pose,
        "variant": variant,
        "subpose": subpose,
        "source": str(json_file.relative_to(ROOT))
    })


# -------------------------
# Export
# -------------------------
print("\n--- Export ---\n")

for (pose, variant), items in grouped.items():
    out_file = OUTPUT_DIR / f"{pose}_{variant}.json"

    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(items, f)

    print(f"{pose}_{variant}: {len(items)}")

print("\nFertig.")