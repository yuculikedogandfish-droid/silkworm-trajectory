# -*- coding: utf-8 -*-
from pathlib import Path

s = Path(r"H:\tool\silkworm-trajectory\_backup\index-v2-20261116-before-restructure.html").read_text(encoding="utf-8")
i = s.find('<div class="transport"')
print(repr(s[i - 140:i + 40]))
print("---------")
k = s.find("<script", i)
print(repr(s[k - 100:k + 30]))

c = Path(r"H:\tool\silkworm-trajectory\docs\index.html").read_text(encoding="utf-8")
j = c.find('<div class="transport"')
print("current before transport:", repr(c[j - 160:j + 40]))
