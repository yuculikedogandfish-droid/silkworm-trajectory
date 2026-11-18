# -*- coding: utf-8 -*-
"""导出当前 index.html 的关键结构行号，用于交接文档。"""
from pathlib import Path
import re

p = Path(r"H:\tool\silkworm-trajectory\docs\index.html")
lines = p.read_text(encoding="utf-8").splitlines()

anchors = [
    ('<style>', '<style>'),
    ('habitat css 注释', '/* ===== Digital Habitat（外层全宽区块） ===== */'),
    ('.workspace css', '<div class="workspace">'),
    ('<section id="habitat"', '<section id="habitat"'),
    ('</section> habitat', '<div id="habGhost"'),
    ('habitat script 起点', 'const MODEL = '),
    ('habitat script 终点', 'window.__studioHabitat = {'),
    ('tracer script 起点', 'const COLORS = '),
    ('iframe', '<iframe id="previewFrame"'),
    ('iframe 结束', '"></iframe>'),
    ('transport', '<div class="transport">'),
]
for label, needle in anchors:
    hits = [i + 1 for i, l in enumerate(lines) if needle in l]
    print(f"{label}: {hits}")

print("total lines:", len(lines))
