# -*- coding: utf-8 -*-
"""把场景 JSON 注入 index.html 的一份副本，供单帧核对用（模拟 render_led_frames.ps1 的注入）"""
import io, os, json

src = r'H:\tool\silkworm-trajectory\docs\index.html'
scene = r'C:\Users\54364\AppData\Local\Temp\qa-master-scene.json'
dst = r'C:\Users\54364\AppData\Local\Temp\qa-single-scene.html'

with io.open(src, 'r', encoding='utf-8') as f:
    s = f.read()
with io.open(scene, 'r', encoding='utf-8') as f:
    sc = json.load(f)
inject = '<script>window.__LED_SCENE=' + json.dumps(sc, ensure_ascii=False) + ';</script>'
i = s.index('</head>')
s = s[:i] + inject + s[i:]
with io.open(dst, 'w', encoding='utf-8', newline='') as f:
    f.write(s)
print(dst)
