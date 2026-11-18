# -*- coding: utf-8 -*-
"""在蚕室脚本段落里查 trace 侧符号残留（state. / state，应为 habitat. 或 window.__previewTrajs）。"""
from pathlib import Path
import re

p = Path(r"H:\tool\silkworm-trajectory\docs\index.html")
s = p.read_text(encoding="utf-8")
start = s.find("const MODEL = ")
end = s.find("window.__studioHabitat = {")
seg = s[start:end]
print("habitat block chars:", len(seg))
for m in re.finditer(r"\bstate\.[A-Za-z_]+", seg):
    line = seg[:m.start()].count("\n") + 1
    print("state ref at block line", line, "->", m.group(0))
for m in re.finditer(r"document\.getElementById\('(hab[A-Za-z]*)'\)", seg):
    pass
ids = set(re.findall(r"getElementById\('([A-Za-z0-9_-]+)'\)", seg))
missing = [i for i in sorted(ids) if f'id="{i}"' not in s]
print("ids referenced but not in HTML:", missing)
