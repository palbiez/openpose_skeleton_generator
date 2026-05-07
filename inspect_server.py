import os
import pathlib

comfyui_root = pathlib.Path(os.getenv("COMFYUI_SOURCE_ROOT", pathlib.Path.home() / "ComfyUI"))
p = comfyui_root / "server.py"
text = p.read_text(encoding='utf-8', errors='ignore').splitlines()
for i, line in enumerate(text):
    if 'EXTENSION_WEB_DIRS' in line or 'web_dir' in line or 'static' in line or 'app.mount' in line:
        print(f'{i+1}:{line}')
