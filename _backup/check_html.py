# -*- coding: utf-8 -*-
"""抽取 index.html 里的 <script> 块（含 iframe srcdoc 内外），写到临时文件，供 node --check 校验语法。"""
import html
import re
import sys
from pathlib import Path

SRC = Path(r"H:\tool\silkworm-trajectory\docs\index.html")
OUT = Path(r"H:\tool\silkworm-trajectory\_backup\_check")
OUT.mkdir(parents=True, exist_ok=True)

raw = SRC.read_text(encoding="utf-8")
# srcdoc 内的脚本被 HTML 实体转义过，先整体反转义一份用于比对
unescaped = html.unescape(raw)

blocks = []
for m in re.finditer(r"<script(?:\s[^>]*)?>(.*?)</script>", raw, re.S):
    blocks.append(("outer%d" % len(blocks), m.group(1)))
for m in re.finditer(r"<script(?:\s[^>]*)?>(.*?)</script>", unescaped, re.S):
    body = m.group(1)
    if "silkworm" in body or "habitat" in body or "trajector" in body:
        blocks.append(("inner%d" % len(blocks), body))

for name, body in blocks:
    if not body.strip():
        continue
    p = OUT / (name + ".js")
    p.write_text(body, encoding="utf-8")
    print(name, len(body))
