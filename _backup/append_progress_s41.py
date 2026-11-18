# -*- coding: utf-8 -*-
s = r"""

## §41 · r33 —— 右键不再"直接删"，改成菜单里给「删除这个锚点 / 删除整个缺口」

**用户口径**：鼠标压在缺口某个锚点上点右键，应该能选"删这个锚点"或"删整个缺口"，而不是一按就删。

**改动**
- `contextmenu` 里删掉了"先 `weaveDeleteAt` 直接删"的行，改成先算命中目标（`weaveHandles` + 优先级权重 + 16 px 容差），
  再把"删什么"变成菜单项，跟原来的通用项拼在一起：
  - 压在 `notchV`（缺口锚点）→ 前两项「删除这个锚点」「删除整个缺口」；
  - 压在 `notchMove/notchR`（圆缺口）→ 「删除整个缺口」；
  - 压在 `islandMove/islandR`（孔）→ 「删除这个孔」；
  - 压在 `wallV/pathV/outlineV/outlineMid` → 「删除这个锚点」；
  - 压空白 → 只有 6 个通用项（开孔 / 重画缺口 / 起笔壁 / 起笔丝路 / 清本格形状 / 退出编辑）。
- 新增闭包内 `deleteWholeNotch()`、`deleteIsland(i)`；删锚点仍复用 `deleteWeaveHandleVertex`（≤3 点时自动整圈删）。
- 文案同步：`syncEditNote` 的提示与 `WT_HINT.notch` 都改成"右键＝菜单，压在锚点时会给出删除项"。

**验收（无头 Chrome 1600×1000，独立 profile，`qa-r33-vertex.png`）**
- 编辑态、缺口 6 个控制点；
- 右键压在 `(-240,-90)` 这个锚点上 → 菜单 **8 项**，前两项 = 「删除这个锚点 / 删除整个缺口」；
- 点第一项之后：顶点 **6 → 5**，菜单关闭（`display=none`）。
- 三段 `node --check` 全 OK。

**没改的**：Alt+左键点顶点仍然直接删（这是老快捷键，保留）；右栏「这一笔收尾 / 重画缺口」照旧。
"""
p = r"PROGRESS_WEAVE_2026-11-16.md"
open(p, "a", encoding="utf-8").write(s)
print("progress s41 appended")
