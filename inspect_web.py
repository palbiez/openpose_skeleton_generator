import pathlib
root = pathlib.Path(r'C:\Users\firew\AppData\Local\Programs\ComfyUI\resources\ComfyUI')
for path in root.rglob('*.py'):
    text = path.read_text(encoding='utf-8', errors='ignore')
    if 'EXTENSION_WEB_DIRS' in text or 'WEB_DIRECTORY' in text or 'web_dir' in text:
        print(path)
