import io
p = r"_backup\r37_module.js"
s = io.open(p, encoding="utf-8").read()
s = s.replace("""    if (!cols) cols = Math.max(2, Math.round(bbW / (bbH / 8)));
    if (!rows) rows = Math.max(2, Math.round(bbH / (bbH / 8)));
    if (!rows) rows = 8;""",
"""    const cellGuess = Math.max(bbW, bbH) / 8;   // 长边按 8 格估，短边随之
    if (!cols) cols = Math.max(2, Math.round(bbW / cellGuess));
    if (!rows) rows = Math.max(2, Math.round(bbH / cellGuess));""")
io.open(p, "w", encoding="utf-8").write(s)

P = r"docs\index.html"
h = io.open(P, encoding="utf-8").read()
old = """        <div class="row"><label>目标格边长</label><input type="range" id="habRecCell" min="120" max="900" step="10" value="320"><span class="hab-adj-val" id="habRecCellVal">320px</span></div>"""
new = """        <div class="row"><label>列数</label><input type="number" id="habRecCols" min="0" max="40" step="1" value="0" placeholder="自动" style="width:62px"><label>排数</label><input type="number" id="habRecRows" min="0" max="40" step="1" value="0" placeholder="自动" style="width:62px"><span class="hab-note" style="margin:0">0＝自动估</span></div>
""" + old
assert h.count(old) == 1
h = h.replace(old, new)
# 用新模块替换旧模块
m = "/* ===== r37 图片识别"
i = h.find(m); start = h.rfind("<script>", 0, i); end = h.find("</script>", i)
mod = io.open(r"_backup\r37_module.js", encoding="utf-8").read().rstrip()
h = h[:start] + mod + h[end+len("</script>"):]
io.open(P, "w", encoding="utf-8").write(h)
print("html+module ok", len(h))
