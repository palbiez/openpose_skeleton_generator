import json
from pathlib import Path
openpose_dir = Path("C:\\Users\\firew\\Documents\\ComfyUI\\input\\openpose2")
with open(openpose_dir / 'pose_index.json', 'r', encoding='utf-8-sig') as f:
    pose_index = json.load(f)
for pose_name, genders in pose_index.items():
    for gender_name, variants in genders.items():
        for variant_name, subposes in variants.items():
            for subpose_name, png_files in subposes.items():
                for png_file in png_files[:3]:
                    print('orig', repr(png_file))
                    norm = str(png_file).replace('\\', '/').replace('\r', '/').replace('\n', '/').strip()
                    print('norm', repr(norm))
                raise SystemExit
