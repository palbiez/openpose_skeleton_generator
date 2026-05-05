import os
from pathlib import Path

path = r"C:\Users\firew\Documents\ComfyUI\models\openpose"
png_count = 0
json_count = 0

for root, dirs, files in os.walk(path):
    for file in files:
        if file.endswith('.png'):
            png_count += 1
        elif file.endswith('.json'):
            json_count += 1

print(f"PNG files: {png_count}")
print(f"JSON files: {json_count}")

# Check for bone_structure.png specifically
bone_structure_count = 0
for root, dirs, files in os.walk(path):
    for file in files:
        if 'bone_structure' in file and file.endswith('.png'):
            bone_structure_count += 1

print(f"Bone structure PNG files: {bone_structure_count}")