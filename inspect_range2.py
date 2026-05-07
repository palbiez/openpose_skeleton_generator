import os
import pathlib

comfyui_root = pathlib.Path(os.getenv("COMFYUI_SOURCE_ROOT", pathlib.Path.home() / "ComfyUI"))
p = comfyui_root / "nodes.py"
text = p.read_text(encoding='utf-8').splitlines()
for i in range(2238, 2276):
    if i < len(text):
        print(f'{i+1}:{text[i]}')
