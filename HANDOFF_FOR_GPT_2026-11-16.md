# 蚕轨迹描图器 · 交接文档（2026-11-16）

> 读者：接手继续开发的下一位工程师 / GPT。
> 目的：让你在不读完全部历史的前提下，准确知道**现在的程序长什么样、数据怎么流、哪些地方别动、接下来该做什么**。
> 唯一的运行时真源是 `docs/index.html`（单文件，253 KB 左右，纯原生 JS，无构建、无外部依赖）。

---

## 1. 项目定位（论文语境，先读这段再改代码）

- 论文题目：《手绘曲线的三维化：面向数字概念资产的草模工具研究》，中国美术学院创新设计学院硕士。
- 研究范式：RtD（Research through Design），实体装置 + 数字工具双轨。
- 本工具在论文里的角色：**「自然主体绘制曲线 → 数字概念资产草模」** 的第一段。用户（研究者）在顶视视频里手工描出蚕的吐丝轨迹，工具把这条"手绘曲线"转成可参数化的数字资产（u ∈ [0,1] 的弧长参数曲线），再导出到 Rhino / Blender / TouchDesigner / p5.js 继续造型。
- 方法论上的取舍（**已被实验否决，不要再回头做**）：
  - 顶视单机位只能得到 2D 轨迹，没有高度信息；
  - 自动追踪（蚕体 blob 追踪、丝差分 + 骨架化、经典多目标追踪）在真实 77.3 s 视频上产出"一坨碎片"，用户明确否决；
  - 视觉大模型逐帧读坐标又慢又不准。
  - 因此主流程固化为**手动描线 + 参数化导出**。`tracking/` 里的 Python 脚本只是失败对照，不要当成可用能力去接。
- 一句话原则：**工具的可信度来自「人描的线」和「参数可复算」，不来自"看起来像真的"的自动生成。**

---

## 2. 运行方式

| 场景 | 做法 |
| --- | --- |
| 本地使用 | 直接用浏览器打开 `docs/index.html`（`file://` 可用，无需服务器） |
| 线上 | GitHub Pages：<https://yuculikedogandfish-droid.github.io/silkworm-trajectory/> |
| 仓库 | <https://github.com/yuculikedogandfish-droid/silkworm-trajectory> |

约束（务必遵守）：

1. **无构建、无框架、无 `type="module"`**。改完直接刷新浏览器可见。
2. 视频在浏览器本地解码，不上传。
3. `docs/index.html` 里有**三个 `<script>` 块，语义完全不同**：
   - `srcdoc` 内的 1 个：右侧「吐丝运动预览」iframe 的独立页面（自己一套状态，与父页只靠 `postMessage` 通信）；
   - 外层第 1 个：Digital Habitat 蚕室（`window.__studioHabitat` 是它暴露的接口）；
   - 外层第 2 个：描图器主逻辑（`state.worms`、导出、`gotoHabitat()` 都在这里）。
   **不要跨块改同名概念**（例如两处都有"预览"，含义不同）。

---

## 3. 页面结构（2026-11-16 版布局，这是本次改动的核心）

```
body
└── div.screen1                 ← 高度硬约束：100vh / min-height 560px，flex 纵向
    ├── header                  ← 顶栏，15 个按钮，允许换行
    └── div.workspace           ← flex: 1 1 auto; min-height: 0（不再用 calc(100vh - 52px)）
        ├── div.panes           ← 左 main（视频 + canvas 描图）/ 右 iframe#previewFrame（运动预览）
        └── div.transport       ← 播放 / 上帧 / 下帧 / 时间 / 进度条，固定在首屏底部
p.scroll-cue                    ← "↓ 向下进入 Digital Habitat（整屏蚕室）"，可点击滚动
section#habitat                 ← 一整块全宽蚕室，不再嵌在 iframe 或右侧栏里
├── div.hab-top                 ← 标题 + 模型免责说明 + habSyncStat（实测 N 只 · 演示 N 只）+ 两个侧栏开关
├── div.hab-stage               ← grid: 250px | 1fr | 270px
│   ├── aside#habLeft            ← 环境：温湿度、场地形状、桑叶障碍、同步入口、保存
│   ├── div#habWorldWrap         ← 场地：habBg / habLeaves / habMist / habWorld / habDepth 五层 canvas
│   └── aside#habRight           ← 个体列表（可拖卡片）+ 选中调整滑杆 + 操作按钮
└── div.hab-time                ← 开始 / 暂停 / 继续 / 模拟时钟 / #habHint 提示行
div#habGhost                     ← 拖拽跟随的提示气泡（position: fixed）
div#habToast                     ← 成功/失败提示条（.ok / .err）
```

要点：

- **首屏必须正好一屏**：`.screen1` 高度 100vh，`.workspace` 用 `flex: 1 1 auto` 吃掉顶栏之外的空间。**不要改回 `height: calc(100vh - 52px)`**——顶栏 15 个按钮会换行，52px 是错的，运输条会被挤出屏幕（这是上一版真实踩过的坑）。
- 蚕室左右面板属于**蚕室自己**，不是运动预览的侧栏。`#habLeft` / `#habRight` 在 `section#habitat` 内部。
- 侧栏收展靠 `.hab-stage.left-off / .right-off` 改 `grid-template-columns`（`250px 1fr 270px` → `1fr 270px` → `250px 1fr` → `1fr`）。
- 断点：
  - `@media (max-width: 1180px)`：预览面板变 46%；
  - `@media (max-width: 860px)`：`.panes` 纵向堆叠、`.hab-stage` 单列、两侧栏变成覆盖式抽屉（`display: none` + `.open` 才显示）。
- 蚕室场地 `min-height: max(640px, calc(100vh - 130px))`，保证滚动进来时是"整屏"的体量感。

---

## 4. 三块面板的数据流（这是最容易改错的地方）

```
【描图器】state.worms = { [wormId]: { color, points:[{x,y,t}], ... } }
      │
      ├─(A)→ buildPreviewPayload() ──postMessage──→ iframe#previewFrame 的预览脚本
      │                                               （预览里再算速度/朝向/身体 ribbon）
      │
      └─(B)→ buildPreviewPayload().trajectories
                 ↘
                   window.__previewTrajs（预览回传的消息缓存，更"新鲜"）
                 ↘
                   measuredSource()   ← 优先 __previewTrajs，回退 payload，再回退 []
                        ↓
                   syncMeasured()      ← 蚕室唯一入口
                        ↓
                   habitat.agents 里 kind:'route' 的个体
```

关键实现细节（按名字检索，不要按行号）：

- `buildPreviewPayload()`（描图器块）：把 `state.worms` 转成 `trajectories`，带 `wormId / color / points[{x,y,t}]`。
- `onPreviewTrajData()`（描图器块）：监听 `silkworm-preview/data`，把有效轨迹（≥2 点）写进 `window.__previewTrajs`。
- `measuredSource()`（蚕室块）：优先 `window.__previewTrajs`；没有就现场调 `buildPreviewPayload()`；都没有返回 `[]`。
- `syncMeasured()`（蚕室块）：
  - 过滤非法点，丢弃点数 < 2 的轨迹；
  - `wormId` 缺省时用序号；
  - `normalizeRoute(raw)`：等比缩放 + 居中，**固定归一化到 110 单位**（写在函数里，未暴露给用户）；
  - 按 `wormId` 合并：已存在的 `kind:'route'` 个体只**刷新 `route`**，保留用户已调的 `offX / offY / rot / scale / follow / u`；`mode` 若是 `bench / drag` 则退回 `idle`；
  - 新个体水平错开 `(order - (n-1)/2) * 26`；
  - 删除磁盘上已不存在的 `wormId` 对应个体；
  - 返回同步成功的条数（用于 toast 文案）。
- `applyRouteTransform(agent)`：由 `route` + `offX/offY/rot/scale` 生成 `routeWorld`（**正序：头→尾**，用于渲染轨迹线）和 `silk`（**逆序：尾→头**，身体重建与吐丝依赖这个顺序）。**改任何一处顺序都要同步另一处**，否则蚕会"倒着长"。
- 自动同步：`IntersectionObserver` 观察 `section#habitat`，滚动进来（阈值 0.2）自动 `syncMeasured()` 一次，800 ms 内节流。

### 为什么不保留"随机演示蚕"作为默认个体

上一版有 `sw-1 / sw-2 / sw-3` 三个 bench 状态的随机个体，用户看到后明确否决："Digital Habitat 这里的蚕应该是我在描图器和吐丝运动预览中的蚕，也就是有实际数据的蚕"。现在：

- `spawnBench()` 已删除；随机蚕改为用户主动点「添加随机演示蚕」才出现（`makeRandomDemo()`），列表里标 `演示`；
- 实测个体由 `syncMeasured()` 自动出现，标 `实测`，显示名统一为「蚕 N」；
- 列表为空时给文案「暂无个体：描好的蚕会自动出现在这里；也可添加随机演示蚕」。

**不要把默认随机蚕加回来。**

---

## 5. 数据结构

### 5.1 描图器 `state`（节选，完整字段见脚本顶部）

```js
state = {
  video, canvas, ctx, mode,               // mode: null | 'origin' | 'scale'
  cal: { ox, oy, scale, p1 },              // 像素 → mm 标定
  worms: { [id]: { color, points:[{x,y,t}] } },
  activeId, segments, segmentIndex,
  videoFps, videoReady, maxWormTab,
  bridge: { enabled, tension },
  regionDrag, boxDrag, editHistory, _trajCache, _draw, uPlay
}
```

### 5.2 蚕室 `habitat`

```js
habitat = {
  shape, tempC, humidity, seed, simTime,
  tool,            // 'worm' | 'leaf'
  selected, selectedLeaf,
  agents: [], orphans: [], obstacles: [], reference: null,
  undo: [], drag: null, mistPhase
}
```

`reference` 是「铺入只读预览轨迹」的淡底图（不可操作），与 `kind:'route'` 的可操作个体是**两回事**，别混。

### 5.3 `agent` 字段与状态机

```js
{
  id, kind: 'route' | 'random',
  wormId,                          // 仅 route
  mode: 'bench' | 'idle' | 'drag' | 'run' | 'paused',
  bodyVisible,
  x, y, heading, silk: [],         // silk 为尾→头顺序的点列
  route: [{x,y}],                  // 归一化后的轨迹（仅 route）
  offX, offY, rot, scale, follow, u,
  color, phase, turnSign, pauseUntil
}
```

状态流转：`bench`（未放入场地）→ 拖卡片松手 → `idle` / 拖到场地内 → `drag` → `idle`；`run` ↔ `paused` 由播放控制与 `blocked()` 决定。`bench` 的个体不参与碰撞、不累积丝。

### 5.4 导出

- 描图器：`SVG` / `JSON`（工程）/ `CSV` / `3D曲线`（`curves3d/v2`，含标定与 u）/ `DXF` / `OBJ` / `glTF` / `运动模型`（`silkworm-motion-model/v2`）。
- 蚕室：`保存场景 JSON` → `exportHabitat()`，`type: 'silkworm-habitat/v1'`，含 `modelVersion: 'habitat-demo-0.1'`、`disclaimer`（温湿度映射为演示模型）、场地、障碍、`orphanSilk`、`reference`、全部 agent 字段。
- 兼容注意：旧的 v1 工程文件仍要能打开（见 `docs/SCHEMA_MIGRATION.md`）；未标定时 3D / DXF / OBJ / glTF / CSV / 运动模型会被 UI 拦截。

---

## 6. 交互与反馈（本轮已落地，验收时逐条点）

1. **进入蚕室**：顶栏「进入 Digital Habitat」→ `gotoHabitat()`：平滑滚到 `#habitat` + 立刻 `syncMeasured()` + toast（成功 `.ok` / 无数据 `.err`）。`scroll-cue` 也可点击滚动。
2. **侧栏开合**：
   - 按钮 `#habOpenLeft` / `#habOpenRight`，文案在「收起环境 / 展开环境」「收起个体 / 展开个体」之间切换；
   - 展开态按钮加 `.on`（填充底色），`aria-pressed` 同步；
   - 每次切换都写 `#habHint`（面板已展开/收起）+ toast；
   - 窄屏（≤860px）下是覆盖式抽屉，`.open` 控制显示。
3. **拖拽放入的三种实时反馈**：
   - 拖动时跟随指针的 `#habGhost` 气泡：`松手放到「蚕 N」处`（可放，绿框） / `这里被桑叶或边界挡住`（不可放，红框） / `拖到场地里松手`（还在场外）；
   - 场地边框：可放时 `.drop-ready`（绿色虚线内框），不可放时 `.drop-fail`（红色虚线内框）；
   - 松手：成功 → `.ok` toast「「蚕 N」已放到该处。」；场外 → `.err` toast「没有放到场地里，…保持原位。」；被挡 → `.err` toast「放不进去：该处被桑叶或场地边界占用…」；
   - 卡片本身有 `cursor: grab/grabbing` 和「按住拖到场地放入 / 可拖动改位置」小字提示。
4. **场地内拖动个体**：`kind:'agent'` 那套，移动后 hint 提示"右侧滑杆可精确微调"。
5. **选中调整面板**：位置 X/Y、旋转、缩放、沿轨迹爬行、居中复位、移除。非 route 个体（演示蚕）旋转/缩放/跟爬被禁用，并用 CSS 降透明度 + `not-allowed` 光标提示。
6. **其余**：撤销上一步破坏（`pushUndo`，最多 24 步）、隐藏/显示蚕体、移除蚕保留丝、移除蚕清除丝。

---

## 7. 本次（2026-11-16）实际改动清单

| # | 改动 | 说明 |
| --- | --- | --- |
| 1 | 蚕室从 `srcdoc` 整体迁出到外层文档 | 见 `_backup/restructure_habitat.py`；备份 `index-v2-20261116-before-restructure.html` |
| 2 | 运输条位置修正 | 见 `_backup/fix_transport_order.py`；备份 `index-v3-20261116-before-transport-fix.html` |
| 3 | 实测个体自动同步、默认随机蚕移除 | `syncMeasured()` / `makeRandomDemo()` / `renderList()` |
| 4 | 蚕室自有左右侧栏 + 收展反馈 | `togglePanel()` / `applyPanelState()` / `.on` 态 / toast |
| 5 | 拖拽幽灵 + 落点虚线框 + 成功失败 toast | `updateGhost()` / `clearGhost()` / `window.pointerup`（`kind:'card'`） |
| 6 | 首屏硬约束 `.screen1 { height: 100vh }` | 移除 `calc(100vh - 52px)`；`.workspace` 改 `flex: 1 1 auto; min-height: 0` |
| 7 | 勾选框状态 bug 修复 | 新增 `panelCheck()`：原来用 `.value` 赋值，「沿实测轨迹爬行」的勾选状态永远不刷新 |
| 8 | 禁用控件与拖拽卡片的视觉反馈 | `:disabled` 降透明 + `not-allowed`；卡片 `grab/grabbing` + 拖拽小字 |

校验方式（改完必跑）：

```powershell
python H:\tool\silkworm-trajectory\_backup\check_screen1.py   # div 平衡 89/89、screen1/section/script 计数
python H:\tool\silkworm-trajectory\_backup\dump_js2.py        # 拆分 srcdoc 内 / 外层脚本为文件
# 再逐个 node --check（srcdoc 内脚本必须已 html.unescape，否则 &amp;&amp; 会误报语法错误）
```

---

## 8. 已知缺口 / 建议后续（给接手者的任务池，按优先级）

1. **场地形状切换的回迁策略未与用户确认**：正方/长方/圆切换后，只在 `blocked()` 成立时把非 bench 个体置 `paused`，没有把它们挪回边界内。建议：切换时对越界个体做一次最近边界投影 + toast 说明。
2. **归一化尺度写死 110 单位**：论文里需要交代"轨迹尺寸 vs 场地尺度"的口径，建议在右侧「选中调整」下加「轨迹尺寸」滑杆，或在左侧环境面板加"场地尺度"输入，并把该值写进场景 JSON。
3. **蚕室没有独立的「载入场景 JSON」入口**：`importHabitat` 已实现并挂在 `window.__studioHabitat`，也有 `silkworm-habitat/import` 消息通路，但蚕室面板只有「保存场景 JSON」。补一个按钮 + `<input type="file" accept=".json">` 即可闭合。
4. **触摸端未实测**：拖拽用的是 Pointer Events，理论上手机可用，但侧栏抽屉 + 长按拖拽在小屏上需要真机验收。
5. **多蚕性能**：每只蚕的 `route` 可能有 2000+ 点，`habWorld` 每帧全量重绘。建议按 `devicePixelRatio` 分档降采样，或对静态轨迹层缓存为离屏 canvas。
6. **温湿度模型仍标 `habitat-demo-0.1`**：只是演示映射，不要在任何论文结论里当实测规律引用；若要做真实模型，需另立数据来源与拟合记录。
7. **导出通道**：glTF 已可用，但 TouchDesigner / p5.js 只有曲线 JSON 口径，没有配套加载脚本；论文若要用 p5 演示，需要补一个最小示例（仓库已有 `examples/touchdesigner/README.md` 可作参照）。

---

## 9. 修改守则（破坏其中任何一条都会让程序退步）

1. **三份副本必须字节一致**（部署用 `docs/index.html`，`editor/` 两份是分发副本）：
   ```powershell
   Copy-Item -LiteralPath "H:\tool\silkworm-trajectory\docs\index.html" -Destination "H:\tool\silkworm-trajectory\editor\silkworm-tracer.html" -Force
   Copy-Item -LiteralPath "H:\tool\silkworm-trajectory\docs\index.html" -Destination "H:\tool\silkworm-trajectory\editor\蚕轨迹描图器.html" -Force
   ```
   改完用 `Get-FileHash -Algorithm SHA256` 核对三者一致。
2. **改文件前先备份到 `_backup/`**（命名为 `index-vN-日期-说明.html`），不要在原件上直接破坏性修改。
3. **`srcdoc` 内的 JS 是 HTML 转义文本**：校验前必须 `html.unescape`，否则 `&amp;&amp;` 会被 node 判为语法错误（这是误报，不是真 bug）。
4. **`silk` 是尾→头**，`routeWorld` 是头→尾。改渲染前先确认自己在哪一层。
5. **别动导出 schema 的既有字段名**；新增字段向后兼容，旧工程 JSON 必须还能打开。
6. **别恢复随机演示蚕为默认**（用户已明确否决）。
7. CSS 断点顺序别打乱：`@media (max-width: 1180px)` 在 `860px` 之前，否则窄屏抽屉会被覆盖。
8. 中文文案口径统一：蚕室叫「Digital Habitat / 蚕室」；个体标「实测 / 演示」；面板叫「环境 / 个体」。

---

## 10. 手工验收清单（打开 `docs/index.html` 逐条点）

- [ ] 首屏正好一屏：左边描图器、右边运动预览，底边能看到播放/进度条，不需要滚动。
- [ ] 顶栏点「进入 Digital Habitat」→ 页面平滑滚到蚕室，并弹出「已同步 N 条实测轨迹」。
- [ ] 蚕室左右面板确实在蚕室内部（左「气候·场地·桑叶·同步·记录」、右「个体·选中调整·操作」）。
- [ ] 点「收起环境」→ 左栏消失、按钮变「展开环境」且底色填充、顶部 hint 与 toast 都有提示；再点回来。
- [ ] 右侧个体列表里，描过线的蚕显示「实测 · 蚕 N」；空列表显示"暂无个体"。
- [ ] 按住「蚕 N」卡片拖到场地：拖动时出现跟随气泡，场地内出现绿色虚线框，松手出绿色成功 toast。
- [ ] 把卡片拖到桑叶上松手：红框 + 红色失败 toast + 位置不变。
- [ ] 选中实测蚕，拖「旋转/缩放」滑杆，场地里的蚕与轨迹同步变化；勾「沿实测轨迹爬行」后勾选态能保持。
- [ ] 选演示蚕（点「添加随机演示蚕」）时，旋转/缩放滑杆变灰不可用。
- [ ] 改变窗口宽度到 860px 以下：预览面板堆到下方，蚕室两侧栏变成可开合抽屉。

---

## 11. 建议给 GPT 的提示词（可直接复用）

> 你会收到一个单文件前端工具 `docs/index.html`（约 253 KB，纯原生 JS，无构建）。它有三块面板：左侧描图器、右侧吐丝运动预览（iframe srcdoc）、下方全宽 Digital Habitat 蚕室。请先读交接文档 `HANDOFF_FOR_GPT_2026-11-16.md`，再按其中"页面结构 / 数据流 / 修改守则"三节定位代码。本轮任务是：<你的具体任务>。要求：只改 `docs/index.html` 一个文件；改动前把当前版本备份到 `_backup/`；不改变导出 schema 的既有字段；改完把文件同步给 `editor/` 两份副本并保证 SHA256 一致；输出一份改动点清单（函数名 + 行为变化 + 验收步骤）。

---

## 12. 交付文件清单见 `FILES_TO_GPT_2026-11-16.md`
