# -*- coding: utf-8 -*-
import io, datetime
P = r"H:\tool\silkworm-trajectory\PROGRESS_WEAVE_2026-11-16.md"
S31 = """

## §31 r23 多格复用 + 格内丝迹夹取（2026-11-17）

### 31.1 做了什么
1. **一种蚕可跨格复用**：`spawnCellWorm(unit, wid, x, y)` 按 `rt-<wid>@<unitId>` 生成独立实例；`assignWormToUnit(unitId, val)` 支持单选或「全部蚕（每种一只）」。指定某格用哪只蚕时，**不会**从别的格摘除或删除。
2. **起点不规律**：实例带随机 `rot`(±0.85rad)/`scale`(0.78–1.06)/`phase`/`turnSign`/`homePhase`；`roamPoint` 的 cell 分支改双频正弦 + 慢漂移（`cos(t*1.55+ph)`、`sin(t*1.22+ph*1.3)` 叠 `sin(t*0.27..)/cos(t*0.19..)`），避免一格内踩出等间距的一排八字。
3. **丝迹夹在格内**：新增 `drawSilkInRect(ctx, pts, v, alpha, unit)`，逐点把坐标夹到 `unit` 矩形 (0.98 内缩) 再画。route 分支不再依赖 canvas `ctx.clip()`（实测对丝迹无效），改为：
   - `kind==='route'` → 有 unit 就 `drawSilkInRect`，没有才 `drawSilk`；
   - 删掉历史遗留的 `drawSilk(ctx, agent.route, v, 0.06)`——`agent.route` 是局部 ±55 归一化坐标，当世界坐标画会生成幽灵长线（这是 r22 遗留的"场地里到处是长丝"根因之一）；
   - 分支条件从 `route.length>1` 放宽为 `kind==='route'`，route 为空但有 silk 的实例也走夹取路径，不再落进无裁剪的 `else`。
4. `syncMeasured` 只更新源头实例 `rt-<wid>`，保留 `@<unit>` 克隆的全部本地位姿。

### 31.2 实测
- `probe_r23b.py`：两格各得 `rt-1@wv-1` / `rt-1@wv-2`，源蚕仍在；重抽起点都在格内；`seek(5)` 后两格各 100 点丝。
- `probe_r23_px2.py`（画布像素采样）：两格分离（x=-160 / 170，280×280）时，格右侧 28px 竖带的亮像素 1084 / 360，与关掉织网（`u=0`）时完全一致 → 该亮度来自场地格线（`rgba(210,220,214,0.10)`，40 世界单位一条），不是丝迹溢出。
- 截图 `qa-r23-final.png`：右格丝迹完整收在格框内。

### 31.3 结论与遗留
- 场地级"到处长丝"已定位为**两条**：幽灵 `agent.route` 世界坐标画线（已删）+ 无裁剪 `else` 分支（已改夹取）。逐点夹取是确定性手段，不依赖 clip 语义。
- 遗留：一格内多蚕仍是"各自爬各自留丝"，没有共享同一份丝路编排；块群批量指定"这块用蚕 A、那块用蚕 B"未做；形状编辑（编辑对象/操作方式/直播预览）仍未按多边形建模式重做——排入 r24。
- 本轮文件：`docs/index.html` 400,797 B / SHA `8F387D4C8D9A139E0D412E3E3866A9E0093A126A75725D121C29FECB8D11D3E4`，三副本一致。
"""
with io.open(P, "a", encoding="utf-8") as f:
    f.write(S31)
print("ok")
