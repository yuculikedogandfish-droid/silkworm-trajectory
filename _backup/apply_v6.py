import io
p = r"_backup\r37_module.js"
s = io.open(p, encoding="utf-8").read()
old = """            const rr = Math.sqrt(cnt / Math.PI);
            const isEdgeBite = maxX === W - 1 || minX === 0 || maxY === H2 - 1 || minY === 0;
            if (isEdgeBite && !wantNotch) continue;
            if (!isEdgeBite && !wantHoles) continue;
            b.islands.push({ cx: (ccx - W / 2) * scale, cy: (ccy - H2 / 2) * scale, r: Math.min(rr * scale, Math.min(bW, bH) * 0.62) });"""
new = """            const rpx = Math.min(bwc, bhc) / 2;
            const left = minX === 0, right = maxX === W - 1, top = minY === 0, bot = maxY === H2 - 1;
            const isEdgeBite = left || right || top || bot;
            if (isEdgeBite && !wantNotch) continue;
            if (!isEdgeBite && !wantHoles) continue;
            if (isEdgeBite) {
              if (extent < 0.45) continue;
              // 咬口：把圆心贴到它咬住的那条边上，半径取短边的一半，画出来才会贴着格边
              let cxp = ccx, cyp = ccy;
              if (left) cxp = rpx; else if (right) cxp = W - rpx;
              if (top) cyp = rpx; else if (bot) cyp = H2 - rpx;
              b.islands.push({
                cx: (cxp - W / 2) * scale,
                cy: (cyp - H2 / 2) * scale,
                r: Math.min(rpx * scale, Math.min(bW, bH) * 0.55)
              });
            } else {
              if (extent < 0.62 || aspect < 0.7 || aspect > 1.45) continue;
              b.islands.push({
                cx: (ccx - W / 2) * scale,
                cy: (ccy - H2 / 2) * scale,
                r: Math.min(Math.sqrt(cnt / Math.PI) * scale, Math.min(bW, bH) * 0.42)
              });
            }"""
assert s.count(old) == 1
s = s.replace(old, new)
io.open(p, "w", encoding="utf-8").write(s)
P = r"docs\index.html"
h = io.open(P, encoding="utf-8").read()
i = h.find("/* ===== r37 图片识别"); start = h.rfind("<script>", 0, i); end = h.find("</script>", i)
h = h[:start] + s.rstrip() + h[end+len("</script>"):]
io.open(P, "w", encoding="utf-8").write(h)
print("islands snapped")
