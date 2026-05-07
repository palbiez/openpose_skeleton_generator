import json
import os
from pathlib import Path

ROOT = Path(os.getenv("OPENPOSE2_DIR", Path.home() / "ComfyUI" / "input" / "openpose2")) / "openpose"
OUTPUT = ROOT / "person_keypoints_train2017.json"

images = []
annotations = []

image_id = 1
annotation_id = 1


for json_file in ROOT.rglob("*.json"):

    try:
        with open(json_file, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"[ERROR] {json_file}: {e}")
        continue

    if "people" not in data or len(data["people"]) == 0:
        continue

    person = data["people"][0]

    if "pose_keypoints_2d" not in person:
        continue

    keypoints = person["pose_keypoints_2d"]

    coco_kp = []
    num_visible = 0

    xs = []
    ys = []

    for i in range(0, len(keypoints), 3):
        x, y, c = keypoints[i:i+3]

        v = 2 if c > 0 else 0
        if v > 0:
            num_visible += 1

        coco_kp.extend([x, y, v])

        if c > 0:
            xs.append(x)
            ys.append(y)

    # Calculate bounding box.
    if xs and ys:
        bbox = [
            min(xs),
            min(ys),
            max(xs) - min(xs),
            max(ys) - min(ys)
        ]
        area = bbox[2] * bbox[3]
    else:
        bbox = [0, 0, 0, 0]
        area = 0

    images.append({
        "id": image_id,
        "file_name": json_file.stem + ".png",
        "width": 512,
        "height": 512
    })

    annotations.append({
        "id": annotation_id,
        "image_id": image_id,
        "category_id": 1,
        "keypoints": coco_kp,
        "num_keypoints": num_visible,
        "iscrowd": 0,
        "area": area,
        "bbox": bbox
    })

    image_id += 1
    annotation_id += 1


coco = {
    "images": images,
    "annotations": annotations,
    "categories": [
        {
            "id": 1,
            "name": "person_nsfw",
            "supercategory": "person"
        }
    ]
}

with open(OUTPUT, "w", encoding="utf-8") as f:
    json.dump(coco, f, indent=2)

print(f"Done: {OUTPUT}")
print(f"Images: {len(images)}")
