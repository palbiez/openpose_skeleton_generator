import pathlib
root = pathlib.Path(r'C:\Users\firew\AppData\Local\Programs\ComfyUI\resources\ComfyUI\web')
for path in root.rglob('*.js'):
    text = path.read_text(encoding='utf-8', errors='ignore')
    if 'extensions/' in text or 'extensions' in text and 'websocket' not in text:
        print(path)
