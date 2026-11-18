# -*- coding: utf-8 -*-
import re, os, html
p = r"H:\tool\silkworm-trajectory\docs\index.html"
out = r"H:\tool\silkworm-trajectory\_backup\_js"
os.makedirs(out, exist_ok=True)
s = open(p, encoding="utf-8").read()
a = s.index('srcdoc="') + len('srcdoc="')
b = s.index('"></iframe>', a)
src = s[a:b]
outer = s[:a] + s[b:]

inner = re.findall(r"<script>([\s\S]*?)</script>", src)
for i, code in enumerate(inner):
    path = os.path.join(out, "inner%d.js" % i)
    with open(path, "w", encoding="utf-8") as f:
        f.write(html.unescape(code))
    print(path, code.count("\n") + 1)

ext = re.findall(r"<script>([\s\S]*?)</script>", outer)
for i, code in enumerate(ext):
    path = os.path.join(out, "outer%d.js" % i)
    with open(path, "w", encoding="utf-8") as f:
        f.write(code)
    print(path, code.count("\n") + 1)
