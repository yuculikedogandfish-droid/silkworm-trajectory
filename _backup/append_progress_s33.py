# -*- coding: utf-8 -*-
import io
P = r"H:\tool\silkworm-trajectory\PROGRESS_WEAVE_2026-11-16.md"
S = """

## §33 r25 形状编辑按「包围盒」重做（拖角点 / 拖边中点）（2026-11-17）

### 33.1 交互定义（面向不懂程序的人）
进入编辑后，这一格四周出现两种手柄，语义和建模软件一致：
- **四角橙方点**：拖角改整块大小，对角钉住不动。
- **四条边中点橙短条**：只改被拖的那一条边（拖左边只动左边界，拖上边只动上边界），另一侧钉死。
- **中间橙十字**：整块挪位置。
- **青色实点 / 青色空心圈**：挪孔洞 / 改孔洞半径；孔洞虚线圆上直接标 `∅ n px`。
- 鼠标悬停手柄时浮出白话标签（`拖：只改这一边` 等）；**拖角或拖边时块上方实时报 `宽 × 高 像素`**。
- 命中半径从 10 px 放宽到 14 px，小屏也好抓。

### 33.2 预览不入成品（结构性保证，非约定）
- 编辑辅助只画在 `drawEditLivePreview()` / `drawWeaveHandles()`，二者只在 `paintWorld()`（屏幕）里调用。
- 导出/母版路径 `ledComposeFrame()` 只调用 `drawWeave(g, agent, v)`，从不调用手柄或预览函数。
- 底部提示条显式写：`虚线框和手柄只是编辑辅助，不会出现在成品图或导出的视频里`。

### 33.3 新增/改动函数清单
| 函数 | 改动 |
| --- | --- |
| `weaveHandles(a, ix, iy)` | 新增 4 个 `unitEdge` 手柄（l/r/t/b）；`want()` 里把 `unitCorner/unitEdge/unitMove` 设为任何工具栏下都可用 |
| `applyWeaveHandleDrag(h, p)` | 新增 `unitEdge` 分支：只改 w 或只改 h，对面边固定；改完清 cache 并 `buildWeave` |
| `drawWeaveHandles(ctx, a, v)` | 新增 `unitEdge` 短粗条绘制；拖动时在块上方实时绘制 `宽 × 高` 读数 |
| `WEAVE_HANDLE_LABEL` | 加 `unitEdge: '拖：只改这一边'` |
| `WT_HINT.shape` | 改为「拖四角＝改整块大小 · 拖四条边中点＝只改宽或只改高 · 拖中间十字＝整块挪位 · 拖青点/青圈＝挪孔/改孔径」 |
| 命中判定（pointerdown） | 容差 `10 / v.s` → `14 / v.s` |

### 33.4 验收
- `node --check` outer_1 通过（`check_index_scripts.py` 拆三段，total 3）。
- `qa-r25-edit.png`：进入编辑的格子四角 + 四边中点手柄齐备，孔洞虚线圆 + `∅109 px`，底部提示条与状态栏同时说明「现在在改哪一块、拖什么会怎样、预览不入成品」。
- 遗留：`unitEdge` 只对矩形单元生效；多边形（`a.outline` 顶点）仍走 `outlineV` 白点。下一步把边中点也做进多边形每条边。
"""
with io.open(P, "a", encoding="utf-8") as f:
    f.write(S)
print("ok")
