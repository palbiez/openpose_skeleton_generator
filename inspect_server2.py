import os
import pathlib

comfyui_root = pathlib.Path(os.getenv("COMFYUI_SOURCE_ROOT", pathlib.Path.home() / "ComfyUI"))
p = comfyui_root / "server.py"
lines = p.read_text(encoding='utf-8', errors='ignore').splitlines()
for i in range(330, 361):
    print(f'{i+1}:{lines[i]}')
