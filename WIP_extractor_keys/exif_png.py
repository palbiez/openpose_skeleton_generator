import sys
print(sys.executable)
import os
import json
import subprocess
from pathlib import Path
from PIL import Image

# ===== KONFIG =====
ROOT_DIR = Path(r"C:\Users\firew\Documents\ComfyUI\input\openpose2\\")
USE_EXIFTOOL_FALLBACK = True  # deutlich robuster
EXIFTOOL_PATH = r"C:\EasyDiffusion\exiftool\exiftool.exe"

# ===== FUNKTIONEN =====

def extract_json_pil(png_path: Path):
    try:
        with Image.open(png_path) as img:
            for key, value in img.info.items():
                if isinstance(value, str):
                    text = value.strip()
                    if text.startswith("{") or text.startswith("["):
                        try:
                            return json.loads(text), f"PIL:{key}"
                        except json.JSONDecodeError:
                            continue
    except Exception as e:
        print(f"[FEHLER PIL] {png_path}: {e}")
    return None, None


def extract_json_exiftool(png_path: Path):
    try:
        result = subprocess.run(
            [EXIFTOOL_PATH, "-j", str(png_path)],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="ignore"
        )

        data = json.loads(result.stdout)[0]

        for key, value in data.items():
            if isinstance(value, str):
                text = value.strip()
                if text.startswith("{") or text.startswith("["):
                    try:
                        return json.loads(text), f"EXIF:{key}"
                    except json.JSONDecodeError:
                        continue
    except Exception as e:
        print(f"[FEHLER EXIFTOOL] {png_path}: {e}")

    return None, None


def process_file(png_path: Path):
    json_path = png_path.with_suffix(".json")

    if json_path.exists():
        return

    # 1. Versuch: PIL
    data, source = extract_json_pil(png_path)

    # 2. Fallback: exiftool
    if data is None and USE_EXIFTOOL_FALLBACK:
        data, source = extract_json_exiftool(png_path)

    if data:
        try:
            with open(json_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            print(f"[OK] {png_path} ({source})")
        except Exception as e:
            print(f"[FEHLER WRITE] {png_path}: {e}")
    else:
        print(f"[KEIN JSON] {png_path}")


# ===== MAIN =====

def main():
    count_total = 0
    count_found = 0

    for png_path in ROOT_DIR.rglob("*_bone_structure*.png"):
        count_total += 1
        process_file(png_path)

    print("\n--- FERTIG ---")
    print(f"Dateien geprüft: {count_total}")


if __name__ == "__main__":
    main()