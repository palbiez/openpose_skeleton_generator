import os
import pathlib

comfyui_root = pathlib.Path(os.getenv("COMFYUI_SOURCE_ROOT", pathlib.Path.home() / "ComfyUI"))
root = comfyui_root / "web"
for path in root.rglob('*.js'):
    text = path.read_text(encoding='utf-8', errors='ignore')
    if 'extensions/' in text or 'extensions' in text and 'websocket' not in text:
        print(path)
