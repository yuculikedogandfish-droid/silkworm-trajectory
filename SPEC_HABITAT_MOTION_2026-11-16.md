# 蚕室运动控制与无限画布修复（规格存档）

项目：`silkworm-trajectory`
基准文件：`docs/index.html`（本轮改动前 253,657 bytes）
存档日期：2026-11-16
来源：用户转交的外部诊断 + 完整规格，已按本规格实施

## 0. 执行要求

目标：

1. 修复实测蚕点击「开始」后不移动。
2. 每只蚕独立速度倍率。
3. 运动预览可拖分隔线改宽、可放大整屏。
4. Digital Habitat 场地高度可调。
5. Digital Habitat 无限平移 / 滚轮缩放 / 适应场地。
6. 原始轨迹坐标、数据结构、导出功能保持兼容。

禁止：

- 不重写整个页面。
- 不改 `silkworm-preview` 消息协议。
- 不改 `silkworm-habitat/v1` 原有字段含义。
- 不改 `routeWorld` 头→尾、`silk` 尾→头的顺序。
- 不恢复默认随机演示蚕。
- 不改描图器视频分段逻辑。
- 不改首屏 `.screen1 { height: 100vh }`。
- 不加 `type="module"` 或外部依赖。
- 保持三个脚本块原有职责。

## 1. 已确认的两个核心问题

### 1.1 点击「开始」没有实际运动

`habStart` 只把状态改成 `run`，而实测蚕运动分支还要求：

```js
if (agent.follow) {
  agent.u = (agent.u + dt * 0.18) % 1;
  const h = sampleRoute(agent, agent.u);
  agent.x = h.x;
  agent.y = h.y;
}
return;
```

新同步进来的蚕默认 `follow: false`，于是状态变了、位置不动。

修复：点击「开始」时自动让实测蚕沿自己的测量轨迹运动，不再要求用户额外勾选。

### 1.2 蚕室没有独立速度控制

只有温度 / 湿度的环境基础速度，没有逐只速度。

方案：新增速度倍率 0.1×～3.0×，默认 1.00×，逐只独立、运行中即时生效、写入场景 JSON；旧场景缺字段按 1.00× 读取。用倍率而不是改环境公式，避免改变论文原有的演示模型口径。

## 2. CSS 规格

- `:root` 增 `--preview-width: clamp(380px, 48%, 980px)`。
- `#previewFrame` 改 `flex: 0 0 var(--preview-width); min-width: 360px`。
- 新增 `#previewSplitter`（8px、`cursor: col-resize`、`touch-action: none`）。
- `body.preview-off` 同时隐藏 frame 与 splitter；`body.resizing-preview` 改光标并禁选中。
- 1180px 断点：`#previewFrame { flex: 0 0 var(--preview-width, 46%); }`。
- 860px 断点：隐藏 splitter、previewFrame 满宽。
- `body.preview-expanded`：全屏遮罩 + previewFrame 固定 `inset: 5vh 4vw`，放大按钮移到右上角。
- `#habitat` 增 `--hab-stage-height: 780px`，`.hab-stage` / `.hab-world` 的 `min-height` 改用该变量；860px 断点用 `max(var(--hab-stage-height), 70vh)`。
- 新增 `.hab-viewport-tools`、`#habZoomLabel`、`#habWorld.pan-mode|.panning`、`.hab-canvas-size`。

## 3. HTML 规格

- 顶栏 `btnPreviewToggle` 后加 `#btnPreviewExpand`（`onclick="togglePreviewExpand()"`）。
- `</main>` 与 `#previewFrame` 之间插 `#previewSplitter`（`role="separator"`、`aria-orientation="vertical"`、`tabindex="0"`）。
- `habSyncStat` 后加 `.hab-canvas-size`：`#habCanvasHeight` + `#habCanvasHeightVal`。
- 五个 canvas 后加 `.hab-viewport-tools`：`#habZoomOut` / `#habZoomLabel` / `#habZoomIn` / `#habFitView` / `#habPanToggle`。
- 右侧「选中调整」缩放滑杆后加 `#habAdjSpeed` + `#habAdjSpeedVal`。

## 4. JavaScript：运动控制

- `makeRandomDemo()` 与 `syncMeasured()` 新建个体都带 `speedScale: 1`；再次同步不覆盖用户已设值。
- `syncRoutePanel()`：无选中置 1.00× 并纳入禁用列表；有选中按 `Number.isFinite(a.speedScale) ? a.speedScale : 1` 回填，速度对两种个体都开放。
- `bindRoutePanel()`：`habAdjSpeed` 的 `input` 绑定，clamp 0.1–3。
- `step(dt)`：
  - 实测蚕 `agent.u` 按 `dt * 0.18 * speedScale` 推进，`heading` 由 `u + 0.002` 反推。
  - 随机蚕 `actualSpeed = env.speed * speedScale`。
- `habStart`：筛选非 `bench` / `drag` 且 route ≥ 2 点的个体 → 实测蚕 `follow = true`（`u` 不合法补 0）→ `mode = run`；无可用个体时 toast + hint 提示先拖入场地。

## 5. JavaScript：无限画布

- `habViewport = { zoom: 1, panX: 0, panY: 0, panMode: false }`。
- `view()`：`s = baseScale * zoom`、`cx = w/2 + panX`、`cy = h/2 + panY`，`px/py` 用 cx/cy。
- `screenToHab()`：`(sx - v.cx) / v.s`（缩放平移后鼠标定位仍正确）。
- `zoomAt(sx, sy, factor)`：以鼠标点为缩放中心，zoom clamp 0.12–8，反算 pan 补偿。
- `resetHabView()` 回 100% 居中；`updateHabZoomLabel()` 刷百分比。
- `world` 的 `wheel`（`passive: false`）缩放 + 阻止页面滚动。
- 工具栏：`±` 以场地中心 1.2 倍缩放、`habFitView` 复位、`habPanToggle` 切换平移模式（同步 `#habWorld.pan-mode`）。
- `pointerdown` 最前插 `button === 1 || shiftKey || panMode` 的 pan 分支；`pointermove` 处理 pan 位移；`pointerup` 只收尾 pan，不误入蚕的拖动逻辑。

## 6. 场地高度与分隔线

- `#habCanvasHeight` 的 `input`：clamp 640–1400，写 `--hab-stage-height`，更新标签，调 `repaintStaticLayers()`。
- `ResizeObserver` 观察 `habWorldWrap`，尺寸变化时重绘静态层。
- `bindPreviewResizer()`：拖分隔线按 `--preview-width` 改宽（360–1100 与容器约束取交集）、双击复位 48%、左右方向键 ±32px；`applyPanelState()` 后调用。

## 7. 持久化

`habSave`、`exportHabitat()`、`importHabitat()` 三处都写 / 读 `speedScale`：

- 写出：`Number.isFinite(a.speedScale) ? a.speedScale : 1`
- 载入：`Number.isFinite(a.speedScale) ? Math.max(0.1, Math.min(3, a.speedScale)) : 1`

旧版 JSON 缺字段回落 1，不得导致旧场景无法载入。

## 8. 验收清单

A 代码检查：标签闭合、媒体查询顺序、拆分三个脚本块、srcdoc 先实体解码、外层 JS 逐个 `node --check`、新增 ID 不重复、事件绑定 DOM 存在。

B 蚕室运动：实测蚕自动进蚕室 → 拖入 → 开始即沿轨迹运动（无需再勾选）→ 暂停 / 继续 → 0.1/1/2/3× 生效 → 两只不同速 → 运行中调滑杆即时生效。

C 无限画布：滚轮缩放且以鼠标为中心、平移开关、平移后鼠标定位仍准、桑叶仍能放、卡片拖入仍正常、适应场地复位、缩放平移不改轨迹数据、碰撞边界仍有效。

D 预览尺寸：拖分隔线改宽、双击复位、放大整屏、退出回双栏、预览内部不错位、860px 以下纵向堆叠。

E 数据兼容：旧描图器 JSON、旧蚕室 JSON、新蚕室 JSON 保留速度、重开速度一致；SVG/CSV/DXF/OBJ/glTF/运动模型导出无回归；`silk` 仍尾→头、`routeWorld` 仍头→尾。

## 9. 交付要求

备份到 `_backup/`；`docs/index.html` 为运行时真源，同步两份 editor 副本并 SHA256 校验；输出函数清单与验收报告。

建议版本名：`index-vNext-20261116-habitat-motion-infinite-canvas.html`

## 附：实际实施与本规格的差异（本轮由主 Agent 直接实现）

1. **`safeUnit` 作用域 bug（新发现，已修）**：蚕室脚本块调用 `safeUnit`，但该函数定义在主描图器脚本块内，运行时报
   `Uncaught ReferenceError: safeUnit is not defined @drawHabitatWorm`，导致每帧蚕体绘制中断——画面上只有丝、没有蚕。
   修复：在蚕室 IIFE 内补一份本地 `safeUnit`（与主脚本同算法），不跨块依赖。
2. **实测蚕沿途留丝（新发现，已补）**：原实现只把 `x/y` 挪到采样点，`silk` 一直为空，视觉上没有“正在吐丝”的过程。
   现按 >2.5 间距把采样点 append 进 `silk`（上限 4000），并在 `paintWorld` 以 0.06 alpha 画 `route` 作为淡色底轨。
3. **场地高度滑杆步进**：规格写 `step=40`，但 `780` 不在 640+40k 网格上，浏览器会把默认值吸附成 `800`。
   实际改为 `step=20`，保证 780 合法。
4. **放大预览与收起联动**：收起运动预览时同时移除 `preview-expanded` 并复位放大按钮文案，避免“隐藏后仍处于放大状态”。
