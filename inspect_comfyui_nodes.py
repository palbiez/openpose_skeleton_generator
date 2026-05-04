import pathlib

p = pathlib.Path(r'C:\Users\firew\AppData\Local\Programs\ComfyUI\resources\ComfyUI\nodes.py')
text = p.read_text(encoding='utf-8')
patterns = ['UPDATE', 'INPUT_TYPES', 'custom_nodes']
for i, l in enumerate(text.splitlines()):
    if any(pat in l for pat in patterns):
        print(f'{i+1}:{l}')
