import json
from pathlib import Path

# ===== INPUT =====
COCO_FILE = Path(r"C:\Users\firew\Documents\ComfyUI\input\openpose2\person_keypoints_train2017.json")
NSFW_FILE = Path(r"C:\Users\firew\Documents\ComfyUI\input\openpose2\openpose\person_keypoints_train2017.json")

OUTPUT = Path(r"C:\Users\firew\Documents\ComfyUI\input\openpose2\person_keypoints_custom.json")


def load(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


coco = load(COCO_FILE)
nsfw = load(NSFW_FILE)

# ===== OUTPUT STRUKTUR =====
images = []
annotations = []

image_id = 1
annotation_id = 1

# ===== Kategorien sauber definieren =====
categories = [
    {"id": 1, "name": "person"},
    {"id": 2, "name": "person_nsfw"}
]

# ===== DUPE FILTER =====
seen_keypoints = set()


def process_dataset(dataset, category_id):
    global image_id, annotation_id

    id_map = {}

    # Images neu nummerieren
    for img in dataset["images"]:
        id_map[img["id"]] = image_id

        images.append({
            "id": image_id,
            "file_name": img.get("file_name", f"{image_id}.png"),
            "width": img.get("width", 512),
            "height": img.get("height", 512)
        })

        image_id += 1

    # Annotations neu aufbauen
    for ann in dataset["annotations"]:
        kp = ann.get("keypoints")

        if not kp:
            continue

        # Duplikate vermeiden
        key = tuple(kp)
        if key in seen_keypoints:
            continue
        seen_keypoints.add(key)

        annotations.append({
            "id": annotation_id,
            "image_id": id_map[ann["image_id"]],
            "category_id": category_id,
            "keypoints": kp,
            "num_keypoints": ann.get("num_keypoints", 0),
            "iscrowd": 0,
            "area": ann.get("area", 0),
            "bbox": ann.get("bbox", [0, 0, 0, 0])
        })

        annotation_id += 1


# ===== DATEN VERARBEITEN =====
print("Verarbeite COCO (SFW)...")
process_dataset(coco, category_id=1)

print("Verarbeite NSFW...")
process_dataset(nsfw, category_id=2)

# ===== FINAL =====
merged = {
    "info": {
        "description": "COCO + NSFW OpenPose merged dataset",
        "version": "1.0"
    },
    "images": images,
    "annotations": annotations,
    "categories": categories
}

# KOMPAKT speichern
with open(OUTPUT, "w", encoding="utf-8") as f:
    json.dump(merged, f, separators=(",", ":"))

print("FERTIG:", OUTPUT)
print("Images:", len(images))
print("Annotations:", len(annotations))