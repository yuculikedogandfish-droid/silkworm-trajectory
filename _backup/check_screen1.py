# -*- coding: utf-8 -*-
import re, sys
p = r"H:\tool\silkworm-trajectory\docs\index.html"
s = open(p, encoding="utf-8").read()

# 只检查外层文档（srcdoc 内容单独剔除）
a = s.index('srcdoc="') + len('srcdoc="')
b = s.index('"></iframe>', a)
outer = s[:a] + s[b:]

print("screen1 open:", outer.count('<div class="screen1">'))
print("body open:", len(re.findall(r"<body[^>]*>", outer)))
print("script open:", len(re.findall(r"<script[^>]*>", outer)), "close:", outer.count("</script>"))
print("section open:", len(re.findall(r"<section[^>]*>", outer)), "close:", outer.count("</section>"))
print("screen1 index:", outer.index('<div class="screen1">'))
print("habitat index:", outer.index('<section id="habitat"'))
print("cue index:", outer.index('class="scroll-cue"'))

# 粗略 div 平衡（剔除 script/style 内容）
clean = re.sub(r"<script[\s\S]*?</script>", "", outer)
clean = re.sub(r"<style[\s\S]*?</style>", "", clean)
opens = len(re.findall(r"<div\b", clean))
closes = clean.count("</div>")
print("div open:", opens, "close:", closes, "balanced:", opens == closes)
if opens != closes:
    sys.exit(1)
