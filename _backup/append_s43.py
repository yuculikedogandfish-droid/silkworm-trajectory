import io
p = "PROGRESS_WEAVE_2026-11-16.md"
s = io.open(p, encoding="utf-8").read()
s += """

## §43 r37 —— 上传一张图 → 自动识别版式并生成（纯新增）

- 入口：左栏最末折叠区「从图片识别版式（上传一张图，自动铺块）」；另有独立覆盖层画布 `#habRecOverlay`（pointer-events:none）。
- 流程：读图（长边缩到 1400）→ 4px 方框模糊把丝线糊成面 → Otsu 取亮面 → 取整块外框 bbox → 按列数/排数均匀切片（0=自动，长边按 8 格估）→ 每片算亮面占比 >34% 判"有丝" → 格内暗块连通域：内部团块=圆孔（半径=面积等效圆、限制 ≤0.42 短边），贴边团块=咬口（半径=短边一半、圆心贴边，画时被格边裁成缺口）。
- 生成：`H.addWeave({})` 取新单元 → 直接赋 w/h/x/y/tileField=false/shape=plain/seed → 写 `custom.shapes['0,0']={notch:null,islands}` → `cache.clear()` → `H.buildWeave(u)`；「替换现有块群」走 `__weaveHooks.deleteUnit`。
- 缩放：整组块自动塞进 820px 框（格边长为上限），避免溢出场地。
- 验收：竖版参考图 → 5×8 网格、33 块有丝 / 7 空位、12 个孔/咬口（预览与场地叠合一致）；横版 → 8×5、33/7、13 个；3×3 小样生成 9 块 178×278，位置 ±182 排布、孔洞写入 5 块。
- 不改任何既有函数：全部逻辑在文件末尾独立 IIFE，只用 `window.__studioHabitat` 与 `__weaveHooks`；折叠区默认收起。
"""
io.open(p, "w", encoding="utf-8").write(s)
print("progress ok")
