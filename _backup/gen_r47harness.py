# -*- coding: utf-8 -*-
import io, re, base64
ROOT = r"H:\tool\silkworm-trajectory"
s = io.open(ROOT + r"\_backup\rec43\t_v.html", encoding="utf-8").read()
b64 = base64.b64encode(io.open(r"C:\Users\54364\AppData\Local\Doubao\User Data\ClipboardTemp\6b643051-5cc5-4931-936f-e2e9517b281f.png", "rb").read()).decode("ascii")
s = re.sub(r'var IMG = "data:image/[^;]+;base64,[A-Za-z0-9+/=]+";', 'var IMG = "data:image/png;base64,' + b64 + '";', s, count=1)
s = s.replace('var polys = present.reduce(function(n,b){return n + (b.polys ? b.polys.length : 0);},0);', 'var polys = present.reduce(function(n,b){return n + (b.polys ? b.polys.length : 0);},0);\n  var outlines = present.filter(function(b){return b.outline && b.outline.length >= 3;});\n  var verts = outlines.map(function(b){return b.outline.length;});', 1)
s = s.replace('" holes=" + (st.holes||[]).length + " polys=" + polys + " weak=" + weak +', '" holes=" + (st.holes||[]).length + " polys=" + polys + " weak=" + weak + " outlines=" + outlines.length + " verts=" + verts.join("/") +', 1)
io.open(ROOT + r"\_backup\rec43\t_new.html", "w", encoding="utf-8").write(s)
print("new harness", len(s))
