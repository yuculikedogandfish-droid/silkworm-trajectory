import io
s = io.open("PROGRESS_WEAVE_2026-11-16.md", encoding="utf-8").read()
s += """

## §45 r39 个体与图层合并 + 组一起挪 + 对齐吸附阵列（2026-11-19）

**问题**：右栏「个体」卡片与「图层」两块重复，操作者要在两处之间来回找；组只是列表分组，拖一块不会带动同组；组关系只在本机缓存里，工程 JSON 带不走。

**做法（仍走"独立模块 + 少量一行钩子"）**
1. 合并面板：`<h3>个体</h3>` + `#habAgents` + `<h3>图层</h3>` 三按钮 + `#habLayerTree` 整段换成「个体与图层」一节：勾选框＋层名（点＝选中并高亮）＋显/隐＋开/锁＋↑↓＋✕，组行带 ▾ 收起、名字、层数、组显隐、改名、解散；`#habAgents` 保留但 `display:none`（`renderList()` 照写，选中仍由它合成 click 触发）。
2. 组关系升级为 `silkworm-habitat-layer-groups/v2`（groups / member / order），暴露 `window.__layerStore{dump,load}`；`exportHabitat()` 加 `layerGroups` 一行、`importHabitat()` 开头挂 `setTimeout(load)`，组随工程 JSON 走。
3. 整组一起挪：模块自带命中（`view()` 反算世界坐标 + 矩形命中），pointerdown 记录基线，移动超过 1.5px 才算拖动；同组成员/多选集合整体跟随；非编辑态才接管（编辑态仍用原生手柄）。
4. 吸附：拖动时按整组外包框对齐**其它块的左/中/右、上/中/下与场地 0 轴**，阈值屏幕 9px，命中即拉齐并画粉色虚线参考线；按住 Ctrl/⌘ 临时关闭。
5. 画布提示：新增 `#habSnapOverlay`（z-index 8，pointer-events:none），选中/全组画青绿虚线外框＋浅填充＋「已选 N 层」。
6. 对齐与批量：`左/横中/右/上/竖中/下`、`水平等距/垂直等距`、`阵列复制`（列×排×缝，复制整块参数＋深拷贝 custom，置 `tileField=false` 后重建）；方向键 1px、Shift 10px；锁定层不响应拖动与方向键（`applyWeaveHandleDrag` 加 `if (a.locked) return;`）。
7. 清掉 r38 的旧图层模块（保留其拖拽上传部分），否则两个模块抢同一个 `#habLayerTree`。

**验收（独立 harness＋整页）**
- 合并列表：4 层 → 勾 3 编组 → 组头 1 + 3 行 + 未编组 1；点组名全选、组眼睛两层同时隐藏（hidden=true/true）。
- 拖动：两块同组，PointerEvent 模拟拖 30/10 → x=-170 与 30 同步位移、y=10；再拖到左缘 -5 → 自动吸附成 0，参考线命中。
- 对齐：三块「左」→ 左缘均为 -100；水平等距 200/200。
- 阵列：3×1 单块后新增 2 块，位置 13:0 / 225:0（间距 12）。
- 锁定后方向键位移 0；✕ 真删（-1 层）。
- 工程 JSON：`export().layerGroups.groups` = 1 组、member 两条；`import` 后组回来。
- 整页截图：右栏「上排两块 2 显 改 ✕」+ 两行「单元 1/2 显 开 ↑ ↓ ✕」+「未编组 1」。

**已知限制**
- 排序只改列表与存储顺序，不改变画布绘制层序；"合并"落地为"并入同组"，不是丝块几何合并。
- 多选靠勾选/组选，尚无框选（marquee）；吸附无等间距引导与角度吸附。
- 组关系进了工程 JSON，但 localStorage 仍保留一份（换机器时以工程文件为准）。
"""
io.open("PROGRESS_WEAVE_2026-11-16.md", "w", encoding="utf-8").write(s)
print("progress ok")
