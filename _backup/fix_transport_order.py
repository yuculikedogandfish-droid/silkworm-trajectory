# -*- coding: utf-8 -*-
"""把 .transport 播放条移回描图器面板底部，并给 workspace 加一层 .panes 行容器。"""
from pathlib import Path

P = Path(r"H:\tool\silkworm-trajectory\docs\index.html")
s = P.read_text(encoding="utf-8")

# 1) 剪出 transport 块
start = s.find('<div class="transport">')
assert start != -1, "transport not found"
end_tag = s.find("</div>", start)
assert end_tag != -1
end = end_tag + len("</div>")
block = s[start:end]
assert 'id="seekBar"' in block, block[:200]

# 连同一个前导空行一起删掉
before = s[:start]
while before.endswith("\n\n"):
    before = before[:-1]
s = before + s[end:].lstrip("\n")
print("transport removed, len:", len(s))

# 2) workspace 内加 .panes 行容器
anchor = '<div class="workspace">'
assert s.count(anchor) == 1
s = s.replace(anchor, anchor + '\n  <div class="panes">', 1)

# 3) 在 iframe 收尾的 </div> 处，插入 panes 收尾 + transport + workspace 收尾
mid = '"></iframe>\n</div>'
assert s.count(mid) == 1, s.count(mid)
replacement = '"></iframe>\n  </div>\n\n' + block + '\n</div>'
s = s.replace(mid, replacement, 1)

P.write_text(s, encoding="utf-8")
print("done, len:", len(s))

# 校验
c = Path(r"H:\tool\silkworm-trajectory\docs\index.html").read_text(encoding="utf-8")
print("transport count:", c.count('<div class="transport">'))
i_ws = c.find('<div class="workspace">')
i_panes = c.find('<div class="panes">')
i_iframe = c.find('<iframe id="previewFrame"')
i_frame_end = c.find('"></iframe>')
i_transport = c.find('<div class="transport">')
i_section = c.find('<section id="habitat"')
print("order ok:", i_ws < i_panes < i_iframe < i_frame_end < i_transport < i_section)
print(repr(c[i_frame_end:i_transport + 30]))
