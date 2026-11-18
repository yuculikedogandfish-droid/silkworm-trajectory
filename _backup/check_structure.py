# -*- coding: utf-8 -*-
"""结构体检：确认蚕室在外层、iframe 内无 habitat 残留、关键 id/类只出现一次。"""
from pathlib import Path
import re

p = Path(r"H:\tool\silkworm-trajectory\docs\index.html")
s = p.read_text(encoding="utf-8")

def count(pat):
    return len(re.findall(pat, s))

i_iframe = s.find('<iframe id="previewFrame"')
i_endframe = s.find('></iframe>')
i_section = s.find('<section id="habitat"')
i_habscript = s.find("const MODEL = ")
print("iframe start:", i_iframe, "iframe end:", i_endframe, "section:", i_section)
print("habitat after iframe:", i_section > i_endframe, "| habitat section inside iframe:", i_iframe < i_section < i_endframe)

inner = s[i_iframe:i_endframe]
print("srcdoc still has #habitat:", 'id="habitat"' in inner or 'id=&quot;habitat&quot;' in inner)
print("inner has habOpenLeft:", 'habOpenLeft' in inner)

for name, pat in [
    ('section habitat', r'<section id="habitat"'),
    ('iframe', r'<iframe id="previewFrame"'),
    ('</iframe>', r'></iframe>'),
    ('habGhost div', r'<div id="habGhost"'),
    ('habToast div', r'<div id="habToast"'),
    ('hab-stage class', r'class="hab-stage"'),
    ('preview-off refs', r'preview-off'),
    ('split-preview refs', r'split-preview'),
    ('goHabitat id', r'id=&quot;goHabitat&quot;|id="goHabitat"'),
]:
    print(f"{name}: {count(pat)}")

# 关键函数是否只定义一次（外层）
for fn in ['function measuredSource', 'function syncMeasured', 'function toast(', 'function updateGhost',
           'function clearGhost', 'function applyPanelState', 'function togglePanel', 'function pushTrajToParent']:
    print(fn, "->", s.count(fn))

print("--- tail ---")
print(s[-40:])
