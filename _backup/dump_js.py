# -*- coding: utf-8 -*-
import re, os
p = r"H:\tool\silkworm-trajectory\docs\index.html"
out = r"H:\tool\silkworm-trajectory\_backup\_js"
os.makedirs(out, exist_ok=True)
s = open(p, encoding="utf-8").read()
scripts = re.findall(r"<script>([\s\S]*?)</script>", s)
for i, code in enumerate(scripts):
    path = os.path.join(out, "block%d.js" % i)
    with open(path, "w", encoding="utf-8") as f:
        f.write(code)
    print(path, code.count("\n") + 1)
