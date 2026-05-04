import pathlib
p = pathlib.Path(r'C:\Users\firew\AppData\Local\Programs\ComfyUI\resources\ComfyUI\nodes.py')
text = p.read_text(encoding='utf-8').splitlines()
for i in range(2238, 2276):
    if i < len(text):
        print(f'{i+1}:{text[i]}')
