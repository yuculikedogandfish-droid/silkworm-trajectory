p = r"docs\index.html"
s = open(p, encoding="utf-8").read()
# 1) 格子尺寸上限 340/400 -> 1200（面板与拖手柄两处）
s = s.replace('id="habWeaveW" min="80" max="340" step="10"', 'id="habWeaveW" min="80" max="1200" step="10"')
s = s.replace('id="habWeaveH" min="80" max="340" step="10"', 'id="habWeaveH" min="80" max="1200" step="10"')
s = s.replace("a.w = Math.max(80, Math.min(340, parseFloat(document.getElementById('habWeaveW').value) || 200));",
              "a.w = Math.max(80, Math.min(1200, parseFloat(document.getElementById('habWeaveW').value) || 200));")
s = s.replace("a.h = Math.max(80, Math.min(340, parseFloat(document.getElementById('habWeaveH').value) || 200));",
              "a.h = Math.max(80, Math.min(1200, parseFloat(document.getElementById('habWeaveH').value) || 200));")
s = s.replace("const nw = Math.max(80, Math.min(400, h.edge === 'l' ? right - p.x : p.x - left));",
              "const nw = Math.max(80, Math.min(1200, h.edge === 'l' ? right - p.x : p.x - left));")
s = s.replace("const nh = Math.max(80, Math.min(400, h.edge === 't' ? bot - p.y : p.y - top));",
              "const nh = Math.max(80, Math.min(1200, h.edge === 't' ? bot - p.y : p.y - top));")
s = s.replace("a.w = Math.max(80, Math.min(400, Math.abs(p.x - fixedX)));",
              "a.w = Math.max(80, Math.min(1200, Math.abs(p.x - fixedX)));")
s = s.replace("a.h = Math.max(80, Math.min(400, Math.abs(p.y - fixedY)));",
              "a.h = Math.max(80, Math.min(1200, Math.abs(p.y - fixedY)));")
# 2) 缺口半径不再限制（原来最多 0.7 格）
s = s.replace("sh.notch.r = Math.max(12, Math.min(Math.min(a.w, a.h) * 0.7, Math.hypot(p.x - ox - sh.notch.cx, p.y - oy - sh.notch.cy)));",
              "sh.notch.r = Math.max(6, Math.hypot(p.x - ox - sh.notch.cx, p.y - oy - sh.notch.cy));")
# 3) 丝线默认更清楚：1.0px 起
s = s.replace("min=\"0.3\" max=\"2.2\" step=\"0.1\" value=\"0.7\"", "min=\"0.3\" max=\"2.2\" step=\"0.1\" value=\"1\"")
s = s.replace("Number.isFinite(habitat.silkWidth) ? habitat.silkWidth : 0.7", "Number.isFinite(habitat.silkWidth) ? habitat.silkWidth : 1")
s = s.replace("habitat.silkWidth = parseFloat(silkWidthEl.value) || 0.7;", "habitat.silkWidth = parseFloat(silkWidthEl.value) || 1;")
open(p, "w", encoding="utf-8").write(s)
print('caps ok')
