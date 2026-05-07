import pathlib

import os

p = pathlib.Path(os.getenv("COMFYUI_SOURCE_ROOT", pathlib.Path.home() / "ComfyUI")) / "nodes.py"
text = p.read_text(encoding='utf-8')
patterns = ['UPDATE', 'INPUT_TYPES', 'custom_nodes']
for i, l in enumerate(text.splitlines()):
    if any(pat in l for pat in patterns):
        print(f'{i+1}:{l}')
