import html
import re
import sys
from pathlib import Path

src = Path(sys.argv[1])
out_dir = Path(sys.argv[2])
out_dir.mkdir(parents=True, exist_ok=True)

text = src.read_text(encoding="utf-8")

# 1) 取出 srcdoc 属性的内容（属性值里是实体转义后的整页 HTML）
m = re.search(r'srcdoc="(.*?)"></iframe>', text, re.S)
inner_html = html.unescape(m.group(1)) if m else ""
outer_html = text[:m.start()] + text[m.end():] if m else text

script_re = re.compile(r"<script[^>]*>(.*?)</script>", re.S)

def dump(htm, prefix):
    made = []
    for i, body in enumerate(script_re.findall(htm)):
        p = out_dir / f"{prefix}_{i}.js"
        p.write_text(body, encoding="utf-8")
        made.append(p)
    return made

files = dump(outer_html, "outer") + dump(inner_html, "srcdoc")
for f in files:
    print(f"{f.name}\t{f.stat().st_size}")
print("total", len(files))
