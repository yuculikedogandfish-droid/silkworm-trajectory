import io
P=r"PROGRESS_WEAVE_2026-11-16.md"
t=io.open(P,encoding="utf-8").read()
sec = """

## 48. r42 说明书升级（图层/分组/排版 + PDF 重出）

- 说明书网页 `docs/使用说明.html`：新增第 11 节「图层、分组与排版」，含图层树真实截图（base64 内嵌）、行内按钮说明表、组/整组拖动、框选（内联 SVG 示意）、吸附（内联 SVG 示意）、对齐/等距/阵列表、层序与锁定；目录补第 11 项，封面版本改 r42。
- 02「界面地图」右栏措辞改为「个体与图层」，06 隐藏说明改为按层「显/隐」；两条均按 r42 实际界面改写。
- 新增 `@media print` 白底紧凑样式（A4 13/12mm 边距、卡片不整体断页、图片限高 92mm、FAQ 深色字），第 11 节强制另起一页。
- 代码侧一处修正：`.lay-menu` 挂载点由 `document.body` 改为 `#habitat` 内，避免任何“只显示场地”的截图/隐藏样式把菜单一起吃掉（同时避免被 body 级样式误伤）。
- PDF 重出：`docs/蚕轨迹描图器_使用说明.pdf` 13 页 / 2.0MB（r36 为 7 页）。页数增长来自新增章节与配图，逐页已核对：封面/01/02/09/10/11–13 排版正常。
- 三副本同步：`docs/index.html` → `editor/silkworm-tracer.html`、`editor/蚕轨迹描图器.html` 字节一致；脚本分段 `node --check` 通过（s1–s3、s5；s0 为 JSON 数据段、s4 为拆分残段，均非代码段）。
"""
io.open(P,"a",encoding="utf-8").write(sec)
print("progress ok")
