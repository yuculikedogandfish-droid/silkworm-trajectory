# -*- coding: utf-8 -*-
"""向 PROGRESS_WEAVE_2026-11-16.md 追加 §22（r14 孔缘过渡）。"""
import sys, io, os

path = sys.argv[1] if len(sys.argv) > 1 else r"H:\tool\silkworm-trajectory\PROGRESS_WEAVE_2026-11-16.md"

sec = """
---

## 22. r14 · 单元格圆孔边缘过渡（2026-11-16）

### 22.1 反馈
用户对照参考图指出：「单元格内开洞的地方边缘太生硬，怎么没有过渡啊就是一团均匀的毛圈」。
即孔口是一条等亮度的环，丝网与黑洞之间没有密度衰减，读起来像“画出来的毛圈”。

### 22.2 改法（`docs/index.html`，单文件 IIFE，无新依赖）
1. **孔缘由等亮圆环 → 大量短弧 + 密度渐变**
   `weaveThread` 的 `bi===0` 分支：
   - `fringe = minWH * 0.12`（孔缘过渡带宽，占单元格短边 12%）
   - `arcs = clamp(minWH * 0.62, 50, 240)`（弧的条数随单元尺寸走；200 单位格约 124 条）
   - 半径 `rr = isl.r * (1 + 0.03*(rng-0.5)) + fringe * pow(t,0.62) * (0.62+rng*0.6)`
   - 弧长 `span = 0.10 + rng*0.32`，步数 `st = max(9, round(26*span))`
   - 亮度系数 `mul = (0.95 - 0.78*t) * (0.45 + rng*0.55)`：越贴孔越亮、越向外越淡（t 为归一化半径位置）
   - 孔缘段返回 `{pts, mul}`，其余段仍是裸点列；`weaveCellContent` 的 `segs.forEach` 两种形态都吃，alpha 乘 `mul`
2. **孔口羽化**：新增 `weaveFeatherHoles(g, cell, ox, oy, v)`，对每个 island 用 `destination-out` 径向渐变（`r*0.45` 起不透明 → `r+feather` 全透明，`feather = max(1.5, r*0.16)`）。
   - 实时绘制：`drawWeave` 的逐格 `clip` 区内、丝画完后调用（`v` 用世界→屏幕映射）
   - 离屏缓存：`weaveRasterFor` 末尾调用（传入 `{s: kx, px, py}` 位图映射），位图里就不带硬边
3. **孔洞轮廓非圆化**：`weaveAllowed` 的 island 判定改为
   `r_eff = isl.r * (1 + 0.045*sin(3θ+ph) + 0.022*sin(7θ+ph*2.3))`；`weaveCellSpecAt` 给 island 加 `ph: rng()*Math.PI*2`（手工编辑出的 island 无 `ph` 时按 0 走）。
   效果：孔口是“有毛边的洞”，不再是完美圆。
4. **删掉 SDF 轮廓描边线**：`drawWeave` 里原先 `content.walls.forEach` 描的那道 `rgba(206,216,210,0.07)` 等粗细线，在 5× 放大下会被读成“画出来的圆圈”，是「生硬」的另一半来源；现在只保留多边形单元 `content.cell.outline` 的描边和人工壁 `customWalls`。

### 22.3 验收（`_backup/probe_p2_accept.py`，同步执行以便真实计时）
| 项 | 结果 |
| --- | --- |
| 60 格 × 3 层 @u=1（1000 px 预览） | 11.62 ms/帧 → 86.1 fps（要求 ≥24） |
| 12 格 @u=0.55 | 6.82 ms → 60 格外推 34.1 ms/帧 → 29.3 fps（要求 ≥24） |
| 同 seed paths | 301/301，不一致点 0 |
| 覆盖 0.2→0.7 亮度 | 71.3 → 81.5 → 89.7 → 97.0 → 99.2，单调 |
| 圆孔内点占比 | 0 / 9687 |
| 洞缘 vs 远区（首带 0.08c） | 416.2 vs 275.4 ≈ **1.51×**（原环带版 2.03×；带子现在铺到 0.12c，首带均值被拉平，视觉上是渐变而非环） |
| u=0 → u=1 亮度 | 0.0 → 112.8 |
| 30 s 动画 u 0→1 | 回退帧 0，单帧最大增量 0.0006 |
| 结构 | paths 352 / pts 9867 / walls 3（环带版 298 / 9143 / 3） |

> 性能回归来自孔缘短弧变多（352 路径/格），第一版 `arcs=minWH*1.1` 时 12 格 @u=0.55 掉到 22.5 fps，故收敛到 `minWH*0.62`；`minWH*0.62` 下 29.3 fps 达标。

### 22.4 视觉 QA（临时图，`C:\\Users\\54364\\AppData\\Local\\Temp\\`）
- `qa-one-final.png`：单格 1000×1000 原生渲染，孔缘是密度渐变 + 毛边，无环线
- `qa-mosaic-final.png`：1500×844，16 块，孔缘在整屏尺度读作"丝在孔口堆了一下再淡出"
- 对比：`qa-one-rim.png`（等亮圆环 + SDF 硬圆弧）→ `qa-one-rim2.png`（短弧堆密但 chord 偏直）→ `qa-one-final.png`

### 22.5 未做 / 已知边界
- 孔洞几何导出（`ledGeometryPolys`）仍按完美圆输出，未同步 `ph` 起伏；导出件用于 Rhino/Blender 建模时是有意简化，若要跟像素严格一致需要另加。
- 块群整体密度仍偏“细网”，参考图更接近“密织块”；靠面板 `worms` / `覆盖` 调，不是默认值问题，未改默认。
"""

with io.open(path, "a", encoding="utf-8") as f:
    f.write(sec)
print("appended", os.path.getsize(path), "B")
