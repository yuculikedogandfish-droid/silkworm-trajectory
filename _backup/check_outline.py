# -*- coding: utf-8 -*-
"""打印顶层结构快照：每个 <main>/aside/iframe/section/div.workspace 的位置。"""
from pathlib import Path
import re

p = Path(r"H:\tool\silkworm-trajectory\docs\index.html")
s = p.read_text(encoding="utf-8")

pats = [
    ('<header', r'<header'),
    ('<div class="workspace"', r'<div class="workspace"'),
    ('<main', r'<main'),
    ('</main>', r'</main>'),
    ('<iframe id="previewFrame"', r'<iframe id="previewFrame"'),
    ('</iframe>', r'></iframe>'),
    ('<section id="habitat"', r'<section id="habitat"'),
    ('</section>', r'</section>'),
    ('<div class="transport"', r'<div class="transport"'),
    ('<footer', r'<footer'),
    ('</body>', r'</body>'),
]
for label, pat in pats:
    idx = [m.start() for m in re.finditer(pat, s)]
    print(label, idx)

# 打印 main 起点之后 40 行，看工具条是否在 main 内
i = s.find('<main')
print('--- after <main> ---')
print(s[i:i+400])
