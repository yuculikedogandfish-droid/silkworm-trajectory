# 交接：蚕室运动控制 / 无限画布 / 预览分栏（2026-11-16）

## 一、这一轮改了什么

运行时真源：`H:\tool\silkworm-trajectory\docs\index.html`
本轮完成后：265,678 B，SHA256 `571CA085C60AA5273C16EC9173BCC43B7059EE7838504C904124F6770A7CBE39`
两份 editor 副本已同步，四份（含 `_backup` 快照）字节一致。

### 1. 两个真 bug

| 问题 | 根因 | 修法 |
| --- | --- | --- |
| 实测蚕拖进场地后点「开始」不动 | `habStart` 只改 `mode = 'run'`，实测蚕分支还要求 `agent.follow === true`，新同步个体默认 `false` | `habStart` 重写：过滤非 `bench`/`drag` 且有 ≥2 点 route 的个体，实测蚕自动 `follow = true`（`u` 非法补 0），再置 `run`；无个体时 toast + hint |
| 画面上只有丝、看不到蚕 | 蚕室脚本块调用 `safeUnit`，该函数定义在主描图器脚本块作用域内 → 每帧 `drawHabitatWorm` 抛 `ReferenceError`，绘制中断 | 在蚕室 IIFE 内补本地 `safeUnit`（同算法），不跨脚本块依赖 |

### 2. 新增能力

- **逐只速度倍率**：`#habAdjSpeed`（0.1–3，step 0.05），实测蚕与演示蚕都可用，运行中即时生效；`habSave` / `exportHabitat` / `importHabitat` 三处持久化，旧 JSON 缺字段回落 1。
- **预览分栏**：`#previewSplitter` 拖拽改 `--preview-width`（360–1100 与容器取交集）、双击复位 48%、方向键 ±32px；`#btnPreviewExpand` 整屏放大，收起预览时联动退出放大。
- **场地高度**：`#habCanvasHeight`（640–1400，**step 20**）写 `--hab-stage-height`，触发 `repaintStaticLayers()`；`ResizeObserver` 观察 `habWorldWrap`。
- **无限画布**：`habViewport{zoom,panX,panY,panMode}`、`view()` 带 cx/cy、`screenToHab()` 用逆变换、`zoomAt()` 以鼠标为中心（zoom 0.12–8）、滚轮缩放、`−/＋/适应场地/平移画布` 四按钮、中键 / Shift / 平移模式下拖动 pan。
- **实测蚕留丝**：`step()` 里按 >2.5 间距把采样点 append 进 `silk`（上限 4000），`paintWorld` 以 0.06 alpha 画 `route` 淡底轨，蚕体朝向由 `sampleRoute(u+0.002)` 反推。

### 3. 关键函数 / 选择器索引（按字符串检索，行号会漂）

CSS：`--preview-width`、`#previewSplitter`、`body.preview-expanded`、`.hab-viewport-tools`、`.hab-canvas-size`、`--hab-stage-height`

HTML：`#btnPreviewExpand`、`#previewSplitter`、`#habCanvasHeight`、`#habZoomOut/#habZoomLabel/#habZoomIn/#habFitView/#habPanToggle`、`#habAdjSpeed`

主脚本：`toggleSplitPreview()`、`togglePreviewExpand()`

蚕室 IIFE：`safeUnit()`、`habViewport`、`syncMeasured()`、`makeRandomDemo()`、`view()`、`screenToHab()`、`zoomAt()`、`resetHabView()`、`updateHabZoomLabel()`、`step()`、`syncRoutePanel()`、`bindRoutePanel()`、`habStart` 监听、`world` 的 `wheel` / `pointerdown` / `pointermove` / `pointerup`、`bindPreviewResizer()`、`habSave` / `exportHabitat()` / `importHabitat()`

## 二、本轮验收结果（可复现）

方法：拆分三个脚本块 → `html.unescape` → 逐个 `node --check`（均 OK）；再用无头 Chrome 跑一个带探针的 QA 副本（隐藏 `.screen1`、真实 `step()` 驱动、逐帧截图）。

| 项 | 结果 |
| --- | --- |
| 实测蚕同步 | `sync=2`，两只都进蚕室 |
| 开始即运动 | `mode=run`、`follow=true`、`u` 持续推进、`x/y` 变化 |
| 逐只速度 | A 设 2.00× 绕满一圈后 `u≈0.158`；B 保持 1× 的 `u≈0.579`（同时长下位移差 2 倍） |
| 丝与蚕体 | `silk=130+`、`body=true`、`safeUnit` 修复后画布白色像素 40,465（蚕体已绘制） |
| 滚轮缩放 | 标签 100% → 127%，`适应场地` 回 100% |
| 平移 | `#habPanToggle` 得 `active on`、`#habWorld` 得 `pan-mode` |
| 分隔线 | `--preview-width` 由 `clamp(380px,48%,980px)` 变为具体像素值 |
| 场地高度 | 标签 `780px`、滑杆值 `780`（step 40 会吸附成 800，已改 20） |
| 三副本 | SHA256 全部 `571CA085…`，265,678 B |

## 三、已知限制 / 未做

1. 预览 iframe 内部在 48% 宽度下仍按自身最小列宽排版，右侧参数栏会被压窄（预览自身响应式，属另一份 srcdoc，本轮未动其协议）。
2. 蚕体在 1× 缩放下偏“长条”，`bodyLen=78` 是画布像素常量，未按 zoom 归一。
3. 场地高度变化只重绘 `bg/depth`，`world` 每帧重绘；若后续加入静态缓存需同步失效。
4. 一格多蚕 / 蚕簇隔间、LED 尺寸导出仍属织网引擎（`prototype/weave-lab.html`）那条线，未并入本页。
5. 无限画布目前作用于 `world` 一层；`bg/leaves/mist/depth` 是屏幕固定装饰层，跟随缩放会需要重做氛围层。

## 四、给 GPT / Cursor 的下一步约束

- 只做增量补丁，禁止重写整页。
- 不得改 `silkworm-preview` 消息协议、`silkworm-habitat/v1` 原字段语义、`routeWorld` 头→尾 / `silk` 尾→头。
- 不得恢复默认随机演示蚕；随机蚕只能按需添加。
- 不得动 `.screen1 { height: 100vh }` 与描图器视频分段逻辑。
- 不得引入 `type="module"` 或外部依赖，保持三个脚本块职责。
- 改完必须：三副本 SHA256 一致 + 输出函数清单与验收报告。

建议后续优先级：

1. 蚕体尺寸随 zoom 归一（视觉一致性）。
2. `world` 静态层（网格 / 场地轮廓）缓存，减少每帧 path 重建。
3. 场景 JSON 版本号升级到 `v2`，显式声明 `speedScale`（向后兼容读 v1）。
4. 接入织网引擎的“隔间（蚕簇）+ 单蚕模式复制”，复用 `routeWorld` 与 `speedScale`。
