import pathlib
p = pathlib.Path(r'C:\Users\firew\AppData\Local\Programs\ComfyUI\resources\ComfyUI\server.py')
text = p.read_text(encoding='utf-8', errors='ignore').splitlines()
for i, line in enumerate(text):
    if 'EXTENSION_WEB_DIRS' in line or 'web_dir' in line or 'static' in line or 'app.mount' in line:
        print(f'{i+1}:{line}')
