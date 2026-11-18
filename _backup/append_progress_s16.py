# -*- coding: utf-8 -*-
"""把 §16 追加到进度文档末尾（utf-8，无 BOM）。"""

from pathlib import Path

TEXT = """
## §16 分层 strata / 多边形轮廓单元 / 有限块群（2026-11-16，第 8 轮）

用户本轮三项要求：① 织块要有分层（strata）；② 新单元按多边形轮廓创建，而不是只能拖矩形框；③ 不要无限格子，要有限数量、贴近参考图的块群。

### 16.1 分层（2D strata 合成，不用 3D 半透明叠）

- `agent.strata`（1–3，默认 2），面板「分层」滑条可改，导出/导入带 `strata`。
- 每层：`off = (L-(n-1)/2)*cw*0.012` 的微小位移 + `tone` 递减 `1-L*0.10`，`L=0` 先铺一遍粗线柔雾（`lineWidth*3.4`，alpha 0.04–0.14），再叠细纤维。
- 已织满（`u>=0.995`）的块走 `weaveRasterFor(..., light, tone, strata)` 离屏位图，缓存键含 `strata`；未织满仍逐丝推进（沿 `weavePathCum` 的实际丝长顺序）。

### 16.2 多边形轮廓单元（像建模软件那样手画 + 拖顶点）

- 新按钮「按轮廓新建单元」→ `startOutlineUnit()`：画布上依次点顶点（凹多边形也行），双击 → `finishOutlineUnit()` 按 bbox 建单元、`outline` 存相对中心的顶点、`shape='island'` 保留大圆孔；Esc 取消。
- 编辑已有单元：`habWeaveEditMode` 增加 `outline`，点顶点后双击即 `agent.outline = pts - 中心`，`buildWeave` 重建。
- `weaveHandles` 新增 `outlineV` 白点手柄：可拖动改顶点、Alt+点删顶点（少于 3 个拒绝）。
- 可织区域：`weaveAllowed` 对 `cell.outline` 走 `weaveInPoly` + `weavePolyDist`（壳内且距边 ≥ margin），外框描一道 `rgba(206,216,210,0.07)` 的边。
- 壁的渲染与评估都过 `weaveSmooth`（Catmull-Rom，`closed` 默认 true），人工画的壁是曲线而不是折线。

### 16.3 有限块群（贴参考图，不铺满）

- 新按钮「铺块群（≤20）」→ `addWeaveMosaic()`：5×5 位阵、间距 `tile*1.03`、随机挑约六成（`want = max(9, round(cand*0.62))`，总数上限 20）；单元边长 `tile = min(spanW/4.6, spanH/4.6)`（参考图 1095px 宽、块≈245px ≈ 1/4.5 场宽）。
- 每块：`gap=8` 硬黑缝、`strata=2`、`worms=6`、`tone=0.58–1.13`、`shape` 72% `island` / 28% `notchIsland`、`u=0`，放完每块都能单独拖 / 改形状 / 改亮度。
- 纤维方向：`weaveThread` 里 32% 的带在 `weaveBandAngle` 基础上再偏 ±(0.35–0.77) rad，形成参考图那种交错马赛克纹理（不是单向拉丝）。
- 整体亮度乘 0.82，块间 tone 差更接近参考图的黑白分层。

### 16.4 验收（无头 Chrome 截图）

- `_backup\\probe_weave_mosaic.py`：点「铺块群」，16 块（5×5 位阵 62% 抽样），块 77×77，`gap 8 / strata 2 / tone 0.59–1.03`，各块大圆孔位置随机、块间硬黑缝、亮度分层可见。
- `_backup\\probe_outline_unit.py`（模拟 4 次 pointerdown + dblclick）：新建 1 个轮廓单元，`outline=4`、`w=208 h=195`，织块按多边形裁剪、内含大圆孔。
- `node --check` 三块脚本（outer_0 / outer_1 / srcdoc_0）全绿。
- 截图：`C:\\Users\\54364\\AppData\\Local\\Temp\\qa-mosaic6.png`（整片块群）、`qa-outline2.png`（轮廓单元）。注意 canvas 内部高 2222px，headless 必须 `--window-size=1500,2400` 才能看全场地。

### 16.5 已知未完成

- 块群仍是「5×5 位阵抽样」的规则骨架；参考图里块边缘有轻微错位与缺块轮廓，需要再加不规则化。
- 轮廓单元的点集仍是手点折线，虽已可拖顶点，但还没有「点中边插入顶点 / 双点平滑手柄」。
- 跨格/跨单元丝线连续性、整场 `tileField` 模式（默认关）仍是 P2 余项。
"""


def main():
    p = Path(r"H:\tool\silkworm-trajectory\PROGRESS_WEAVE_2026-11-16.md")
    with p.open("a", encoding="utf-8", newline="\n") as f:
        f.write(TEXT)
    print(p.stat().st_size)


if __name__ == "__main__":
    main()
