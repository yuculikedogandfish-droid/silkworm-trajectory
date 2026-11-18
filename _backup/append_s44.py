import io
p = "PROGRESS_WEAVE_2026-11-16.md"
s = io.open(p, encoding="utf-8").read()
s += """

## §44 r38 —— 识别入口上移＋拖拽上传＋图层组（纯增量）

- 识别面板从左栏整体移到中间画布上方的一条 `.hab-rec-bar`（默认折叠，一行摘要）；展开后三列：拖拽框 / 行列与参数 / 按钮与状态。
- 上传方式两种：点击拖拽框（label 内 hidden file input）或直接把图片拖进框（dragenter 高亮、drop 读取，非图片给提示）。
- 右栏新增「图层」：PS 式组 / 层树，未编组层平铺；每层有勾选、名称（点名称＝选中该个体）、显／隐开关；组有折叠、改名、整组显隐。
- 编组：勾两层以上 →「编组所选」（prompt 命名）；「解散组」按勾选解散、未勾选则全部解散；组关系存 localStorage `silkworm-habitat-layer-groups/v1`（agentId→groupId）。
- 显隐直接写既有字段：织网单元 `hideSilk`；蚕 `hideSilk+hideBody`，渲染循环立即生效，不新造状态。
- 验收：独立 harness 跑模块 → 3 层 → 勾 2 → 编组得 1 组 2 层＋未编组 1 层；点组眼睛 → 两层 hideSilk 均置 1、按钮变「隐」；localStorage 已写入。整页截图：顶部折叠条、展开三列布局、右栏图层列表均正常。
"""
io.open(p, "w", encoding="utf-8").write(s)
print("progress ok")
