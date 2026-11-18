import io
p = r"_backup\r37_module.js"
s = io.open(p, encoding="utf-8").read()
old = """    // 目标格边长 T：宽高按图里格子的实际比例，不强行拉成正方
    const T = Number(($('habRecCell') || {}).value || 320);
    const pxW = bbW / cols, pxH = bbH / rows;
    const scale = T / pxW;
    const bW = T, bH = pxH * scale;"""
new = """    // 目标格边长 T 只是"上限"；整组块必须能放进场地（默认留 820px 的框）
    const Tuser = Number(($('habRecCell') || {}).value || 320);
    const pxW = bbW / cols, pxH = bbH / rows;
    const fitMax = 820;
    const fitScale = Math.min(fitMax / (cols * pxW), fitMax / (rows * pxH));
    const scale = Math.min(fitScale, Tuser / pxW);
    const bW = pxW * scale, bH = pxH * scale;"""
assert s.count(old) == 1
s = s.replace(old, new)
io.open(p, "w", encoding="utf-8").write(s)

P = r"docs\index.html"
h = io.open(P, encoding="utf-8").read()
i = h.find("/* ===== r37 图片识别"); start = h.rfind("<script>", 0, i); end = h.find("</script>", i)
h = h[:start] + s.rstrip() + h[end+len("</script>"):]
io.open(P, "w", encoding="utf-8").write(h)
print("scale patched")
