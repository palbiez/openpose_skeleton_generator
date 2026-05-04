import pathlib
p = pathlib.Path(r'C:\Users\firew\AppData\Local\Programs\ComfyUI\resources\ComfyUI\server.py')
lines = p.read_text(encoding='utf-8', errors='ignore').splitlines()
for i in range(330, 361):
    print(f'{i+1}:{lines[i]}')
