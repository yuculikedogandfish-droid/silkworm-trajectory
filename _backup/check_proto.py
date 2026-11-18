# -*- coding: utf-8 -*-
import re, os, subprocess, tempfile
p = r"H:\tool\silkworm-trajectory\prototype\weave-lab.html"
s = open(p, encoding="utf-8").read()
scripts = re.findall(r"<script>([\s\S]*?)</script>", s)
print("script blocks:", len(scripts))
out = r"H:\tool\silkworm-trajectory\_backup\_js"
os.makedirs(out, exist_ok=True)
for i, code in enumerate(scripts):
    fp = os.path.join(out, "proto%d.js" % i)
    open(fp, "w", encoding="utf-8").write(code)
    print(fp, code.count("\n") + 1)
